import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List
from dateutil.parser import parse as parse_date
from ..models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert, AlertSeverity
from .base import WeatherProvider

logger = logging.getLogger(__name__)

class AlertReadyProvider(WeatherProvider):
    # Public NAAD Feed URL (Root)
    # Browsable at: http://cap.naad-adna.pelmorex.com/
    # We use the aggregate RSS feed for all of Canada.
    DEFAULT_FEED_URL = "http://cap.naad-adna.pelmorex.com/rss/all.rss"

    def __init__(self, **kwargs):
        self.points_cache = {}
        # Hardcoded URL as requested, user just enables the feature.
        self.feed_url = self.DEFAULT_FEED_URL
        self.extra_zones = kwargs.get('alerts', {}).get('extra_zones', [])
        # reuse ca_events or have separate list? Using ca_events is consistent.
        self.allowed_events = kwargs.get('alerts', {}).get('ca_events', [])

    def get_location_info(self, lat: float, lon: float) -> LocationInfo:
        # Not used for location resolution, just alerts
        return LocationInfo(latitude=lat, longitude=lon, city="Unknown", region="Canada", country_code="CA", timezone="UTC")

    def get_conditions(self, lat: float, lon: float) -> CurrentConditions:
        # Not supported
        return CurrentConditions(temperature=0, description="N/A")

    def get_forecast(self, lat: float, lon: float) -> List[WeatherForecast]:
        return []

    def is_point_in_polygon(self, x, y, poly):
        """
        Ray Casting Algorithm.
        x: lon, y: lat
        poly: list of (lon, lat) tuples
        """
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def parse_cap_polygon(self, poly_str: str) -> List[tuple]:
        # "lat,lon lat,lon ..."
        points = []
        try:
            for pair in poly_str.strip().split(' '):
                if ',' in pair:
                    lat_str, lon_str = pair.split(',')
                    points.append((float(lon_str), float(lat_str)))
        except ValueError:
            pass
        return points

    def get_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        alerts = []
        try:
            # parsing the RSS/Atom feed of *current* CAP messages
            # Note: The NAAD feed is huge. We should optimize?
            # User wants "non-weather". Typically much fewer than weather.
            # But the feed includes EVERYTHING (Environment Canada too?).
            # Yes, "all.rss".
            # We must be careful not to duplicate what EC provider provides.
            # Usually EC provider handles "Weather" types.
            # We should filter for types NOT in a blacklist or ONLY in a whitelist.
            # For now, let's fetch and see.
            
            resp = requests.get(self.feed_url, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"AlertReady Feed fetch failed: {resp.status_code}")
                return []
            
            # Simple XML parsing of RSS
            root = ET.fromstring(resp.content)
            # RSS 2.0: channel/item
            for item in root.findall('./channel/item'):
                title = item.find('title').text if item.find('title') is not None else "Unknown Alert"
                link = item.find('link').text if item.find('link') is not None else None
                
                # Check duplication? (Maybe check Title for 'Environment Canada')
                # If title contains "Environment Canada", skip?
                # User config says "enable_alert_ready" for "Civil/Non-Weather".
                # Let's filter OUT known weather sources if possible, or just rely on self.allowed_events?
                # But self.allowed_events currently holds Weather strings too (for EC provider).
                # The user config seems to share "ca_events".
                # If we use shared config, we double-report.
                # Heuristic: If Title starts with "Environment Canada", skip it (let EC provider handle it).
                if "Environment Canada" in title:
                    continue
                    
                if not link:
                    continue
                    
                # Fetch CAP XML
                try:
                    cap_resp = requests.get(link, timeout=5)
                    if cap_resp.status_code != 200:
                        continue
                        
                    cap_root = ET.fromstring(cap_resp.content)
                    # Namespace handling might be needed. CAP usually uses xmlns "urn:oasis:names:tc:emergency:cap:1.2"
                    # We can strip namespaces or use wildcards.
                    # ElementTree with namespaces is annoying.
                    # Hack: Remove xmlns from string before parsing? Or just use local-name().
                    # Let's try ignoring namespace by using `findall` with `{namespace}tag` if needed, 
                    # but simple `find` might fail.
                    # Let's rely on string searching or simple iterative search if needed.
                    
                    # Finding <info> block
                    # Assume namespace present.
                    ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
                    # Try finding info without NS first (if no xmlns defined), then with.
                    infos = cap_root.findall('cap:info', ns)
                    if not infos:
                        infos = cap_root.findall('info') # Try no namespace
                        
                    for info in infos:
                        # Event Type
                        event = info.find('cap:event', ns).text if info.find('cap:event', ns) is not None else info.find('event').text
                        
                        # Severity
                        severity_str = info.find('cap:severity', ns).text if info.find('cap:severity', ns) is not None else info.find('severity').text
                        
                        # Area/Polygon
                        areas = info.findall('cap:area', ns)
                        if not areas:
                            areas = info.findall('area')
                            
                        is_relevant = False
                        for area in areas:
                            polys = area.findall('cap:polygon', ns)
                            if not polys: polys = area.findall('polygon')
                            
                            for poly_elem in polys:
                                poly_points = self.parse_cap_polygon(poly_elem.text)
                                if poly_points and self.is_point_in_polygon(lon, lat, poly_points):
                                    is_relevant = True
                                    break
                            if is_relevant: break
                            
                        if is_relevant:
                            # Parse dates
                            effective = None
                            expires = None
                            issued = None
                            # ... (Date parsing logic similar to other providers)
                            
                            # Map severity
                            sev_enum = AlertSeverity.UNKNOWN
                            if severity_str == 'Extreme': sev_enum = AlertSeverity.CRITICAL
                            elif severity_str == 'Severe': sev_enum = AlertSeverity.WARNING
                            elif severity_str == 'Moderate': sev_enum = AlertSeverity.WATCH
                            elif severity_str == 'Minor': sev_enum = AlertSeverity.ADVISORY
                            
                            # Create Alert
                            # Deduplicate ID? Link is unique usually.
                            alert = WeatherAlert(
                                id=link, # Use URL as ID
                                title=event,
                                description=info.find('cap:description', ns).text if info.find('cap:description', ns) is not None else "No description",
                                severity=sev_enum,
                                issued=datetime.now(), # Placeholder if parsing fails
                                effective=datetime.now(),
                                expires=datetime.now()
                            )
                            alerts.append(alert)

                except Exception as e:
                    logger.warning(f"Failed to process CAP {link}: {e}")
                    continue

        except Exception as e:
            logger.error(f"AlertReady Error: {e}")
            
        return alerts
