from typing import Tuple, Dict, Optional
import json
import logging
import socket

class LocationService:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def get_coordinates(self) -> Tuple[float, float]:
        """
        Returns (lat, lon). 
        Tries GPS first if configured, then falls back to static config.
        """
        if self.config.get('location', {}).get('type') == 'auto':
            try:
                return self._read_gpsd()
            except Exception as e:
                self.logger.warning(f"GPS read failed: {e}. Falling back to static.")
        
        # Static fallback
        lat = self.config.get('location', {}).get('latitude')
        lon = self.config.get('location', {}).get('longitude')
        if lat is None or lon is None:
            raise ValueError("No valid location coordinates found in config or GPS.")
        return float(lat), float(lon)

    def _read_gpsd(self) -> Tuple[float, float]:
        # Simple socket reader for GPSD standard port 2947
        # We start the WATCH command and wait for a TPV report
        try:
            with socket.create_connection(('localhost', 2947), timeout=2) as sock:
                sock.sendall(b'?WATCH={"enable":true,"json":true}\n')
                fp = sock.makefile()
                for line in fp:
                    data = json.loads(line)
                    if data.get('class') == 'TPV':
                        lat = data.get('lat')
                        lon = data.get('lon')
                        if lat and lon:
                            return lat, lon
        except Exception as e:
            raise e
        raise RuntimeError("No TPV data received from GPSD")
