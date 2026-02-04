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

    logger.info("Starting Alert Monitor...")
    
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
                text = narrator.announce_alerts(new_alerts)
                wav = handler.generate_audio(text, "alert.ul")
                handler.play_on_nodes(wav, nodes)
            
            # Cleanup expired from known
            known_alerts = known_alerts.intersection(current_ids)
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        time.sleep(interval)

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
