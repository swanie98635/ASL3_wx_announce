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
            'alert_item': "A {title} is in effect from {effective} until {expires}. ",
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
            'alert_item': "Un {title} est en vigueur du {effective} au {expires}. ",
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

    def _fmt_alert_dt(self, dt: datetime, tz) -> str:
        """Format a datetime as 'Monday, March 10 at 3 45 PM' in local time."""
        try:
            local_dt = dt.astimezone(tz)
        except Exception:
            local_dt = dt

        days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        months_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        months_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

        day_idx = local_dt.weekday()
        month_idx = local_dt.month - 1
        day_num = local_dt.day

        if self.lang == 'fr':
            # French: lundi 10 mars à 15 heures 45
            day_name = days_fr[day_idx]
            month_name = months_fr[month_idx]
            time_str = local_dt.strftime("%H heures %M")
            return f"{day_name} {day_num} {month_name} à {time_str}"
        else:
            # English: Monday, March 10 at 3 45 PM
            day_name = days_en[day_idx]
            month_name = months_en[month_idx]
            time_str = local_dt.strftime("%I %M %p").lstrip("0").strip()
            return f"{day_name}, {month_name} {day_num} at {time_str}"

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

    def announce_alerts(self, alerts: List[WeatherAlert], timezone: str = None) -> str:
        if not alerts:
            return self._t('no_alerts')

        try:
            tz = pytz.timezone(timezone) if timezone else pytz.utc
        except Exception:
            tz = pytz.utc

        text = self._t('alerts_intro', count=len(alerts))
        for a in alerts:
            start = a.onset if a.onset else a.effective
            end = a.ends if a.ends else a.expires
            
            start_str = self._fmt_alert_dt(start, tz)
            end_str = self._fmt_alert_dt(end, tz)
            text += self._t('alert_item', title=a.title, effective=start_str, expires=end_str)

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
            parts.append(self._t('alert_advise') + self.announce_alerts(alerts, timezone=loc.timezone))
             
        parts.append(self.announce_conditions(loc, current))
        parts.append(self.announce_forecast(forecast))
        
        if sun_info:
            parts.append(sun_info)
            
        return " ".join(parts)
