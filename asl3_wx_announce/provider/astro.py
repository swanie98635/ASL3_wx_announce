from datetime import datetime
from astral import LocationInfo as AstralLoc
from astral.sun import sun
from astral.moon import phase
from ..models import LocationInfo

class AstroProvider:
    def get_astro_info(self, loc: LocationInfo) -> str:
        try:
            # Astral uses its own LocationInfo
            City = AstralLoc(loc.city, loc.region, loc.timezone, loc.latitude, loc.longitude)
            s = sun(City.observer, date=datetime.now(), tzinfo=City.timezone)
            
            sunrise = s['sunrise'].strftime("%I %M %p")
            sunset = s['sunset'].strftime("%I %M %p")
            
            # Moon phase: 0..27
            ph = phase(datetime.now())
            moon_desc = self._describe_phase(ph)
            
            return f"Sunrise is at {sunrise}. Sunset is at {sunset}. The moon is {moon_desc}."
        except Exception as e:
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
