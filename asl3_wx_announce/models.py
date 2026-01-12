from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class AlertSeverity(str, Enum):
    UNKNOWN = "Unknown"
    ADVISORY = "Advisory"
    WATCH = "Watch"
    WARNING = "Warning"
    CRITICAL = "Critical"

class WeatherAlert(BaseModel):
    id: str
    severity: AlertSeverity
    title: str
    description: str
    instruction: Optional[str] = None
    area_description: str
    effective: datetime
    expires: datetime
    
    @property
    def is_active(self) -> bool:
        now = datetime.now(self.expires.tzinfo)
        return self.effective <= now < self.expires

class WeatherForecast(BaseModel):
    period_name: str  # e.g., "Today", "Tonight", "Monday"
    high_temp: Optional[float]  # Celsius
    low_temp: Optional[float]   # Celsius
    summary: str
    precip_probability: Optional[int]
    
class CurrentConditions(BaseModel):
    temperature: float  # Celsius
    humidity: Optional[int]
    wind_speed: Optional[float] # km/h
    wind_direction: Optional[str]
    description: str
    
class LocationInfo(BaseModel):
    latitude: float
    longitude: float
    city: str
    region: str  # State/Province
    country_code: str
    timezone: str
