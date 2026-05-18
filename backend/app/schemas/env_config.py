from pydantic import BaseModel, field_validator


class TerrainConfig(BaseModel):
    type: str = "mountain"
    elevation_min: float = 0.0
    elevation_max: float = 3000.0
    resolution: float = 1.0

    @field_validator("elevation_min")
    @classmethod
    def validate_elevation_min(cls, v: float) -> float:
        if v < 0 or v > 10000:
            raise ValueError("elevation_min must be between 0 and 10000")
        return v

    @field_validator("elevation_max")
    @classmethod
    def validate_elevation_max(cls, v: float) -> float:
        if v < 0 or v > 10000:
            raise ValueError("elevation_max must be between 0 and 10000")
        return v

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: float) -> float:
        if v < 0.1 or v > 100:
            raise ValueError("resolution must be between 0.1 and 100")
        return v


class WeatherConfig(BaseModel):
    wind_speed: float = 5.0
    wind_direction: float = 0.0
    visibility: float = 10000.0

    @field_validator("wind_speed")
    @classmethod
    def validate_wind_speed(cls, v: float) -> float:
        if v < 0 or v > 50:
            raise ValueError("wind_speed must be between 0 and 50")
        return v

    @field_validator("wind_direction")
    @classmethod
    def validate_wind_direction(cls, v: float) -> float:
        if v < 0 or v > 360:
            raise ValueError("wind_direction must be between 0 and 360")
        return v

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: float) -> float:
        if v < 0 or v > 50000:
            raise ValueError("visibility must be between 0 and 50000")
        return v


class FlightDynamicsConfig(BaseModel):
    aircraft_model: str = "c172p"
    mass: float = 1000.0
    wingspan: float = 11.0


class RewardItem(BaseModel):
    name: str
    coefficient: float = 1.0


class RewardConfig(BaseModel):
    reward_items: list[RewardItem] = []
    penalty_items: list[RewardItem] = []


class ObstacleConfig(BaseModel):
    count: int = 0
    types: list[str] = []
    density: float = 0.0

    @field_validator("count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("count must be between 0 and 100")
        return v

    @field_validator("density")
    @classmethod
    def validate_density(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("density must be between 0 and 1")
        return v


class Waypoint(BaseModel):
    id: str
    position: list[float]
    order: int = 0

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: list[float]) -> list[float]:
        if len(v) != 3:
            raise ValueError("position must have exactly 3 elements [x, y, z]")
        return v


class EnvConfig(BaseModel):
    terrain: TerrainConfig = TerrainConfig()
    weather: WeatherConfig = WeatherConfig()
    flight_dynamics: FlightDynamicsConfig = FlightDynamicsConfig()
    rewards: RewardConfig = RewardConfig()
    obstacles: ObstacleConfig = ObstacleConfig()
    waypoints: list[Waypoint] = []
