import json
from datetime import UTC, datetime, timedelta

import pytest

from trips import views
from trips.providers import NotFoundError, ProviderError
from trips.providers.here import parse_routes
from trips.types import HourlyWeather, Place

from tests.payloads import NO_ROUTE, ROUTES

DEPARTURE = (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0).isoformat()


class FakeHere:
    def __init__(self, routes=ROUTES, fail=False):
        self.routes, self.fail = routes, fail

    def geocode(self, query):
        if query == "Nowhere":
            raise NotFoundError("No location found for 'Nowhere'")
        return Place(query, 41.88, -87.63)

    def truck_routes(self, origin, destination, departure_at, weight_lb):
        if self.fail:
            raise ProviderError("HERE request failed: Timeout")
        return parse_routes(self.routes)


class FakeWeather:

    def __init__(self, wind=10.0, fail=False):
        self.wind, self.fail = wind, fail

    def hourly(self, coords, start, end):
        if self.fail:
            return {}
        first = start.replace(minute=0, second=0, microsecond=0)
        n = int((end - first).total_seconds() // 3600) + 2
        times = [first + timedelta(hours=h) for h in range(n)]
        w = HourlyWeather(times, [self.wind] * n, [self.wind + 5] * n, [0.0] * n, [0.0] * n)
        return {c: w for c in coords}


def post(client, monkeypatch, here=None, weather=None, **overrides):
    here = here or FakeHere()
    monkeypatch.setattr(views, "get_providers", lambda: (here, here, weather or FakeWeather()))
    body = {"origin": "Chicago, IL", "destination": "Denver, CO", "departure_at": DEPARTURE, "load_weight_lb": 42000}
    body.update(overrides)
    body = {k: v for k, v in body.items() if v is not ...}
    return client.post("/api/trips", json.dumps(body), content_type="application/json")


@pytest.mark.parametrize("overrides, field", [
    ({"origin": ...}, "origin"),
    ({"destination": "  "}, "destination"),
    ({"load_weight_lb": 0}, "load_weight_lb"),
    ({"load_weight_lb": "heavy"}, "load_weight_lb"),
    ({"departure_at": "2026-11-03T06:00:00"}, "departure_at"),
    ({"departure_at": "tomorrow"}, "departure_at"),
    ({"departure_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat()}, "departure_at"),
])
def test_validation(client, monkeypatch, overrides, field):
    resp = post(client, monkeypatch, **overrides)
    assert resp.status_code == 400
    assert resp.json()["field"] == field


@pytest.mark.parametrize("here, origin, status", [
    (FakeHere(), "Nowhere", 422),
    (FakeHere(NO_ROUTE), "Chicago, IL", 422),
    (FakeHere(fail=True), "Chicago, IL", 502),
])
def test_upstream_errors(client, monkeypatch, here, origin, status):
    assert post(client, monkeypatch, here=here, origin=origin).status_code == status


def test_success_shape(client, monkeypatch):
    data = post(client, monkeypatch).json()

    assert len(data["routes"]) == 3
    assert set(data["recommendation"]) == {"10", "25", "50"}
    for route in data["routes"]:
        cps = route["by_interval"]["10"]["checkpoints"]
        assert cps[0]["mile"] == 0 and cps[0]["eta"] == data["departure_at"]
        assert cps[-1]["mile"] == route["distance_mi"]
        assert route["by_interval"]["50"]["summary"]["rank"] in (1, 2, 3)
    heat = data["heatmap"]
    assert heat["hours"] == 49 and len(heat["risk"]) == len(heat["points"])
    assert all(len(row) == 49 for row in heat["risk"])
    first = data["routes"][0]["by_interval"]["10"]["checkpoints"][0]
    assert heat["points"][0] == [first["lat"], first["lon"]]


@pytest.mark.parametrize("wind, level, adjusted", [(10, "LOW", False), (38, "SEVERE", True)])
def test_load_adjusted_levels(client, monkeypatch, wind, level, adjusted):
    data = post(client, monkeypatch, weather=FakeWeather(wind=wind)).json()
    cp = data["routes"][0]["by_interval"]["25"]["checkpoints"][1]
    assert (cp["level"], cp["load_adjusted"]) == (level, adjusted)


def test_weather_failure_gives_unknown(client, monkeypatch):
    resp = post(client, monkeypatch, weather=FakeWeather(fail=True))
    assert resp.status_code == 200
    route = resp.json()["routes"][0]
    summary = route["by_interval"]["10"]["summary"]
    assert summary["unknown_miles"] == pytest.approx(route["distance_mi"], abs=0.1)
    assert route["by_interval"]["10"]["checkpoints"][0]["weather"]["wind_mph"] is None
