from datetime import datetime
from typing import List
import subprocess
import re
from .models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert

class Narrator:
    STRINGS = {
        'en': {
            'current_conditions_intro': "Current conditions for {city}, {region}.",
            'temperature': "The temperature is {val} {unit}.",
            'conditions': "Conditions are {desc}{wind}.",
            'wind_with_dir': ", with winds from the {dir} at {val} {unit}",
            'wind_no_dir': ", with winds at {val} {unit}",
            'forecast_intro': "Here is the forecast.",
            'forecast_item': "{period}: {cond}.{temp}",
            'no_alerts': "There are no active weather alerts.",
            'active_alerts_count': "There are {count} active weather alerts. ",
            'alert_issued': "A {title} was issued at {time}. ",
            'alert_effect': "A {title} is in effect. ",
            'alert_effective_from': "It is effective from {time}. ",
            'alert_expires': "It expires at {time}. ",
            'clear': "{callsign} Clear.",
            'time_msg': "The time is {time} {tz}. Time provided by the {agency}.",
            'automated_report': "This is the automated weather report for {city}, {region}. Break. [PAUSE]",
            'please_advise': "Please be advised: {alerts} Break. [PAUSE]",
            'system_status': "System status: Monitoring for {sev} level events and higher. Tone alerts active for {tone_sev} events and higher. Monitoring interval is {interval} minutes. Break. [PAUSE]",
            'code_source': "A S L 3 underscore w x underscore announce is available on github and developed by N 7 X O B as non-commercial code provided for the benefit of the amateur radio community.",
            'data_source_us': "Data provided by the National Weather Service and the National Institute of Standards and Technology.",
            'data_source_ca': "Data provided by Environment Canada, National Research Council Canada, and the National Alert Aggregation and Dissemination System.",
            'intro_cq': "CQ CQ CQ. This is {callsign} with the updated weather report.",
            'intro_good_day': "Good day.",
            'concludes': "This concludes the weather report for {city}. {callsign} Clear.",
            'degrees': "degrees",
            'degrees_celsius': "degrees celsius",
            'mph': "miles per hour",
            'kph': "kilometers per hour",
            'high': " High",
            'low': " Low",
            # Test & Monitor Strings - (Simplified for brevity, can add more)
            'test_preamble': "{callsign} Testing. The following is an alerting test of an automated alerting notification and message. Do not take any action as a result of the following message. Repeating - take no action - this is only a test. The test tones will follow in 10 seconds.",
            'test_message': "This is a test message. This is a sample emergency test message. This is only a test. No action is required.",
            'test_postamble': "{callsign} reminds you this was a test. Do not take action. Repeat - take no action. If this was an actual emergency, the preceding tone would be followed by specific information from official authorities on an imminent emergency that requires your immediate attention and possibly action to prevent loss of life, injury or property damage. This test is concluded.",
            'monitor_online': "{callsign} Automatic Monitoring Online. Data provided by {source}. {nodes}Current location {city}. {time_msg} Active Alert Check Interval {interval} minutes. Dynamic Alert Check Interval {active} minutes.",
            'interval_change_active': "{callsign} Notification. The monitoring interval is being changed to {interval} minutes due to active alerts in the area.",
            'interval_change_normal': "{callsign} Notification. Active alerts have expired. The monitoring interval is being changed back to {interval} minutes."
        },
        'fr': {
            'current_conditions_intro': "Conditions actuelles pour {city}, {region}.",
            'temperature': "La température est de {val} {unit}.",
            'conditions': "Les conditions sont {desc}{wind}.",
            'wind_with_dir': ", avec des vents du {dir} à {val} {unit}",
            'wind_no_dir': ", avec des vents à {val} {unit}",
            'forecast_intro': "Voici les prévisions.",
            'forecast_item': "{period}: {cond}.{temp}",
            'no_alerts': "Il n'y a aucune alerte météo active.",
            'active_alerts_count': "Il y a {count} alertes météo actives. ",
            'alert_issued': "Une {title} a été émise à {time}. ",
            'alert_effect': "Une {title} est en vigueur. ",
            'alert_effective_from': "Elle est en vigueur à partir de {time}. ",
            'alert_expires': "Elle expire à {time}. ",
            'clear': "{callsign} Terminé.",
            'time_msg': "Il est {time} {tz}. Heure fournie par {agency}.",
            'automated_report': "Ceci est le rapport météo automatisé pour {city}, {region}. Pause. [PAUSE]",
            'please_advise': "Veuillez noter : {alerts} Pause. [PAUSE]",
            'system_status': "État du système : Surveillance des événements de niveau {sev} et supérieurs. Alertes sonores actives pour les événements {tone_sev} et supérieurs. L'intervalle de surveillance est de {interval} minutes. Pause. [PAUSE]",
            'code_source': "A S L 3 underscore w x underscore announce est disponible sur github et développé par N 7 X O B comme code non commercial fourni au bénéfice de la communauté radioamateur.",
            'data_source_us': "Données fournies par le National Weather Service et le National Institute of Standards and Technology.",
            'data_source_ca': "Données fournies par Environnement Canada, le Conseil national de recherches du Canada et le Système national d'agrégation et de diffusion des alertes.",
            'intro_cq': "CQ CQ CQ. Ici {callsign} avec le rapport météo mis à jour.",
            'intro_good_day': "Bonjour.",
            'concludes': "Ceci conclut le rapport météo pour {city}. {callsign} Terminé.",
            'degrees': "degrés",
            'degrees_celsius': "degrés celsius",
            'mph': "milles par heure",
            'kph': "kilomètres par heure",
            'high': " Maximum",
            'low': " Minimum",
             # Test & Monitor Strings (French translations approx)
            'test_preamble': "{callsign} Essai. Ceci est un test d'alerte d'un système de notification et de message automatisé. Ne prenez aucune mesure suite au message suivant. Je répète - ne prenez aucune mesure - ceci n'est qu'un test. Les tonalités d'essai suivront dans 10 secondes.",
            'test_message': "Ceci est un message de test. Ceci est un exemple de message d'urgence. Ceci n'est qu'un test. Aucune action n'est requise.",
            'test_postamble': "{callsign} vous rappelle que ceci était un test. Ne prenez aucune mesure. Je répète - ne prenez aucune mesure. S'il s'agissait d'une urgence réelle, la tonalité précédente aurait été suivie d'informations spécifiques des autorités officielles sur une urgence imminente nécessitant votre attention immédiate et éventuellement une action pour prévenir la perte de vie, des blessures ou des dommages matériels. Ce test est terminé.",
            'monitor_online': "{callsign} Surveillance automatique en ligne. Données fournies par {source}. {nodes}Emplacement actuel {city}. {time_msg} Intervalle de vérification des alertes actives {interval} minutes. Intervalle de vérification dynamique {active} minutes.",
            'interval_change_active': "{callsign} Notification. L'intervalle de surveillance est modifié à {interval} minutes en raison d'alertes actives dans la région.",
            'interval_change_normal': "{callsign} Notification. Les alertes actives ont expiré. L'intervalle de surveillance revient à {interval} minutes."
        }
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        # Determine language (default en)
        self.lang = self.config.get('station', {}).get('announce_language', 'en')
        if self.lang not in self.STRINGS:
            self.lang = 'en'

    def _get_str(self, key: str, **kwargs) -> str:
        tmpl = self.STRINGS.get(self.lang, {}).get(key, self.STRINGS['en'].get(key, ""))
        return tmpl.format(**kwargs)

    def announce_conditions(self, loc: LocationInfo, current: CurrentConditions) -> str:
        is_us = (loc.country_code or "").upper() == 'US'
        
        # Temp Logic
        temp_val = int(current.temperature)
        temp_unit = "degrees_celsius"
        if is_us:
            temp_val = int((current.temperature * 9/5) + 32)
            temp_unit = "degrees" # US usually assumes F
            
        wind = ""
        # Low threshold for wind
        if current.wind_speed is not None and current.wind_speed > 2:
            direction = current.wind_direction
            
            # Expand abbreviations
            dirs = {
                "N": "North", "NNE": "North Northeast", "NE": "Northeast", "ENE": "East Northeast",
                "E": "East", "ESE": "East Southeast", "SE": "Southeast", "SSE": "South Southeast",
                "S": "South", "SSW": "South Southwest", "SW": "Southwest", "WSW": "West Southwest",
                "W": "West", "WNW": "West Northwest", "NW": "Northwest", "NNW": "North Northwest"
            }
            # French Directions (TODO: Complete list or keep EN for now if simple)
            # For now, simplistic approach: if lang is FR, we might need a separate map or just rely on EN abbreviations being understood or adding translation map.
            # Let's add basic map for FR if needed, or just let it pass for now.
            
            if direction and direction in dirs:
                direction = dirs[direction]
            
            # Wind Speed Logic
            speed_val = int(current.wind_speed)
            speed_unit = self._get_str('kph')
            if is_us:
                speed_val = int(current.wind_speed * 0.621371)
                speed_unit = self._get_str('mph')
            
            if direction:
                wind = self._get_str('wind_with_dir', dir=direction, val=speed_val, unit=speed_unit)
            else:
                wind = self._get_str('wind_no_dir', val=speed_val, unit=speed_unit)
        
        return (
            self._get_str('current_conditions_intro', city=loc.city, region=loc.region) + " " +
            self._get_str('temperature', val=temp_val, unit=self._get_str(temp_unit)) + " " + # temp_unit is key 'degrees' or 'degrees_celsius' now
            self._get_str('conditions', desc=current.description, wind=wind)
        )

    def announce_forecast(self, forecasts: List[WeatherForecast], loc: LocationInfo, verbose: bool = True) -> str:
        if not forecasts:
            return ""
            
        is_us = (loc.country_code or "").upper() == 'US'
        
        text = self._get_str('forecast_intro') + " "
        
        limit = 4 if not verbose else len(forecasts)
        
        for f in forecasts[:limit]: 
            temp = ""
            if f.high_temp is not None:
                val = f.high_temp
                if is_us: val = (val * 9/5) + 32
                temp = self._get_str('high') + f" {int(val)}."
            elif f.low_temp is not None:
                val = f.low_temp
                if is_us: val = (val * 9/5) + 32
                temp = self._get_str('low') + f" {int(val)}."
            
            # Always prefer short_summary if available for the new style
            condition = f.short_summary if f.short_summary else f.summary
                
            text += self._get_str('forecast_item', period=f.period_name, cond=condition, temp=temp) + " Break. [PAUSE] "
            
        return text

    def announce_alerts(self, alerts: List[WeatherAlert], loc: LocationInfo = None) -> str:
        if not alerts:
            return self._get_str('no_alerts')
        
        text = self._get_str('active_alerts_count', count=len(alerts))
        for a in alerts:
            # Format times
            fmt = "%I %M %p"
            
            issued_str = a.issued.strftime(fmt) if a.issued else ""
            eff_str = a.effective.strftime(fmt)
            exp_str = a.expires.strftime(fmt)
            
            # Construct message
            if issued_str:
                text += self._get_str('alert_issued', title=a.title, time=issued_str)
            else:
                text += self._get_str('alert_effect', title=a.title)
                
            # If effective is different from issued, mention it
            if a.effective and a.issued and abs((a.effective - a.issued).total_seconds()) > 600: # >10 mins diff
                 text += self._get_str('alert_effective_from', time=eff_str)
            
            # Expires
            text += self._get_str('alert_expires', time=exp_str)
            
        # Add sign-off to alerts
        if loc:
             full_callsign = self.get_full_callsign(loc)
             text += " " + self._get_str('clear', callsign=full_callsign)
        else:
             # Fallback if no loc passed (though we should always pass it)
             callsign = self.config.get('station', {}).get('callsign')
             if callsign: text += " " + self._get_str('clear', callsign=callsign)
             
        return text
             
        return text

    def get_clock_offset(self) -> float:
        """Returns the system clock offset in seconds, or None if unavailable."""
        try:
            result = subprocess.run(['chronyc', 'tracking'], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                return None
            match = re.search(r"Last offset\s*:\s*([+-]?\d+\.\d+)\s*seconds", result.stdout)
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None

    def get_time_offset_message(self, agency_name: str) -> str:
        """
        Returns string like "The system clock differs from [Agency] official time by 0.3 seconds."
        """
        offset = self.get_clock_offset()
        if offset is None:
            return ""
            
        abs_offset = abs(offset)
        # Format: "0.310"
        offset_str = f"{abs_offset:.3f}".rstrip('0').rstrip('.')
        
        if abs_offset < 0.000001: return "" # Too small
        
        return f"The system clock differs from {agency_name} official time by {offset_str} seconds."


    def get_full_callsign(self, loc: LocationInfo) -> str:
        """
        Determines the portable suffix based on location.
        Returns the formatted string e.g. "N7XOB Portable V E 3"
        """
        callsign = self.config.get('station', {}).get('callsign')
        if not callsign or not loc.country_code:
            return callsign or "Station"
            
        upper_call = callsign.upper()
        country = loc.country_code.upper()
        region = loc.region.upper().strip() if loc.region else ""

        # Region Normalization Map (Full Name -> Abbrev)
        # Providers (like reverse_geocoder) may return full names
        region_map = {
            # Canada
            "BRITISH COLUMBIA": "BC", "ALBERTA": "AB", "SASKATCHEWAN": "SK", "MANITOBA": "MB",
            "ONTARIO": "ON", "QUEBEC": "QC", "QUÉBEC": "QC", "NEW BRUNSWICK": "NB", "NOVA SCOTIA": "NS",
            "PRINCE EDWARD ISLAND": "PE", "NEWFOUNDLAND AND LABRADOR": "NL", "NEWFOUNDLAND": "NL",
            "YUKON": "YT", "NORTHWEST TERRITORIES": "NT", "NUNAVUT": "NU",
            # US (Common ones, extend as needed)
            "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA",
            "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA",
            "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
            "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
            "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO",
            "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ",
            "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH",
            "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
            "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT",
            "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
            "DISTRICT OF COLUMBIA": "DC"
        }
        
        # Normalize Region
        if region in region_map:
            region = region_map[region]

        # Handle accented characters if not caught by map (though we added QUÉBEC above)
        # This catch-all helps if there are other variations
        if region == "QUÉBEC":
             region = "QC"

        # Determine Origin (Simple heuristic: K,N,W,A=US; V,C=CA)
        origin_country = "US"
        # Callsigns starting with V, C, CY, VO, VY are Canadian
        if upper_call[0] in ['V', 'C'] or upper_call.startswith('VE') or upper_call.startswith('VA') or upper_call.startswith('VO') or upper_call.startswith('VY'):
            origin_country = "CA"
            
        suffix = ""
        
        # 1. Canadian Station in US -> "Portable [Zone]"
        if origin_country == "CA" and country == "US":
            # US Call Zones
            zones = {
                '1': ['CT', 'MA', 'ME', 'NH', 'RI', 'VT'],
                '2': ['NJ', 'NY'],
                '3': ['DE', 'DC', 'MD', 'PA'],
                '4': ['AL', 'FL', 'GA', 'KY', 'NC', 'SC', 'TN', 'VA'],
                '5': ['AR', 'LA', 'MS', 'NM', 'OK', 'TX'],
                '6': ['CA', 'HI'], # HI is KH6, often treated as 6 for this context
                '7': ['AZ', 'ID', 'MT', 'NV', 'OR', 'UT', 'WA', 'WY', 'AK'], # AK is KL7
                '8': ['MI', 'OH', 'WV'],
                '9': ['IL', 'IN', 'WI'],
                '0': ['CO', 'IA', 'KS', 'MN', 'MO', 'NE', 'ND', 'SD']
            }
            
            zone_num = None
            for z, states in zones.items():
                if region in states:
                    zone_num = z
                    break
            
            if zone_num:
                suffix = f" Portable N {zone_num}"
            else:
                suffix = " Portable U S"

        # 2. US Station in CA -> "Portable [Prefix] [Zone]"
        elif origin_country == "US" and country == "CA":
            # Canadian Prefixes Map
            provinces = {
                'BC': 'V E 7', 'AB': 'V E 6', 'SK': 'V E 5', 'MB': 'V E 4',
                'ON': 'V E 3', 'QC': 'V E 2', 'NB': 'V E 9', 'NS': 'V E 1',
                'PE': 'V Y 2', 'NL': 'V O 1', 'YT': 'V Y 1', 'NT': 'V E 8', 
                'NU': 'V Y 0'
            }
            
            # Fallback mappings for standard zones if precise prefix unknown
            fallback_map = {
                'BC': '7', 'AB': '6', 'SK': '5', 'MB': '4', 'ON': '3', 'QC': '2',
                'NB': '1', 'NS': '1', 'PE': '1', 'NL': '1', 'YT': '1', 'NT': '8', 'NU': '0' 
            }
            
            prefix_str = provinces.get(region)
            if not prefix_str:
                # Try fallback generic VE#
                digit = fallback_map.get(region)
                if digit:
                    prefix_str = f"V E {digit}"
            
            if prefix_str:
                suffix = f" Portable {prefix_str}"
            else:
                suffix = " Portable Canada"

        return f"{callsign}{suffix}"


    def build_full_report(self, loc: LocationInfo, current: CurrentConditions, forecast: List[WeatherForecast], alerts: List[WeatherAlert], sun_info: str = "", report_config: dict = None) -> str:
        parts = []
        
        # Default Config if None (Backward Compat)
        if report_config is None:
            report_config = {
                'time': True,
                'time_error': False,
                'conditions': True,
                'forecast': True,
                'forecast_verbose': False, 
                'astro': True,
                'solar_flux': False,
                'status': False,
                'code_source': False
            }
        
        # Time string: "10 30 PM"
        import pytz
        tz_name = self.config.get('location', {}).get('timezone', 'UTC')
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()
            
        now_str = now.strftime("%I %M %p")
        if now_str.startswith("0"): 
            now_str = now_str[1:]
        
        # State Expansion Map
        states_map = {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", 
            "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia", 
            "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", 
            "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", 
            "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", 
            "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", 
            "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", 
            "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", 
            "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
            "DC": "District of Columbia"
        }
        
        region_clean = loc.region.upper() if loc.region else ""
        region_full = states_map.get(region_clean, loc.region) 
        
        # Intro callsign logic
        callsign_raw = self.config.get('station', {}).get('callsign')
        
        if callsign_raw:
            full_callsign = self.get_full_callsign(loc)
            parts.append(self._get_str('intro_cq', callsign=full_callsign))
        else:
            parts.append(self._get_str('intro_good_day'))

        # Time Section
        if report_config.get('time', True):
            # Timezone Formatting
            tz_str = now.strftime("%Z")
            tz_map = {
                'EST': 'Eastern Standard Time', 'EDT': 'Eastern Daylight Time',
                'CST': 'Central Standard Time', 'CDT': 'Central Daylight Time',
                'MST': 'Mountain Standard Time', 'MDT': 'Mountain Daylight Time',
                'PST': 'Pacific Standard Time', 'PDT': 'Pacific Daylight Time',
                'AST': 'Atlantic Standard Time', 'ADT': 'Atlantic Daylight Time',
                'NST': 'Newfoundland Standard Time', 'NDT': 'Newfoundland Daylight Time',
                'AKST': 'Alaska Standard Time', 'AKDT': 'Alaska Daylight Time',
                'HST': 'Hawaii Standard Time', 'HDT': 'Hawaii Daylight Time'
            }
            # French TZ map? 
            # For now keep English TZ names or basic generic.
            
            full_tz = tz_map.get(tz_str, tz_str)
            
            # Attribution
            agency = "National Atomic"
            if loc.country_code == "US":
                agency = "National Institute of Standards and Technology"
            elif loc.country_code == "CA":
                agency = "National Research Council Canada"
                
            parts.append(self._get_str('time_msg', time=now_str, tz=full_tz, agency=agency))

        # Time Error Section (New Separate)
        if report_config.get('time_error', False):
             # Determine Agency Short Name for Error Message
             agency_short = "National Atomic"
             if loc.country_code == "US":
                 agency_short = "National Institute of Standards and Technology"
             elif loc.country_code == "CA":
                 agency_short = "National Research Council"
             
             msg = self.get_time_offset_message(agency_short)
             if msg: parts.append(msg + " Break. [PAUSE]")

        parts.append(self._get_str('automated_report', city=loc.city, region=region_full))
        
        if alerts:
             parts.append(self._get_str('please_advise', alerts=self.announce_alerts(alerts, loc)))
             
        # Conditions
        if report_config.get('conditions', True):
            parts.append(self.announce_conditions(loc, current) + " Break. [PAUSE]")
            
        # Forecast
        if report_config.get('forecast', True):
            is_verbose = report_config.get('forecast_verbose', False)
            parts.append(self.announce_forecast(forecast, loc, verbose=is_verbose))
        
        # Astro (Sun/Moon)
        if report_config.get('astro', True) and sun_info:
            parts.append(sun_info + " Break. [PAUSE]")

        # Solar Flux
        if report_config.get('solar_flux', False):
             try:
                 from .provider.astro import AstroProvider
                 ap = AstroProvider()
                 sfi = ap.get_solar_flux()
                 if sfi: parts.append(sfi + " Break. [PAUSE]")
             except Exception: pass

        # Status
        if report_config.get('status', False):
            interval = self.config.get('alerts', {}).get('check_interval_minutes', 10)
            sev = self.config.get('alerts', {}).get('min_severity', 'Watch')
            tone_sev = self.config.get('alerts', {}).get('alert_tone', {}).get('min_severity', 'Warning')
            parts.append(self._get_str('system_status', sev=sev, tone_sev=tone_sev, interval=interval))

        # Code Source
        if report_config.get('code_source', False):
            parts.append(self._get_str('code_source'))
            
            # Agency Credits
            if loc.country_code == 'US':
                parts.append(self._get_str('data_source_us'))
            elif loc.country_code == 'CA':
                parts.append(self._get_str('data_source_ca'))
                
            parts.append("Break. [PAUSE]")

        # Outro
        parts.append(self._get_str('concludes', city=loc.city, callsign=full_callsign))
            
        return " ".join(parts)

    def get_test_preamble(self, loc: LocationInfo = None) -> str:
        if loc:
            callsign = self.get_full_callsign(loc)
        else:
            callsign = self.config.get('station', {}).get('callsign', 'Amateur Radio')
            
        return self._get_str('test_preamble', callsign=callsign)

    def get_test_message(self) -> str:
        return self._get_str('test_message')

    def get_test_postamble(self, loc: LocationInfo = None) -> str:
        if loc:
            callsign = self.get_full_callsign(loc)
        else:
            callsign = self.config.get('station', {}).get('callsign', 'Amateur Radio')
            
        return self._get_str('test_postamble', callsign=callsign)

    def get_startup_message(self, loc: LocationInfo, interval: int, active_interval: int, nodes: List[str], source_name: str, hourly_config: dict = None) -> str:
        callsign = self.get_full_callsign(loc)
        city = loc.city if loc.city else "Unknown Location"
        
        node_str = ""
        if nodes:
            # Format nodes to be read as digits: "1234" -> "1 2 3 4"
            formatted_nodes = [" ".join(list(str(n))) for n in nodes]
            
            if len(formatted_nodes) == 1:
                node_str = f"Active on node {formatted_nodes[0]}. "
            else:
                joined = " and ".join(formatted_nodes)
                node_str = f"Active on nodes {joined}. "

        # Time Calc
        import pytz
        tz_name = self.config.get('location', {}).get('timezone', 'UTC')
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()
            
        now_str = now.strftime("%I %M %p")
        if now_str.startswith("0"): 
            now_str = now_str[1:]
            
        # Timezone Formatting
        tz_str = now.strftime("%Z")
        tz_map = {
            'EST': 'Eastern Standard Time', 'EDT': 'Eastern Daylight Time',
            'CST': 'Central Standard Time', 'CDT': 'Central Daylight Time',
            'MST': 'Mountain Standard Time', 'MDT': 'Mountain Daylight Time',
            'PST': 'Pacific Standard Time', 'PDT': 'Pacific Daylight Time',
            'AST': 'Atlantic Standard Time', 'ADT': 'Atlantic Daylight Time',
            'NST': 'Newfoundland Standard Time', 'NDT': 'Newfoundland Daylight Time',
            'AKST': 'Alaska Standard Time', 'AKDT': 'Alaska Daylight Time',
            'HST': 'Hawaii Standard Time', 'HDT': 'Hawaii Daylight Time'
        }
        full_tz = tz_map.get(tz_str, tz_str)

        # Offset Check
        agency_short = "National Atomic"
        if loc.country_code == "US":
             agency_short = "National Institute of Standards and Technology"
        elif loc.country_code == "CA":
             agency_short = "National Research Council"
             
        # We manually construct message here to add the warning if needed
        offset = self.get_clock_offset()
        offset_msg = ""
        
        if offset is not None:
            abs_offset = abs(offset)
            if abs_offset >= 0.000001:
                offset_str = f"{abs_offset:.3f}".rstrip('0').rstrip('.')
                offset_msg = f"The system clock differs from {agency_short} official time by {offset_str} seconds."
                
                # Critical Warning > 60s
                if abs_offset > 60:
                    offset_msg += " Time Error warrants correction to ensure timely notifications."

        time_msg = f"The time is {now_str} {full_tz}. {offset_msg}"

        # Using simpler localization for startup message to avoid overly complex templating
        msg = self._get_str('monitor_online', callsign=callsign, source=source_name, nodes=node_str, city=city, time_msg=time_msg, interval=interval, active=active_interval)

        if hourly_config and hourly_config.get('enabled', False):
            minute = hourly_config.get('minute', 0)
            msg += f"Hourly report is on. Hourly notifications will occur at {minute} minutes after the hour. "
            # TODO: Localize hourly report content listing if needed
        
        return msg

    def get_interval_change_message(self, interval_mins: int, active_alerts: bool, loc: LocationInfo = None) -> str:
        if loc:
             callsign = self.get_full_callsign(loc)
        else:
             callsign = self.config.get('station', {}).get('callsign', 'Station')
             
        if active_alerts:
             return self._get_str('interval_change_active', callsign=callsign, interval=interval_mins)
        else:
             return self._get_str('interval_change_normal', callsign=callsign, interval=interval_mins)
