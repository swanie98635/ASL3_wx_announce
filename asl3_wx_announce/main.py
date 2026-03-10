import argparse
import yaml
import time
import logging
from .models import AlertSeverity
from .location import LocationService
from .provider.factory import get_provider_instance
from .provider.astro import AstroProvider
from .narrator import Narrator
from .audio import AudioHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asl3_wx")

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def do_full_report(config):
    loc_svc = LocationService(config)
    lat, lon = loc_svc.get_coordinates()
    
    # Provider
    prov_code = config.get('location', {}).get('provider')
    provider = get_provider_instance(CountryCode=prov_code, Lat=lat, Lon=lon, Config=config)
    
    # Fetch Data
    loc_info = provider.get_location_info(lat, lon)
    logger.info(f"Resolved Location: {loc_info.city}, {loc_info.region} ({loc_info.country_code})")
    
    conditions = provider.get_conditions(lat, lon)
    forecast = provider.get_forecast(lat, lon)
    alerts = provider.get_alerts(lat, lon)
    
    # Astro
    astro = AstroProvider()
    sun_info = astro.get_astro_info(loc_info)
    
    # Narrate
    narrator = Narrator(config)
    text = narrator.build_full_report(loc_info, conditions, forecast, alerts, sun_info)
    logger.info(f"Report Text: {text}")
    
    # Audio
    handler = AudioHandler(config)
    wav_file = handler.generate_audio(text, "report.ul")
    
    # Play
    nodes = config.get('audio', {}).get('nodes', [])
    handler.play_on_nodes(wav_file, nodes)

def monitor_loop(config):
    interval = config.get('alerts', {}).get('check_interval_minutes', 10) * 60
    known_alerts = set()
    
    loc_svc = LocationService(config)
    narrator = Narrator(config)
    handler = AudioHandler(config)
    nodes = config.get('audio', {}).get('nodes', [])
    prov_code = config.get('location', {}).get('provider')

<<<<<<< HEAD
    logger.info("Starting Alert Monitor...")
=======
    logger.info(f"Starting Alert Monitor... (Hourly Reports: {do_hourly})")
    
    # Robust Wait for Asterisk
    if wait_for_asterisk():
        # Give a small buffer after it claims ready
        time.sleep(5) 
        
        try:
            # Startup Announcement
            # Resolve initial location info for city name
            # info variable is already fetched above
            city_name = info.city if info.city else "Unknown Location"
            interval_mins = int(normal_interval / 60)
            active_mins = config.get('alerts', {}).get('active_check_interval_minutes', 1)
            
            # Determine Source Name
            source_name = "National Weather Service" # Default fallback
            prov_class = provider.__class__.__name__
            
            if prov_class == 'ECProvider':
                source_name = "Environment Canada"
                if ar_provider: 
                    source_name += " and National Alert Ready System"
            elif prov_class == 'NWSProvider':
                 source_name = "National Weather Service"

            # Get Hourly Config
            hourly_cfg = config.get('station', {}).get('hourly_report', {})
            
            startup_text = narrator.get_startup_message(info, interval_mins, active_mins, nodes, source_name, hourly_config=hourly_cfg)
            logger.info(f"Startup Announcement: {startup_text}")
            
            # Generate and Play
            wav_files = handler.generate_audio(startup_text, filename="startup.gsm")
            if wav_files:
                handler.play_on_nodes(wav_files, nodes)
                
        except Exception as e:
            logger.error(f"Failed to play startup announcement: {e}")
            
    last_alert_check = 0
    last_location_check = time.time()
    last_report_hour = -1
>>>>>>> dfc4beb (Fix provider logic to prioritize coordinates and add location to startup message)
    
    while True:
        try:
            # Update location each interval for mobile nodes
            lat, lon = loc_svc.get_coordinates()
            # Re-init provider with new coords
            provider = get_provider_instance(CountryCode=prov_code, Lat=lat, Lon=lon, Config=config)
            
            alerts = provider.get_alerts(lat, lon)
            current_ids = {a.id for a in alerts}
            
            new_alerts = []
            for a in alerts:
                if a.id not in known_alerts:
                    new_alerts.append(a)
                    known_alerts.add(a.id)
            
            # Announce new items
            if new_alerts:
                logger.info(f"New Alerts detected: {len(new_alerts)}")
                loc_info = provider.get_location_info(lat, lon)
                text = narrator.announce_alerts(new_alerts, timezone=loc_info.timezone)
                wav = handler.generate_audio(text, "alert.ul")
                handler.play_on_nodes(wav, nodes)
            
            # Cleanup expired from known
            known_alerts = known_alerts.intersection(current_ids)
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
<<<<<<< HEAD
        time.sleep(interval)
