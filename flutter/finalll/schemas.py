from typing import Any, Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    location: Optional[Location] = None


class Intent(BaseModel):
    user_query: str
    intent: str
    language: str = "en"
    location: Location = Field(default_factory=Location)
    requested_parameters: list[str] = Field(default_factory=list)
    time_range: str = "current"
    hazards: list[str] = Field(default_factory=list)
    requires_route: bool = False
    requires_pfz: bool = False
    requires_geofence: bool = False
    requires_productivity: bool = False


class DataPoint(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    timestamp: Optional[str] = None
    distance_km: Optional[float] = None
    confidence: float = 0.0
    status: str = "unavailable"


class Conditions(BaseModel):
    sea_surface_temperature: DataPoint = Field(default_factory=DataPoint)
    wave_height: DataPoint = Field(default_factory=DataPoint)
    wave_period: DataPoint = Field(default_factory=DataPoint)
    wave_direction: DataPoint = Field(default_factory=DataPoint)
    current_speed: DataPoint = Field(default_factory=DataPoint)
    current_direction: DataPoint = Field(default_factory=DataPoint)
    sea_level: DataPoint = Field(default_factory=DataPoint)
    wind_speed: DataPoint = Field(default_factory=DataPoint)
    wind_direction: DataPoint = Field(default_factory=DataPoint)
    pressure: DataPoint = Field(default_factory=DataPoint)
    precipitation: DataPoint = Field(default_factory=DataPoint)
    weather_code: DataPoint = Field(default_factory=DataPoint)
    salinity: DataPoint = Field(default_factory=DataPoint)
    chlorophyll: DataPoint = Field(default_factory=DataPoint)
    mixed_layer_depth: DataPoint = Field(default_factory=DataPoint)


class Hazard(BaseModel):
    name: str
    status: str
    severity: str
    source: Optional[str] = None
    source_url: Optional[str] = None
    timestamp: Optional[str] = None
    details: Optional[str] = None


class PFZRecord(BaseModel):
    sector: str
    advisory_date: Optional[str] = None
    valid_upto: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    source: str = "INCOIS"
    source_url: str
    confidence: float = 0.0


class GeofenceHit(BaseModel):
    name: str
    zone_type: str
    inside: bool
    distance_km: float
    source: str


class RoutePoint(BaseModel):
    latitude: float
    longitude: float
    risk_cost: float = 0.0


class RouteResult(BaseModel):
    status: str
    distance_km: Optional[float] = None
    estimated_hours: Optional[float] = None
    risk_score: Optional[float] = None
    points: list[RoutePoint] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DataQuality(BaseModel):
    requested: int = 0
    available: int = 0
    completeness_percent: float = 0.0
    missing: list[str] = Field(default_factory=list)
    source_count: int = 0


class Evidence(BaseModel):
    id: str
    title: str
    source: str
    url: str
    type: str
    parameters: list[str] = Field(default_factory=list)
    timestamp: Optional[str] = None
    confidence: float = 0.0
    note: Optional[str] = None


class UnifiedData(BaseModel):
    intent: Intent
    location: Location
    conditions: Conditions
    hazards: list[Hazard] = Field(default_factory=list)
    pfz: list[PFZRecord] = Field(default_factory=list)
    geofences: list[GeofenceHit] = Field(default_factory=list)
    route: Optional[RouteResult] = None
    productivity: dict[str, Any] = Field(default_factory=dict)
    quality: DataQuality
    assessment: dict[str, Any]
    evidence: list[Evidence] = Field(default_factory=list)


class FinalLanguageOutput(BaseModel):
    status: str
    summary: str
    observations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    request_id: str
    conversation_id: str
    language: str
    location: Location
    intent: dict[str, Any]
    answer: dict[str, Any]
    ocean: dict[str, Any]
    weather: dict[str, Any]
    pfz: list[dict[str, Any]] = Field(default_factory=list)
    hazards: list[dict[str, Any]] = Field(default_factory=list)
    geofencing: list[dict[str, Any]] = Field(default_factory=list)
    route: Optional[dict[str, Any]] = None
    productivity: dict[str, Any] = Field(default_factory=dict)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    map: dict[str, Any] = Field(default_factory=dict)
