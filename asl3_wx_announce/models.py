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
    onset: Optional[datetime] = None
    expires: datetime
    ends: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        start = self.onset if self.onset else self.effective
        end = self.ends if self.ends else self.expires
        now = datetime.now(end.tzinfo)
        return start <= now < end

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