=======
        # 1. Hourly Report Check
        # Check config struct
        hr_config = config.get('station', {}).get('hourly_report', {})
        # Handle legacy boolean if present (though we updated config)
        if isinstance(hr_config, bool):
            hr_enabled = hr_config
            hr_minute = 0
            hr_content = None # Use default
        else:
            hr_enabled = hr_config.get('enabled', False)
            hr_minute = hr_config.get('minute', 0)
            hr_content = hr_config.get('content') # dict or None

        if hr_enabled:
            # Check if minute matches and we haven't run this hour yet
            # Note: We track last_report_hour. If minute is 15, we run at 10:15.
            # We need to ensure we don't run multiple times in the same hour.
            if now_dt.minute == hr_minute and now_dt.hour != last_report_hour:
                logger.info(f"Triggering Hourly Weather Report (Scheduled for XX:{hr_minute:02d})...")
                try:
                    do_full_report(config, report_config=hr_content)
                    last_report_hour = now_dt.hour
                except Exception as e:
                    logger.error(f"Hourly Report Failed: {e}")
        
        # 2. Alert Check
        if (now - last_alert_check) > current_interval:
            last_alert_check = now
            try:
                logger.info(f"Checking for alerts... (Interval: {current_interval}s)")
                # Fetch Weather Alerts
                alerts = provider.get_alerts(lat, lon)
                
                # Fetch AlertReady Alerts
                if ar_provider:
                    try:
                        ar_alerts = ar_provider.get_alerts(lat, lon)
                        if ar_alerts:
                             logger.info(f"AlertReady found {len(ar_alerts)} items.")
                             alerts.extend(ar_alerts)
                    except Exception as e:
                        logger.error(f"AlertReady Check Failed: {e}")
                
                current_ids = {a.id for a in alerts}
                
                new_alerts = []
                for a in alerts:
                    if a.id not in known_alerts:
                        new_alerts.append(a)
                        known_alerts.add(a.id)
                
                # Check for Tone Trigger & Dynamic Polling
                tone_config = config.get('alerts', {}).get('alert_tone', {})
                ranks = {'Unknown': 0, 'Advisory': 1, 'Watch': 2, 'Warning': 3, 'Critical': 4}
                
                # 1. Determine Max Severity of ALL active alerts for Dynamic Polling
                max_severity_rank = 0
                for a in alerts: # Scan ALL active alerts
                     s_val = a.severity.value if hasattr(a.severity, 'value') else str(a.severity)
                     rank = ranks.get(s_val, 0)
                     if rank > max_severity_rank:
                         max_severity_rank = rank
                         
                # If Watch (2) or Higher, set interval to configured active interval
                new_interval = normal_interval
                active_threat = False
                
                if max_severity_rank >= 2:
                    # Default to 1 minute if not set
                    active_mins = config.get('alerts', {}).get('active_check_interval_minutes', 1)
                    new_interval = active_mins * 60
                    active_threat = True
                    logger.info(f"Active Watch/Warning/Critical detected. Requesting {active_mins}-minute polling.")
                
                # Check for Interval Change
                if new_interval != current_interval:
                    logger.info(f"Interval Change Detected: {current_interval} -> {new_interval}")
                    current_interval = new_interval
                    
                    mins = int(current_interval / 60)
                    msg = narrator.get_interval_change_message(mins, active_threat, loc=info)
                    logger.info(f"Announcing Interval Change: {msg}")
                    
                    try:
                        wavs = handler.generate_audio(msg, "interval_change.gsm")
                        handler.play_on_nodes(wavs, nodes)
                    except Exception as e:
                        logger.error(f"Failed to announce interval change: {e}")

                # 2. Check for Tone Trigger (New Alerts Only)
                if new_alerts and tone_config.get('enabled', False):
                    min_sev_str = tone_config.get('min_severity', 'Warning')
                    threshold = ranks.get(min_sev_str, 3)
                    
                    should_tone = False
                    for a in new_alerts:
                        s_val = a.severity.value if hasattr(a.severity, 'value') else str(a.severity)
                        if ranks.get(s_val, 0) >= threshold:
                            should_tone = True
                            break
                    
                    if should_tone:
                        logger.info("High severity alert detected. Playing Attention Signal.")
                        try:
                            tone_file = handler.ensure_alert_tone()
                            handler.play_on_nodes([tone_file], nodes)
                        except Exception as e:
                            logger.error(f"Failed to play alert tone: {e}")

                # Announce new items
                if new_alerts:
                    logger.info(f"New Alerts detected: {len(new_alerts)}")
                    text = narrator.announce_alerts(new_alerts, loc=info)
                    wavs = handler.generate_audio(text, "alert.gsm")
                    handler.play_on_nodes(wavs, nodes)
                
                # Cleanup expired from known
                known_alerts = known_alerts.intersection(current_ids)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
        
        # 3. Location Refresh Check
        loc_refresh_mins = config.get('location', {}).get('update_interval_minutes', 0)
        if loc_refresh_mins > 0:
            refresh_interval = loc_refresh_mins * 60
            if (now - last_location_check) > refresh_interval:
                last_location_check = now
                try:
                    logger.info("Checking for location update...")
                    new_lat, new_lon = loc_svc.get_coordinates()
                    
                    # Simple change detection (approx 100-200m difference)
                    if abs(new_lat - lat) > 0.002 or abs(new_lon - lon) > 0.002:
                        logger.info(f"Location changed: ({lat},{lon}) -> ({new_lat},{new_lon})")
                        lat, lon = new_lat, new_lon
                        
                        # Refresh Location Info (City/State)
                        info = provider.get_location_info(lat, lon)
                        logger.info(f"New Location Resolved: {info.city}, {info.region}")
                        
                        # Note: We rely on the next alert check to pick up the new zone/lat/lon
                except Exception as e:
                    logger.warning(f"Failed to refresh location: {e}")

        # Check every minute (resolution of the loop)
        time.sleep(60)

