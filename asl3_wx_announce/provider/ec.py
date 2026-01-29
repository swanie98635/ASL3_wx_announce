from datetime import datetime
from typing import List
from env_canada.ec_weather import ECWeather
from ..models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert, AlertSeverity
from .base import WeatherProvider

class ECProvider(WeatherProvider):
    def __init__(self, **kwargs):
        self.points_cache = {}
        self.extra_zones = kwargs.get('alerts', {}).get('extra_zones', [])
        self.allowed_events = kwargs.get('alerts', {}).get('ca_events', [])

    def _get_ec_data(self, lat, lon):
        # ECWeather auto-selects station based on lat/lon
        import asyncio
        ec = ECWeather(coordinates=(lat, lon))
        asyncio.run(ec.update())
        return ec

    def get_location_info(self, lat: float, lon: float) -> LocationInfo:
        ec = self._get_ec_data(lat, lon)
        # ECData metadata is nested
        meta = ec.metadata
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"DEBUG: ec.metadata type: {type(meta)}")
        logger.info(f"DEBUG: ec.metadata content: {meta}")

        # Safe access
        if not isinstance(meta, dict):
            meta = {}

        city = meta.get('location')
        region = meta.get('province')
        
        # Fallback to reverse_geocoder if EC fails to name the location
        if not city or city == 'Unknown':
            try:
                import reverse_geocoder as rg
                results = rg.search((lat, lon))
                if results:
                    city = results[0].get('name')
                    if not region:
                         region = results[0].get('admin1')
            except Exception as e:
                logger.warning(f"Reverse geocode failed: {e}")
        
        return LocationInfo(
            latitude=lat,
            longitude=lon,
            city=city or 'Unknown',
            region=region or 'Canada',
            country_code="CA",
            timezone="Unknown" # EC lib doesn't trivialy expose TZ
        )

    def get_conditions(self, lat: float, lon: float) -> CurrentConditions:
        ec = self._get_ec_data(lat, lon)
        cond = ec.conditions
        
        return CurrentConditions(
            temperature=float(cond.get('temperature', {}).get('value') or 0),
            humidity=int(cond.get('humidity', {}).get('value') or 0),
            wind_speed=float(cond.get('wind_speed', {}).get('value') or 0),
            wind_direction=cond.get('wind_direction', {}).get('value'),
            description=cond.get('condition', {}).get('value') or 'Unknown'
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
                short_summary=d.get('text_summary', ''),
                precip_probability=int(d.get('precip_probability') or 0)
            ))
        return forecasts

    def get_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        ec_objects = [self._get_ec_data(lat, lon)]
        
        # Add extra zones (Station IDs e.g., 'ON/s0000430')
        for zone_id in self.extra_zones:
            if "/" in zone_id: # Basic check if it looks like EC station ID
                 try:
                     ec_objects.append(ECWeather(station_id=zone_id))
                 except Exception:
                     pass

        results = []
        now = datetime.now()
        seen_titles = set()

        for ec in ec_objects:
            try:
                if not getattr(ec, 'conditions', None): # Ensure updated
                     import asyncio
                     asyncio.run(ec.update())
                
                for a in ec.alerts:
                    title = a.get('title', '')
                    if title in seen_titles: continue
                    seen_titles.add(title)
                    
                    # Filter by allowed list if present
                    if self.allowed_events:
                        if not any(ae.lower() in title.lower() for ae in self.allowed_events):
                            continue

                    # Mapping severity roughly
                    severity = AlertSeverity.UNKNOWN
                    if "warning" in title.lower(): severity = AlertSeverity.WARNING
                    elif "watch" in title.lower(): severity = AlertSeverity.WATCH
                    elif "advisory" in title.lower(): severity = AlertSeverity.ADVISORY
                    elif "statement" in title.lower(): severity = AlertSeverity.ADVISORY
                    
                    # Using current time as dummy effective/expires if missing
                    eff_str = a.get('date') 
                    eff_dt = now
                    if eff_str:
                        # EC format often: "2023-10-27T15:00:00-04:00" or similar? 
                        # actually env_canada lib might return a string.
                        # We'll try to parse it if dateutil is available, or use now.
                        try:
                            from dateutil.parser import parse as parse_date
                            eff_dt = parse_date(eff_str)
                        except:
                            pass

                    results.append(WeatherAlert(
                        id=title, 
                        severity=severity,
                        title=title,
                        description=a.get('detail', ''),
                        area_description=ec.metadata.get('location', 'Local Area'),
                        effective=eff_dt,  
                        expires=now, # EC doesn't explicitly give expires in this view
                        issued=eff_dt
                    ))
            except Exception:
                continue
            
        return results

