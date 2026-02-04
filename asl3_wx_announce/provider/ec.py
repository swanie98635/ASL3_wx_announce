from datetime import datetime
from typing import List
from env_canada import ECWeather
from ..models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert, AlertSeverity
from .base import WeatherProvider

class ECProvider(WeatherProvider):
    def __init__(self, **kwargs):
        self.points_cache = {}
        self.extra_zones = kwargs.get('alerts', {}).get('extra_zones', [])
        
        # Map config language code (fr/en) to ECWeather expected parameter (french/english)
        self.language = 'french' if kwargs.get('language') == 'fr' else 'english'

    def _get_ec_data(self, lat, lon):
        # ECWeather auto-selects station based on lat/lon
        ec = ECWeather(coordinates=(lat, lon), language=self.language)
        ec.update()
        return ec

    def get_location_info(self, lat: float, lon: float) -> LocationInfo:
        ec = self._get_ec_data(lat, lon)
        # ECData metadata is nested
        meta = ec.metadata
        return LocationInfo(
            latitude=lat,
            longitude=lon,
            city=meta.get('location', 'Unknown'),
            region=meta.get('province', 'Canada'),
            country_code="CA",
            timezone="Unknown" # EC lib doesn't trivialy expose TZ
        )

    def get_conditions(self, lat: float, lon: float) -> CurrentConditions:
        ec = self._get_ec_data(lat, lon)
        cond = ec.conditions
        
        return CurrentConditions(
            temperature=float(cond.get('temperature', {}).get('value', 0)),
            humidity=int(cond.get('humidity', {}).get('value') or 0),
            wind_speed=float(cond.get('wind_speed', {}).get('value') or 0),
            wind_direction=cond.get('wind_direction', {}).get('value'),
            description=cond.get('condition', 'Unknown')
        )

    def get_forecast(self, lat: float, lon: float) -> List[WeatherForecast]:
        ec = self._get_ec_data(lat, lon)
        daily = ec.daily_forecasts
        
        forecasts = []
        for d in daily:
            forecasts.append(WeatherForecast(
                period_name=d.get('period'),
                high_temp=float(d.get('temperature')) if d.get('temperature') else None,
                low_temp=None, # EC daily structure is period-based (e.g. "Monday", "Monday Night")
                summary=d.get('text_summary', ''),
                precip_probability=int(d.get('precip_probability') or 0)
            ))
        return forecasts

    def get_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        ec_objects = [self._get_ec_data(lat, lon)]
        
        # Add extra zones (Station IDs e.g., 'ON/s0000430')
        for zone_id in self.extra_zones:
            if "/" in zone_id: # Basic check if it looks like EC station ID
                 try:
                     ec_objects.append(ECWeather(station_id=zone_id, language=self.language))
                 except Exception:
                     pass

        results = []
        now = datetime.now()
        seen_titles = set()

        for ec in ec_objects:
            try:
                if not getattr(ec, 'conditions', None): # Ensure updated
                     ec.update()
                
                for a in ec.alerts:
                    title = a.get('title', '')
                    if title in seen_titles: continue
                    seen_titles.add(title)

                    # Mapping severity roughly
                    severity = AlertSeverity.UNKNOWN
                    if "warning" in title.lower(): severity = AlertSeverity.WARNING
                    elif "watch" in title.lower(): severity = AlertSeverity.WATCH
                    elif "advisory" in title.lower(): severity = AlertSeverity.ADVISORY
                    elif "statement" in title.lower(): severity = AlertSeverity.ADVISORY
                    
                    # Using current time as dummy effective/expires if missing
                    eff = a.get('date') 
                    
                    results.append(WeatherAlert(
                        id=title, 
                        severity=severity,
                        title=title,
                        description=a.get('detail', ''),
                        area_description=ec.metadata.get('location', 'Local Area'),
                        effective=now,  
                        expires=now     
                    ))
            except Exception:
                continue
            
        return results

