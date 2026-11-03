from datetime import datetime
from typing import Protocol

from trips.types import HourlyWeather, Place, Route, Suggestion

Coord = tuple[float, float]


class ProviderError(Exception):
    pass


class NotFoundError(Exception):
    pass


class Geocoder(Protocol):
    def geocode(self, query: str) -> Place: ...


class PlaceSuggester(Protocol):
    def suggest(self, query: str) -> list[Suggestion]: ...


class Router(Protocol):
    def truck_routes(
        self,
        origin: Place,
        destination: Place,
        departure_at: datetime,
        weight_lb: float,
    ) -> list[Route]: ...


class WeatherProvider(Protocol):
    def hourly(
        self, coords: list[Coord], start: datetime, end: datetime
    ) -> dict[Coord, HourlyWeather]:
        ...
