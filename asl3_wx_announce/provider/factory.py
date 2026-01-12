import reverse_geocoder as rg
from typing import Type
from .base import WeatherProvider
from .nws import NWSProvider
from .ec import ECProvider

# Registry to hold provider classes
_PROVIDERS = {
    "US": NWSProvider,
    "CA": ECProvider
}

def register_provider(country_code: str, provider_cls: Type[WeatherProvider]):
    _PROVIDERS[country_code.upper()] = provider_cls

def get_provider_class(lat: float, lon: float) -> Type[WeatherProvider]:
    """
    Determines the appropriate provider class based on location.
    """
    try:
        # result is a list of dicts: [{'lat': '...', 'lon': '...', 'name': 'City', 'admin1': 'Region', 'cc': 'US'}]
        results = rg.search((lat, lon))
        cc = results[0]['cc'].upper()
        
        if cc in _PROVIDERS:
            return _PROVIDERS[cc]
        
        print(f"Warning: No explicit provider for {cc}, defaulting to generic if possible or erroring.")
        raise ValueError(f"No weather provider found for country code: {cc}")
        
    except Exception as e:
        raise e

def get_provider_instance(CountryCode: str = None, Lat: float = None, Lon: float = None, Config: dict = None) -> WeatherProvider:
    if CountryCode:
        cls = _PROVIDERS.get(CountryCode.upper())
        if not cls:
            raise ValueError(f"Unknown country code: {CountryCode}")
        return cls(**(Config or {}))
    
    if Lat is not None and Lon is not None:
        cls = get_provider_class(Lat, Lon)
        return cls(**(Config or {}))
    
    raise ValueError("Must provide either CountryCode or Lat/Lon to select provider.")
