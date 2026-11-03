from datetime import datetime

import flexpolyline
import requests

from trips.providers import NotFoundError, ProviderError
from trips.types import Place, Route, Suggestion

GEOCODE_URL = "https://geocode.search.hereapi.com/v1/geocode"
AUTOCOMPLETE_URL = "https://autocomplete.search.hereapi.com/v1/autocomplete"
ROUTES_URL = "https://router.hereapi.com/v8/routes"
LB_TO_KG = 0.45359237


def parse_geocode(data: dict, query: str) -> Place:
    items = data.get("items", [])
    if not items:
        raise NotFoundError(f"No location found for '{query}'")
    first = items[0]
    return Place(
        label=first["address"]["label"],
        lat=first["position"]["lat"],
        lon=first["position"]["lng"],
    )


def parse_autocomplete(data: dict) -> list[Suggestion]:
    return [Suggestion(id=item["id"], label=item["address"]["label"]) for item in data.get("items", [])]


def parse_routes(data: dict) -> list[Route]:
    if not data.get("routes"):
        raise NotFoundError("No truck route found between these locations")
    routes = []
    for route in data["routes"]:
        sections = route["sections"]
        coords = []
        for section in sections:
            coords += [(lon, lat) for lat, lon in flexpolyline.decode(section["polyline"])]
        routes.append(
            Route(
                distance_m=sum(s["summary"]["length"] for s in sections),
                duration_s=sum(s["summary"]["duration"] for s in sections),
                coordinates=coords,
            )
        )
    return routes


class HereClient:
    def __init__(self, api_key: str, timeout: float = 15):
        self.api_key = api_key
        self.timeout = timeout

    def _get(self, url: str, params: dict) -> dict:
        try:
            resp = requests.get(url, params={**params, "apiKey": self.api_key}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            # The URL contains the API key.
            raise ProviderError(f"HERE request failed: {type(e).__name__}") from None

    def geocode(self, query: str) -> Place:
        return parse_geocode(self._get(GEOCODE_URL, {"q": query}), query)

    def suggest(self, query: str) -> list[Suggestion]:
        params = {"q": query, "in": "countryCode:USA", "limit": 5}
        return parse_autocomplete(self._get(AUTOCOMPLETE_URL, params))

    def truck_routes(
        self, origin: Place, destination: Place, departure_at: datetime, weight_lb: float
    ) -> list[Route]:
        params = {
            "transportMode": "truck",
            "origin": f"{origin.lat},{origin.lon}",
            "destination": f"{destination.lat},{destination.lon}",
            "alternatives": 2,
            "return": "polyline,summary",
            "departureTime": departure_at.isoformat(),
            "vehicle[grossWeight]": round(weight_lb * LB_TO_KG),
        }
        return parse_routes(self._get(ROUTES_URL, params))
