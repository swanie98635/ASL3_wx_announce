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
        Checks 'source' config: 'fixed' or 'gpsd' (default).
        If 'gpsd' fails, falls back to fixed config.
        """
        loc_config = self.config.get('location', {})
        source = loc_config.get('source', 'gpsd')
        
        if source == 'fixed':
            return self._get_fixed_coords()

        if source == 'auto' or source == 'gpsd':
            try:
                return self._read_gpsd()
            except Exception as e:
                self.logger.warning(f"GPS read failed: {e}. Falling back to fixed/static.")
                return self._get_fixed_coords()
        
        # Default fallback
        return self._get_fixed_coords()

    def _get_fixed_coords(self) -> Tuple[float, float]:
        loc_config = self.config.get('location', {})
        # Try new 'fixed' block first
        fixed = loc_config.get('fixed', {})
        lat = fixed.get('lat')
        lon = fixed.get('lon')
        
        # Fallback to legacy top-level
        if lat is None:
            lat = loc_config.get('latitude')
        if lon is None:
            lon = loc_config.get('longitude')
            
        if lat is None or lon is None:
            raise ValueError("No valid location coordinates found in config (fixed or legacy) or GPS.")
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
