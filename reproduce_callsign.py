
import sys
import os

# Add the project root to sys.path so we can import modules
sys.path.append(os.getcwd())

from asl3_wx_announce.narrator import Narrator
from asl3_wx_announce.models import LocationInfo
import reverse_geocoder as rg

def test_callsign(region_input, lat, lon):
    print(f"--- Testing Region: '{region_input}' ---")
    config = {
        'station': {'callsign': 'N7XOB'},
        'location': {'latitude': lat, 'longitude': lon}
    }
    narrator = Narrator(config)
    
    loc = LocationInfo(
        latitude=lat,
        longitude=lon,
        city="Test City",
        region=region_input,
        country_code="US", # Will change conditionally for test? 
        # Wait, user is N7XOB (US) in Canada (QC).
        # So country_code of location should be CA.
        timezone="UTC"
    )
    # Correct country code for the location test
    loc.country_code = "CA"
    
    full_call = narrator.get_full_callsign(loc)
    print(f"Result: {full_call}")

def check_rg(lat, lon):
    print(f"--- Checking Reverse Geocoder for {lat}, {lon} ---")
    results = rg.search((lat, lon))
    print(f"RG Result: {results}")

if __name__ == "__main__":
    lat = 46.8139
    lon = -71.2080
    
    check_rg(lat, lon)
    
    # Test cases
    test_callsign("Quebec", lat, lon)
    test_callsign("Québec", lat, lon) # Accented
    test_callsign("QC", lat, lon)
    test_callsign("QC ", lat, lon)
