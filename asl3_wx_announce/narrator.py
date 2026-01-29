from datetime import datetime
from typing import List
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

    def announce_forecast(self, forecasts: List[WeatherForecast], loc: LocationInfo) -> str:
        if not forecasts:
            return ""
            
        is_us = (loc.country_code or "").upper() == 'US'
        style = self.config.get('station', {}).get('report_style', 'verbose')
        
        text = "Here is the forecast. "
        
        # New Logic per user request:
        # Both modes use the concise "Quick" format (Short description + Temps).
        # "quick" mode: Limit to Today + Tomorrow (first 4 periods usually: Today, Tonight, Tomorrow, Tomorrow Night).
        # "verbose" mode: Full forecast duration (all periods).
        
        limit = 4 if style == 'quick' else len(forecasts)
        
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
            # "A Tornado Warning was issued at 3 00 PM. Effective from 3 15 PM until 4 00 PM."
            
            item_text = f"A {a.title} "
            if issued_str:
                item_text += f"was issued at {issued_str}. "
            else:
                item_text += "is in effect. "
                
            # If effective is different from issued, mention it
            if a.effective and a.issued and abs((a.effective - a.issued).total_seconds()) > 600: # >10 mins diff
                 item_text += f"It is effective from {eff_str}. "
            
            # Expires
            # Check if expires is dummy (e.g. for EC) or real
            # For now, just announce it if it's in the future or we assume it's valid
            item_text += f"It expires at {exp_str}. "
            
            text += item_text
            
        # Add sign-off to alerts
        callsign = self.config.get('station', {}).get('callsign')
        if callsign:
             text += f" {callsign} Clear."
             
        return text

    def build_full_report(self, loc: LocationInfo, current: CurrentConditions, forecast: List[WeatherForecast], alerts: List[WeatherAlert], sun_info: str = "") -> str:
        parts = []
        
        # Time string: "10 30 PM"
        import pytz
        tz_name = self.config.get('location', {}).get('timezone', 'UTC')
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()
            
        now_str = now.strftime("%I %M %p")
        # Remove leading zero from hour if desired, but TTS usually handles "09" fine. 
        # For cleaner TTS: 
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
        region_full = states_map.get(region_clean, loc.region) # Default to original if no match (e.g. "British Columbia")

        # Intro
        callsign = self.config.get('station', {}).get('callsign')
        full_callsign = callsign or ""
        
        if callsign:
            # Cross-border logic
            suffix = ""
            upper_call = callsign.upper()
            country = loc.country_code.upper() if loc.country_code else ""
            
            # US Ops (N, K, W) in Canada (CA) -> "Portable VE..."
            if country == 'CA' and (upper_call.startswith('N') or upper_call.startswith('K') or upper_call.startswith('W')):
                # default fallback
                ve_prefix = "V E" 
                
                # Map full province names (returned by EC provider) to prefixes
                # Note: keys must match what env_canada returns (Title Case generally)
                prov_map = {
                    "Nova Scotia": "V E 1",
                    "Quebec": "V E 2",
                    "Québec": "V E 2", # Handle accent
                    "Ontario": "V E 3",
                    "Manitoba": "V E 4",
                    "Saskatchewan": "V E 5",
                    "Alberta": "V E 6",
                    "British Columbia": "V E 7",
                    "Northwest Territories": "V E 8",
                    "New Brunswick": "V E 9",
                    "Newfoundland": "V O 1",
                    "Labrador": "V O 2",
                    "Yukon": "V Y 1",
                    "Prince Edward Island": "V Y 2",
                    "Nunavut": "V Y 0"
                }
                
                # Try to find province in region string
                region_title = loc.region.title() if loc.region else ""
                
                # Direct match or partial match? EC usually returns clean names.
                # However, let's check if the region is in our keys
                if region_title in prov_map:
                    ve_prefix = prov_map[region_title]
                else:
                    # Try code lookup if region was passed as code (e.g. AB, ON)
                    code_map = {
                        "NS": "V E 1", "QC": "V E 2", "ON": "V E 3", "MB": "V E 4",
                        "SK": "V E 5", "AB": "V E 6", "BC": "V E 7", "NT": "V E 8",
                        "NB": "V E 9", "NL": "V O 1", "YT": "V Y 1", "PE": "V Y 2", "NU": "V Y 0"
                    }
                    if loc.region.upper() in code_map:
                        ve_prefix = code_map[loc.region.upper()]

                suffix = f" Portable {ve_prefix}"
            
            # Canadian Ops (V) in US -> "Portable W..."
            elif country == 'US' and upper_call.startswith('V'):
                us_prefix = "W" # Fallback
                
                # Map States to US Call Regions (Source: provided file)
                # W0: CO, IA, KS, MN, MO, NE, ND, SD
                # W1: CT, ME, MA, NH, RI, VT
                # W2: NJ, NY
                # W3: DE, DC, MD, PA
                # W4: AL, FL, GA, KY, NC, SC, TN, VA
                # W5: AR, LA, MS, NM, OK, TX
                # W6: CA
                # W7: AZ, ID, MT, NV, OR, UT, WA, WY
                # W8: MI, OH, WV
                # W9: IL, IN, WI
                # WH6: HI, WL7: AK, WP4: PR, WP2: VI, WH2: GU, WH0: MP, WH8: AS
                
                zone_map = {
                    "Colorado": "W 0", "Iowa": "W 0", "Kansas": "W 0", "Minnesota": "W 0", 
                    "Missouri": "W 0", "Nebraska": "W 0", "North Dakota": "W 0", "South Dakota": "W 0",
                    
                    "Connecticut": "W 1", "Maine": "W 1", "Massachusetts": "W 1", "New Hampshire": "W 1", 
                    "Rhode Island": "W 1", "Vermont": "W 1",
                    
                    "New Jersey": "W 2", "New York": "W 2",
                    
                    "Delaware": "W 3", "District of Columbia": "W 3", "Maryland": "W 3", "Pennsylvania": "W 3",
                    
                    "Alabama": "W 4", "Florida": "W 4", "Georgia": "W 4", "Kentucky": "W 4", 
                    "North Carolina": "W 4", "South Carolina": "W 4", "Tennessee": "W 4", "Virginia": "W 4",
                    
                    "Arkansas": "W 5", "Louisiana": "W 5", "Mississippi": "W 5", "New Mexico": "W 5", 
                    "Oklahoma": "W 5", "Texas": "W 5",
                    
                    "California": "W 6",
                    
                    "Arizona": "W 7", "Idaho": "W 7", "Montana": "W 7", "Nevada": "W 7", 
                    "Oregon": "W 7", "Utah": "W 7", "Washington": "W 7", "Wyoming": "W 7",
                    
                    "Michigan": "W 8", "Ohio": "W 8", "West Virginia": "W 8",
                    
                    "Illinois": "W 9", "Indiana": "W 9", "Wisconsin": "W 9",
                    
                    "Hawaii": "W H 6", "Alaska": "W L 7", "Puerto Rico": "W P 4", "Virgin Islands": "W P 2",
                    "Guam": "W H 2", "American Samoa": "W H 8"
                }

                region_title = region_full.title() if region_full else ""
                
                # Try full name match
                if region_title in zone_map:
                    us_prefix = zone_map[region_title]
                else:
                     pass

                suffix = f" Portable {us_prefix}"
            
            full_callsign = f"{callsign}{suffix}"
            parts.append(f"CQ CQ CQ. This is {full_callsign} with the updated weather report.")
        else:
            parts.append("Good day.")
            

        
        # State Expansion (Done above)
        
        parts.append(f"The time is {now_str}.")
        parts.append(f"This is the automated weather report for {loc.city}, {region_full}. Break. [PAUSE]")
        
        if alerts:
             parts.append("Please be advised: " + self.announce_alerts(alerts) + " Break. [PAUSE]")
             
        parts.append(self.announce_conditions(loc, current) + " Break. [PAUSE]")
        parts.append(self.announce_forecast(forecast, loc))
        
        if sun_info:
            parts.append(sun_info + " Break. [PAUSE]")

        # Outro / Sign-off
        # "This concludes the weather report for (Location) (Callsign) Clear"
        # The forecast loop ends with a Break/[PAUSE] already, so this will be a new segment.
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

    def get_startup_message(self, city: str, interval: int) -> str:
        callsign = self.config.get('station', {}).get('callsign', 'Station')
        # "N7XOB Alerting Notification Active. Current location Quebec City. Checking interval is 10 minutes."
        return (
            f"{callsign} Alerting Notification Active. "
            f"Current location {city}. "
            f"Checking interval is {interval} minutes."
        )

    def get_interval_change_message(self, interval_mins: int, active_alerts: bool) -> str:
        callsign = self.config.get('station', {}).get('callsign', 'Station')
        if active_alerts:
             return f"{callsign} Notification. The monitoring interval is being changed to {interval_mins} minute{'s' if interval_mins!=1 else ''} due to active alerts in the area."
        else:
             return f"{callsign} Notification. Active alerts have expired. The monitoring interval is being changed back to {interval_mins} minutes."
