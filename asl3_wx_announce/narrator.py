from datetime import datetime
import pytz
from typing import List, Dict
from .models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert

class Narrator:
    STRINGS = {
        'en': {
            'wind_fmt': ", with winds from the {dir} at {kph} kilometers per hour, or {mph} miles per hour",
            'current_intro': "Current conditions for {city}, {region}.",
            'temp_fmt': "The temperature is {temp_c} degrees celsius, {temp_f} degrees fahrenheit.",
            'conditions_fmt': "Conditions are {desc}{wind}.",
            'forecast_intro': "Here is the forecast. ",
            'high_fmt': " with a high of {c} celsius, {f} fahrenheit",
            'low_fmt': " with a low of {c} celsius, {f} fahrenheit",
            'period_fmt': "{period}: {summary}{temp}. ",
            'no_alerts': "There are no active weather alerts.",
            'alerts_intro': "There are {count} active weather alerts. ",
            'alert_item': "A {title} is in effect until {expires}. ",
            'greeting': "Good day. The time is {time}.",
            'intro_city': "This is the automated weather report for {city}.",
            'alert_advise': "Please be advised: ",
            'time_fmt': "%I %M %p"
        },
        'fr': {
            'wind_fmt': ", avec des vents du {dir} à {kph} kilomètres à l'heure",
            'current_intro': "Conditions actuelles pour {city}, {region}.",
            'temp_fmt': "La température est de {temp_c} degrés Celsius, {temp_f} degrés Fahrenheit.",
            'conditions_fmt': "Les conditions sont {desc}{wind}.",
            'forecast_intro': "Voici les prévisions. ",
            'high_fmt': " avec un maximum de {c} Celsius, {f} Fahrenheit",
            'low_fmt': " avec un minimum de {c} Celsius, {f} Fahrenheit",
            'period_fmt': "{period}: {summary}{temp}. ",
            'no_alerts': "Il n'y a aucune alerte météo en vigueur.",
            'alerts_intro': "Il y a {count} alertes météo en vigueur. ",
            'alert_item': "Un {title} est en vigueur jusqu'à {expires}. ",
            'greeting': "Bonjour. Il est {time}.",
            'intro_city': "Ceci est le bulletin météo automatisé pour {city}.",
            'alert_advise': "Veuillez noter : ",
            'time_fmt': "%H heures %M"
        }
    }

    def __init__(self, config: Dict):
        self.lang = config.get('language', 'en')
        self.s = self.STRINGS.get(self.lang, self.STRINGS['en'])

    def _c_to_f(self, temp_c: float) -> int:
        return int((temp_c * 9/5) + 32)
    
    def _t(self, key, **kwargs):
        tpl = self.s.get(key, "")
        return tpl.format(**kwargs)

    def announce_conditions(self, loc: LocationInfo, current: CurrentConditions) -> str:
        wind = ""
        if current.wind_speed and current.wind_speed > 5:
            mph = int(current.wind_speed * 0.621371)
            wind = self._t('wind_fmt', dir=current.wind_direction, kph=int(current.wind_speed), mph=mph)
        
        intro = self._t('current_intro', city=loc.city, region=loc.region)
        temp_str = self._t('temp_fmt', temp_c=int(current.temperature), temp_f=self._c_to_f(current.temperature))
        cond_str = self._t('conditions_fmt', desc=current.description, wind=wind)
        
        return f"{intro} {temp_str} {cond_str}"

    def announce_forecast(self, forecasts: List[WeatherForecast]) -> str:
        if not forecasts:
            return ""
        
        text = self._t('forecast_intro')
        for f in forecasts[:3]:
            temp = ""
            if f.high_temp is not None:
                temp = self._t('high_fmt', c=int(f.high_temp), f=self._c_to_f(f.high_temp))
            elif f.low_temp is not None:
                temp = self._t('low_fmt', c=int(f.low_temp), f=self._c_to_f(f.low_temp))
            
            text += self._t('period_fmt', period=f.period_name, summary=f.summary, temp=temp)
            
        return text

    def announce_alerts(self, alerts: List[WeatherAlert]) -> str:
        if not alerts:
            return self._t('no_alerts')
        
        text = self._t('alerts_intro', count=len(alerts))
        for a in alerts:
            # Need locale specific time format?
            # Alerts usually have specific expiration.
            expires_str = a.expires.strftime(self.s.get('time_fmt', "%I %M %p"))
            text += self._t('alert_item', title=a.title, expires=expires_str)
            
        return text

    def build_full_report(self, loc: LocationInfo, current: CurrentConditions, forecast: List[WeatherForecast], alerts: List[WeatherAlert], sun_info: str = "") -> str:
        parts = []
        
        try:
            tz = pytz.timezone(loc.timezone)
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()

        time_fmt = self.s.get('time_fmt', "%I %M %p")
        now_str = now.strftime(time_fmt)
        if self.lang == 'en' and now_str.startswith("0"):
            now_str = now_str[1:]
            
        parts.append(self._t('greeting', time=now_str))
        parts.append(self._t('intro_city', city=loc.city))
        
        if alerts:
             parts.append(self._t('alert_advise') + self.announce_alerts(alerts))
             
        parts.append(self.announce_conditions(loc, current))
        parts.append(self.announce_forecast(forecast))
        
        if sun_info:
            parts.append(sun_info)
            
        return " ".join(parts)
