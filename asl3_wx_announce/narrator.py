from datetime import datetime
from typing import List
from .models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert

class Narrator:
    def __init__(self):
        pass

    def announce_conditions(self, loc: LocationInfo, current: CurrentConditions) -> str:
        wind = ""
        if current.wind_speed and current.wind_speed > 5:
            wind = f", with winds from the {current.wind_direction} at {int(current.wind_speed)} kilometers per hour"
        
        return (
            f"Current conditions for {loc.city}, {loc.region}. "
            f"The temperature is {int(current.temperature)} degrees celsius. "
            f"Conditions are {current.description}{wind}."
        )

    def announce_forecast(self, forecasts: List[WeatherForecast]) -> str:
        if not forecasts:
            return ""
        
        text = "Here is the forecast. "
        for f in forecasts[:3]: # Read first 3 periods
            temp = ""
            if f.high_temp is not None:
                temp = f" with a high of {int(f.high_temp)}"
            elif f.low_temp is not None:
                temp = f" with a low of {int(f.low_temp)}"
            
            text += f"{f.period_name}: {f.summary}{temp}. "
            
        return text

    def announce_alerts(self, alerts: List[WeatherAlert]) -> str:
        if not alerts:
            return "There are no active weather alerts."
        
        text = f"There are {len(alerts)} active weather alerts. "
        for a in alerts:
            # "A Severe Thunderstorm Warning is in effect until 5 PM."
            expires_str = a.expires.strftime("%I %M %p")
            text += f"A {a.title} is in effect until {expires_str}. "
            
        return text

    def build_full_report(self, loc: LocationInfo, current: CurrentConditions, forecast: List[WeatherForecast], alerts: List[WeatherAlert], sun_info: str = "") -> str:
        parts = []
        
        # Time string: "10 30 PM"
        now_str = datetime.now().strftime("%I %M %p")
        # Remove leading zero from hour if desired, but TTS usually handles "09" fine. 
        # For cleaner TTS: 
        if now_str.startswith("0"): 
            now_str = now_str[1:]
            
        parts.append(f"Good day. The time is {now_str}.")
        parts.append(f"This is the automated weather report for {loc.city}.")
        
        if alerts:
             parts.append("Please be advised: " + self.announce_alerts(alerts))
             
        parts.append(self.announce_conditions(loc, current))
        parts.append(self.announce_forecast(forecast))
        
        if sun_info:
            parts.append(sun_info)
            
        return " ".join(parts)
