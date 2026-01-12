from abc import ABC, abstractmethod
from typing import List, Tuple
from ..models import LocationInfo, CurrentConditions, WeatherForecast, WeatherAlert

class WeatherProvider(ABC):
    """
    Abstract Base Class for Country-Specific Weather Providers.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize provider with arbitrary config.
        """
        pass

    @abstractmethod
    def get_location_info(self, lat: float, lon: float) -> LocationInfo:
        """
        Resolve lat/lon to standard location info (City, Region, etc.).
        """
        pass

    @abstractmethod
    def get_conditions(self, lat: float, lon: float) -> CurrentConditions:
        """
        Get current weather observations.
        """
        pass

    @abstractmethod
    def get_forecast(self, lat: float, lon: float) -> List[WeatherForecast]:
        """
        Get daily forecast periods.
        """
        pass

    @abstractmethod
    def get_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """
        Get active weather alerts.
        """
        pass