def do_test_alert(config):
    """
    Executes the comprehensive Test Alert sequence.
    """
    logger.info("Executing System Test Alert...")
    
    narrator = Narrator(config)
    handler = AudioHandler(config)
    nodes = config.get('voice', {}).get('nodes', [])

    if not nodes:
        logger.error("No nodes configured for playback.")
        return

    # Resolve Location for Callsign Logic
    loc_svc = LocationService(config)
    lat, lon = loc_svc.get_coordinates()
    prov_code = config.get('location', {}).get('provider')
    provider = get_provider_instance(CountryCode=prov_code, Lat=lat, Lon=lon, Config=config)
    loc_info = provider.get_location_info(lat, lon)

    # 1. Preamble
    logger.info("Playing Preamble...")
    preamble_text = narrator.get_test_preamble(loc=loc_info)
    files = handler.generate_audio(preamble_text, "test_preamble.gsm")
    handler.play_on_nodes(files, nodes)
    
    # 2. Silence (10s unkeyed)
    logger.info("Waiting 10s (Unkeyed)...")
    time.sleep(10)
    
    # 3. Alert Tone
    # Check if tone is enabled in config, otherwise force it for test? 
    # User said "The preceding tone" in postamble, so we should play it regardless of config setting for the TEST mode.
    logger.info("Playing Alert Tone...")
    tone_file = handler.ensure_alert_tone()
    handler.play_on_nodes([tone_file], nodes)
    
    # 4. Test Message
    logger.info("Playing Test Message...")
    msg_text = narrator.get_test_message()
    files = handler.generate_audio(msg_text, "test_message.gsm")
    handler.play_on_nodes(files, nodes)
    
    # 5. Postamble
    logger.info("Playing Postamble...")
    post_text = narrator.get_test_postamble(loc=loc_info)
    files = handler.generate_audio(post_text, "test_postamble.gsm")
    handler.play_on_nodes(files, nodes)
    
    logger.info("Test Alert Concluded.")
>>>>>>> dfc4beb (Fix provider logic to prioritize coordinates and add location to startup message)

def main():
    parser = argparse.ArgumentParser(description="ASL3 Weather Announcer")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--report", action="store_true", help="Play full weather report now")
    parser.add_argument("--monitor", action="store_true", help="Run in continuous monitor mode")
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    if args.report:
        do_full_report(config)
    elif args.monitor:
        monitor_loop(config)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
