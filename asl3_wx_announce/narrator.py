from datetime import datetime
from typing import List
import subprocess
import re
from .models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert

class Narrator:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def announce_conditions(self, loc: LocationInfo, current: CurrentConditions) -> str:
        is_us = (loc.country_code or "").upper() == 'US'
        
        # Temp Logic
        temp_val = int(current.temperature)
        temp_unit = "degrees celsius"
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
            
            if direction and direction in dirs:
                direction = dirs[direction]
            
            # Wind Speed Logic
            speed_val = int(current.wind_speed)
            speed_unit = "kilometers per hour"
            if is_us:
                speed_val = int(current.wind_speed * 0.621371)
                speed_unit = "miles per hour"
            
            if direction:
                wind = f", with winds from the {direction} at {speed_val} {speed_unit}"
            else:
                wind = f", with winds at {speed_val} {speed_unit}"
        
        return (
            f"Current conditions for {loc.city}, {loc.region}. "
            f"The temperature is {temp_val} {temp_unit}. "
            f"Conditions are {current.description}{wind}."
        )

    def announce_forecast(self, forecasts: List[WeatherForecast], loc: LocationInfo, verbose: bool = True) -> str:
        if not forecasts:
            return ""
            
        is_us = (loc.country_code or "").upper() == 'US'
        
        text = "Here is the forecast. "
        
        limit = 4 if not verbose else len(forecasts)
        
        for f in forecasts[:limit]: 
            temp = ""
            if f.high_temp is not None:
                val = f.high_temp
                if is_us: val = (val * 9/5) + 32
                temp = f" High {int(val)}."
            elif f.low_temp is not None:
                val = f.low_temp
                if is_us: val = (val * 9/5) + 32
                temp = f" Low {int(val)}."
            
            # Always prefer short_summary if available for the new style
            condition = f.short_summary if f.short_summary else f.summary
                
            text += f"{f.period_name}: {condition}.{temp} Break. [PAUSE] "
            
        return text

    def announce_alerts(self, alerts: List[WeatherAlert]) -> str:
        if not alerts:
            return "There are no active weather alerts."
        
        text = f"There are {len(alerts)} active weather alerts. "
        for a in alerts:
            # Format times
            fmt = "%I %M %p"
            
            issued_str = a.issued.strftime(fmt) if a.issued else ""
            eff_str = a.effective.strftime(fmt)
            exp_str = a.expires.strftime(fmt)
            
            # Construct message
            item_text = f"A {a.title} "
            if issued_str:
                item_text += f"was issued at {issued_str}. "
            else:
                item_text += "is in effect. "
                
            # If effective is different from issued, mention it
            if a.effective and a.issued and abs((a.effective - a.issued).total_seconds()) > 600: # >10 mins diff
                 item_text += f"It is effective from {eff_str}. "
            
            # Expires
            item_text += f"It expires at {exp_str}. "
            
            text += item_text
            
        # Add sign-off to alerts
        callsign = self.config.get('station', {}).get('callsign')
        if callsign:
             text += f" {callsign} Clear."
             
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
        region = loc.region.upper() if loc.region else ""

        # Region Normalization Map (Full Name -> Abbrev)
        # Providers (like reverse_geocoder) may return full names
        region_map = {
            # Canada
            "BRITISH COLUMBIA": "BC", "ALBERTA": "AB", "SASKATCHEWAN": "SK", "MANITOBA": "MB",
            "ONTARIO": "ON", "QUEBEC": "QC", "NEW BRUNSWICK": "NB", "NOVA SCOTIA": "NS",
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
            parts.append(f"CQ CQ CQ. This is {full_callsign} with the updated weather report.")
        else:
            parts.append("Good day.")

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
            full_tz = tz_map.get(tz_str, tz_str)
            
            # Attribution
            agency = "National Atomic"
            if loc.country_code == "US":
                agency = "National Institute of Standards and Technology"
            elif loc.country_code == "CA":
                agency = "National Research Council Canada"
                
            parts.append(f"The time is {now_str} {full_tz}. Time provided by the {agency}.")

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

        parts.append(f"This is the automated weather report for {loc.city}, {region_full}. Break. [PAUSE]")
        
        if alerts:
             parts.append("Please be advised: " + self.announce_alerts(alerts) + " Break. [PAUSE]")
             
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
            parts.append(f"System status: Monitoring for {sev} level events and higher. Tone alerts active for {tone_sev} events and higher. Monitoring interval is {interval} minutes. Break. [PAUSE]")

        # Code Source
        if report_config.get('code_source', False):
            parts.append("A S L 3 underscore w x underscore announce is available on github and developed by N 7 X O B as non-commercial code provided for the benefit of the amateur radio community.")
            
            # Agency Credits
            if loc.country_code == 'US':
                parts.append("Data provided by the National Weather Service and the National Institute of Standards and Technology.")
            elif loc.country_code == 'CA':
                parts.append("Data provided by Environment Canada, National Research Council Canada, and the National Alert Aggregation and Dissemination System.")
                
            parts.append("Break. [PAUSE]")

        # Outro
        parts.append(f"This concludes the weather report for {loc.city}. {full_callsign} Clear.")
            
        return " ".join(parts)

    def get_test_preamble(self) -> str:
        callsign = self.config.get('station', {}).get('callsign', 'Amateur Radio')
        return (
            f"{callsign} Testing. The following is an alerting test of an automated alerting notification and message. "
            "Do not take any action as a result of the following message. "
            "Repeating - take no action - this is only a test. "
            "The test tones will follow in 10 seconds."
        )

    def get_test_message(self) -> str:
        return (
            "This is a test message. "
            "This is a sample emergency test message. "
            "This is only a test. No action is required."
        )

    def get_test_postamble(self) -> str:
        callsign = self.config.get('station', {}).get('callsign', 'Amateur Radio')
        return (
            f"{callsign} reminds you this was a test. "
            "Do not take action. Repeat - take no action. "
            "If this was an actual emergency, the preceding tone would be followed by specific information "
            "from official authorities on an imminent emergency that requires your immediate attention "
            "and possibly action to prevent loss of life, injury or property damage. "
            "This test is concluded."
        )


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

        msg = (
            f"{callsign} Automatic Monitoring Online. "
            f"Data provided by {source_name}. "
            f"{node_str}"
            f"Current location {city}. "
            f"{time_msg} "
            f"Active Alert Check Interval {interval} minutes. "
            f"Dynamic Alert Check Interval {active_interval} minutes. "
        )

        if hourly_config and hourly_config.get('enabled', False):
            minute = hourly_config.get('minute', 0)
            msg += f"Hourly report is on. Hourly notifications will occur at {minute} minutes after the hour. "
            
            content = hourly_config.get('content', {})
            enabled_items = []
            
            order = ['time', 'time_error', 'conditions', 'forecast', 'forecast_verbose', 'astro', 'solar_flux', 'status', 'code_source']
            
            for key in order:
                if content.get(key, False):
                    # Special handling for nicer speech
                    spoken = key.replace('_', ' ')
                    if key == 'astro': spoken = 'astronomy'
                    enabled_items.append(spoken)
            
            if enabled_items:
                if len(enabled_items) == 1:
                    msg += f"Content includes {enabled_items[0]}."
                else:
                    # Join with commas, and add "and" before last
                    joined_content = ", ".join(enabled_items[:-1]) + " and " + enabled_items[-1]
                    msg += f"Content includes {joined_content}."
        
        return msg

    def get_interval_change_message(self, interval_mins: int, active_alerts: bool) -> str:
        callsign = self.config.get('station', {}).get('callsign', 'Station')
        if active_alerts:
             return f"{callsign} Notification. The monitoring interval is being changed to {interval_mins} minute{'s' if interval_mins!=1 else ''} due to active alerts in the area."
        else:
             return f"{callsign} Notification. Active alerts have expired. The monitoring interval is being changed back to {interval_mins} minutes."
