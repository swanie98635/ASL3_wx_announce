from datetime import datetime
from astral import LocationInfo as AstralLoc
from astral.sun import sun
from astral.moon import phase
from ..models import LocationInfo

class AstroProvider:
    def get_astro_info(self, loc: LocationInfo) -> str:
        parts = []
        try:
            # Astral uses its own LocationInfo
            City = AstralLoc(loc.city, loc.region, loc.timezone, loc.latitude, loc.longitude)
            s = sun(City.observer, date=datetime.now(), tzinfo=City.timezone)
            
            sunrise = s['sunrise'].strftime("%I %M %p")
            sunset = s['sunset'].strftime("%I %M %p")
            parts.append(f"Sunrise is at {sunrise}. Sunset is at {sunset}.")
            
            # Moon phase: 0..27
            ph = phase(datetime.now())
            moon_desc = self._describe_phase(ph)
            parts.append(f"The moon is {moon_desc}.")
            
            # Solar Flux
            sfi_msg = self.get_solar_flux()
            if sfi_msg:
                parts.append(sfi_msg)
                
            return " ".join(parts)
            
        except Exception as e:
            # logger.error(f"Astro error: {e}")
            return ""

    def get_solar_flux(self) -> str:
        """
        Fetches the latest Solar Flux Index (SFI) from NOAA SWPC.
        "SFI taken (date time) from the Penticton Radio Observatory in Penticton, British Columbia, 
        as reported by the National Weather Service Space Weather Prediction Center."
        """
        import requests
        from dateutil.parser import parse as parse_date
        import pytz
        
        url = "https://services.swpc.noaa.gov/products/summary/10cm-flux.json"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # Expected format: {"Flux": "165", "Time": "2025-01-29 18:00"} OR similar
            
            flux = data.get('Flux')
            timestamp_str = data.get('TimeStamp') # Verify key case
            
            if not flux or not timestamp_str:
                 return ""
                 
            # Parse time
            # Timestamp is usually UTC.
            dt = parse_date(timestamp_str)
            # Format: Month Day, Hour Minute UTC? 
            # Or just "Date Time" as user asked? User said "SFI taken (date time)..."
            # Let's format nicely: "January 29 at 10 00 UTC"
            
            # Ensure it is treated as UTC if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            
            dt_fmt = dt.strftime("%B %d at %H %M UTC")
            
            return (
                f"Solar Flux Index is {flux}. "
                f"S F I taken {dt_fmt} from the Penticton Radio Observatory in Penticton, British Columbia, "
                f"as reported by the National Weather Service Space Weather Prediction Center."
            )
            
        except Exception as e:
            # Fail silently for SFI
            return ""

    def _describe_phase(self, day: float) -> str:
        if day < 1: return "New"
        if day < 7: return "Waxing Crescent"
        if day < 8: return "First Quarter"
        if day < 14: return "Waxing Gibbous"
        if day < 15: return "Full"
        if day < 21: return "Waning Gibbous"
        if day < 22: return "Last Quarter"
        return "Waning Crescent"
