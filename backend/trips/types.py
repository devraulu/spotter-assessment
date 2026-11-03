from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Place:
    label: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Suggestion:
    id: str
    label: str


@dataclass(frozen=True)
class Route:
    distance_m: float
    duration_s: int
    coordinates: list[tuple[float, float]]  # (lon, lat), GeoJSON order


@dataclass(frozen=True)
class HourlyWeather:
    times: list[datetime]
    wind_mph: list[float | None]
    gust_mph: list[float | None]
    rain_in: list[float | None]
    snow_in: list[float | None]
