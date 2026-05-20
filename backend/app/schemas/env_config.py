from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class TerrainType(str, Enum):
    FLAT = "flat"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"


class TerrainConfig(BaseModel):
    type: TerrainType = TerrainType.FLAT
    elevation_min: float = Field(0, ge=-1000, le=10000)
    elevation_max: float = Field(100, ge=0, le=20000)
    resolution: float = Field(1.0, ge=0.1, le=10.0)


class AtmosphereConfig(BaseModel):
    wind_speed: float = Field(5.0, ge=0, le=50)
    wind_direction: float = Field(90, ge=0, le=360)
    visibility: float = Field(10000, ge=100, le=100000)


class AircraftConfig(BaseModel):
    model: str = "c172x"
    mass: float = Field(1043, ge=100, le=100000)
    wingspan: float = Field(11.0, ge=1, le=100)


class RewardItem(BaseModel):
    name: str
    coefficient: float = Field(1.0, ge=-100, le=100)


class PenaltyItem(BaseModel):
    name: str
    coefficient: float = Field(-1.0, le=0, ge=-100)


class RewardConfig(BaseModel):
    items: List[RewardItem] = []
    penalties: List[PenaltyItem] = []


class ObstacleConfig(BaseModel):
    count: int = Field(0, ge=0, le=100)
    types: List[str] = []
    density: float = Field(0.0, ge=0, le=1.0)


class WaypointConfig(BaseModel):
    id: str
    position: List[float] = Field(..., min_length=3, max_length=3)
    order: int


class EnvConfig(BaseModel):
    terrain: TerrainConfig = TerrainConfig()
    atmosphere: AtmosphereConfig = AtmosphereConfig()
    aircraft: AircraftConfig = AircraftConfig()
    reward: RewardConfig = RewardConfig()
    obstacles: ObstacleConfig = ObstacleConfig()
    waypoints: List[WaypointConfig] = []
