from asl3_wx_announce.narrator import Narrator
from asl3_wx_announce.models import LocationInfo, CurrentConditions, WeatherForecast, AlertSeverity
from datetime import datetime

def test_report():
    config = {
        'station': {'callsign': 'VE2TEST', 'report_style': 'quick'},
        'alerts': {'min_severity': 'Watch', 'check_interval_minutes': 15}
    }
    narrator = Narrator(config)
    
    loc = LocationInfo(latitude=45.0, longitude=-73.0, city="Test City", region="Quebec", country_code="CA", timezone="America/Toronto")
    curr = CurrentConditions(temperature=20, humidity=50, wind_speed=10, wind_direction="N", description="Sunny")
    fc = [WeatherForecast(period_name="Today", high_temp=25, summary="Sunny all day", short_summary="Sunny")]
    
    # Test 1: Full Report with SFI and Status
    report_cfg = {
        'conditions': True,
        'forecast': True,
        'forecast_verbose': False,
        'astro': True,
        'solar_flux': True, # Should fail gracefully or print nothing if no network
        'status': True
    }
    
    print("\n--- Test Report (All Enabled) ---")
    msg = narrator.build_full_report(loc, curr, fc, [], sun_info="Sunrise at 6am", report_config=report_cfg)
    print(msg)

    # Test 2: Minimal
    report_cfg_min = {
        'conditions': True,
        'forecast': False,
        'astro': False,
        'solar_flux': False,
        'status': False
    }
    print("\n--- Test Report (Minimal) ---")
    msg2 = narrator.build_full_report(loc, curr, fc, [], sun_info="Sunrise at 6am", report_config=report_cfg_min)
    print(msg2)

if __name__ == "__main__":
    test_report()
