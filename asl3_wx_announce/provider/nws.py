import requests
from datetime import datetime
from typing import List
from dateutil.parser import parse as parse_date
from ..models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert, AlertSeverity
from .base import WeatherProvider

class NWSProvider(WeatherProvider):
    USER_AGENT = "(asl3-wx-announce, contact@example.com)"
    
    def __init__(self, **kwargs):
        self.points_cache = {}
        self.extra_zones = kwargs.get('alerts', {}).get('extra_zones', [])
    
    def _headers(self):
        return {"User-Agent": self.USER_AGENT, "Accept": "application/geo+json"}

    def _get_point_metadata(self, lat, lon):
        key = f"{lat},{lon}"
        if key in self.points_cache:
            return self.points_cache[key]
        
        url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        self.points_cache[key] = data['properties']
        return data['properties']

    def get_location_info(self, lat: float, lon: float) -> LocationInfo:
        meta = self._get_point_metadata(lat, lon)
        props = meta.get('relativeLocation', {}).get('properties', {})
        return LocationInfo(
            latitude=lat,
            longitude=lon,
            city=props.get('city', 'Unknown'),
            region=props.get('state', 'US'),
            country_code="US",
            timezone=meta.get('timeZone', 'UTC')
        )

    def get_conditions(self, lat: float, lon: float) -> CurrentConditions:
        # NWS "current conditions" often requires finding a nearby station first
        # For simplicity, we can sometimes pull from the gridpoint "now", but standard practice 
        # is to hit the stations endpoint.
        meta = self._get_point_metadata(lat, lon)
        stations_url = meta['observationStations']
        
        # Get first station
        s_resp = requests.get(stations_url, headers=self._headers())
        s_data = s_resp.json()
        station_id = s_data['features'][0]['properties']['stationIdentifier']
        
        # Get obs
        obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
        o_resp = requests.get(obs_url, headers=self._headers())
        props = o_resp.json()['properties']
        
        temp_c = props.get('temperature', {}).get('value')
        return CurrentConditions(
            temperature=temp_c if temp_c is not None else 0.0,
            humidity=props.get('relativeHumidity', {}).get('value'),
            wind_speed=props.get('windSpeed', {}).get('value'),
            wind_direction=str(props.get('windDirection', {}).get('value')),
            description=props.get('textDescription', 'Unknown')
        )

    def get_forecast(self, lat: float, lon: float) -> List[WeatherForecast]:
        meta = self._get_point_metadata(lat, lon)
        forecast_url = meta['forecast']
        
        resp = requests.get(forecast_url, headers=self._headers())
        periods = resp.json()['properties']['periods']
        
        forecasts = []
        for p in periods[:4]: # Just next few periods
            # NWS gives temp in F sometimes, but API usually defaults to F. 
            # We strictly want models in C, so check unit.
            temp = p.get('temperature')
            unit = p.get('temperatureUnit')
            if unit == 'F':
                temp = (temp - 32) * 5.0/9.0
            
            summary = p['detailedForecast']
            forecasts.append(WeatherForecast(
                period_name=p['name'],
                high_temp=temp if p['isDaytime'] else None,
                low_temp=temp if not p['isDaytime'] else None,
                summary=summary,
                precip_probability=p.get('probabilityOfPrecipitation', {}).get('value')
            ))
        return forecasts

    def get_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        meta = self._get_point_metadata(lat, lon)
        
        # Extract zone IDs (e.g., https://api.weather.gov/zones/forecast/MDZ013)
        # We want the basename
        def get_id(url):
            return url.split('/')[-1] if url else None

        zones = set(self.extra_zones)
        zones.add(get_id(meta.get('county')))
        zones.add(get_id(meta.get('fireWeatherZone')))
        zones.add(get_id(meta.get('forecastZone')))
        zones.discard(None) # Remove None if any failed
        
        if not zones:
            # Fallback to point if no zones found (unlikely)
            url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
        else:
            # Join zones: active?zone=MDZ013,MDC031
            zone_str = ",".join(zones)
            url = f"https://api.weather.gov/alerts/active?zone={zone_str}"

        resp = requests.get(url, headers=self._headers())
        features = resp.json().get('features', [])
        
        alerts = []
        for f in features:
            props = f['properties']
            
            # Map severity
            sev_str = props.get('severity', 'Unknown')
            severity = AlertSeverity.UNKNOWN
            if sev_str == 'Severe': severity = AlertSeverity.WARNING 
            
            event_type = props.get('event', '').upper()
            if "WARNING" in event_type: severity = AlertSeverity.WARNING
            elif "WATCH" in event_type: severity = AlertSeverity.WATCH
            elif "ADVISORY" in event_type: severity = AlertSeverity.ADVISORY
            elif "STATEMENT" in event_type: severity = AlertSeverity.ADVISORY
            
            alerts.append(WeatherAlert(
                id=props['id'],
                severity=severity,
                title=props['event'],
                description=props['description'] or "",
                instruction=props.get('instruction'),
                area_description=props.get('areaDesc', ''),
                effective=parse_date(props['effective']),
                expires=parse_date(props['expires'])
            ))
            
        return alerts
