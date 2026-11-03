import json
from datetime import UTC, datetime

import pytest
import requests

from trips import views
from trips.providers import ProviderError
from trips.providers import here, open_meteo
from trips.providers.here import HereClient
from trips.providers.open_meteo import OpenMeteoClient
from trips.types import Place

from tests.payloads import (
    AUTOCOMPLETE,
    FORECAST_ERROR,
    GEOCODE,
    GEOCODE_EMPTY,
    ROUTES,
    forecast,
)

DEPARTURE = "2026-11-03T06:00:00-06:00"


class FakeResponse:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


class FakeHttp:

    def __init__(self, weather_status=200):
        self.calls = []
        self.weather_status = weather_status

    def __call__(self, url, params, timeout):
        self.calls.append((url, params))
        if url == here.GEOCODE_URL:
            return FakeResponse(GEOCODE.get(params["q"], GEOCODE_EMPTY))
        if url == here.AUTOCOMPLETE_URL:
            return FakeResponse(AUTOCOMPLETE)
        if url == here.ROUTES_URL:
            return FakeResponse(ROUTES)
        if url == open_meteo.FORECAST_URL:
            if self.weather_status != 200:
                return FakeResponse(FORECAST_ERROR, self.weather_status)
            n = len(params["latitude"].split(","))
            locations = [forecast() for _ in range(n)]
            return FakeResponse(locations if n > 1 else locations[0])
        raise AssertionError(f"unexpected URL {url}")

    def params_for(self, url):
        return [p for u, p in self.calls if u == url]


@pytest.fixture
def http(monkeypatch):
    fake = FakeHttp()
    monkeypatch.setattr(requests, "get", fake)
    return fake


def test_here_route_request_params(http):
    client = HereClient("secret")
    origin, destination = Place("A", 41.88, -87.63), Place("B", 39.74, -104.99)
    routes = client.truck_routes(
        origin, destination, datetime.fromisoformat(DEPARTURE), 42_000
    )

    (params,) = http.params_for(here.ROUTES_URL)
    assert params == {
        "transportMode": "truck",
        "origin": "41.88,-87.63",
        "destination": "39.74,-104.99",
        "alternatives": 2,
        "return": "polyline,summary",
        "departureTime": DEPARTURE,
        "vehicle[grossWeight]": 19051,
        "apiKey": "secret",
    }
    assert len(routes) == 3


def test_here_autocomplete_request_params(http):
    suggestions = HereClient("secret").suggest("Chica")
    (params,) = http.params_for(here.AUTOCOMPLETE_URL)
    assert params == {
        "q": "Chica",
        "in": "countryCode:USA",
        "limit": 5,
        "apiKey": "secret",
    }
    assert suggestions[0].label == "Chicago, IL, United States"


@pytest.mark.parametrize(
    "error", [requests.Timeout("timed out"), FakeResponse({}, 500)]
)
def test_here_failure_is_provider_error_without_key(monkeypatch, error):
    def fail(url, params, timeout):
        if isinstance(error, Exception):
            raise error
        return error

    monkeypatch.setattr(requests, "get", fail)
    with pytest.raises(ProviderError) as exc:
        HereClient("secret").geocode("Chicago, IL")
    assert "secret" not in str(exc.value)


def test_open_meteo_chunks_and_params(http):
    coords = [(40 + i / 100, -90.0) for i in range(250)]
    start = datetime(2026, 11, 3, 12, 30, tzinfo=UTC)
    end = datetime(2026, 11, 5, 12, 10, tzinfo=UTC)
    result = OpenMeteoClient().hourly(coords, start, end)

    calls = http.params_for(open_meteo.FORECAST_URL)
    assert [len(p["latitude"].split(",")) for p in calls] == [100, 100, 50]
    assert {
        k: calls[0][k]
        for k in ("hourly", "wind_speed_unit", "precipitation_unit", "timezone")
    } == {
        "hourly": "wind_speed_10m,wind_gusts_10m,rain,showers,snowfall",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
    }
    assert (calls[0]["start_hour"], calls[0]["end_hour"]) == (
        "2026-11-03T12:00",
        "2026-11-05T13:00",
    )
    assert len(result) == 250


def test_open_meteo_failed_chunk_is_left_out(monkeypatch):
    fake = FakeHttp(weather_status=400)
    monkeypatch.setattr(requests, "get", fake)
    assert (
        OpenMeteoClient().hourly(
            [(41.88, -87.63)],
            datetime(2026, 11, 3, 12, tzinfo=UTC),
            datetime(2026, 11, 5, 12, tzinfo=UTC),
        )
        == {}
    )


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 11, 3, 11, 0, tzinfo=UTC)


def post_trip(client, monkeypatch, origin="Chicago, IL"):
    monkeypatch.setattr(views, "datetime", FrozenDatetime)
    monkeypatch.setattr(views.settings, "HERE_API_KEY", "secret")
    body = {
        "origin": origin,
        "destination": "Denver, CO",
        "departure_at": DEPARTURE,
        "load_weight_lb": 42000,
    }
    return client.post("/api/trips", json.dumps(body), content_type="application/json")


def test_full_trip(client, monkeypatch, http):
    resp = post_trip(client, monkeypatch)
    assert resp.status_code == 200
    data = resp.json()

    assert data["origin"]["label"] == "Chicago, IL, United States"
    assert data["departure_at"] == "2026-11-03T12:00:00Z"
    assert [r["distance_mi"] for r in data["routes"]] == [1004.7, 1017.8, 1121.2]

    weather_calls = http.params_for(open_meteo.FORECAST_URL)
    coords = sum(len(p["latitude"].split(",")) for p in weather_calls)
    assert len(weather_calls) == -(-coords // 100)

    hourly = forecast()["hourly"]
    weather = data["routes"][0]["by_interval"]["10"]["checkpoints"][0]["weather"]
    assert weather == {
        "wind_mph": hourly["wind_speed_10m"][0],
        "gust_mph": hourly["wind_gusts_10m"][0],
        "rain_in_hr": round(hourly["rain"][0] + hourly["showers"][0], 3),
        "snow_in_hr": hourly["snowfall"][0],
    }
    assert all(None not in row for row in data["heatmap"]["risk"])


@pytest.mark.parametrize("interval", ["10", "25", "50"])
def test_checkpoint_weather_uses_eta_hour(client, monkeypatch, http, interval):
    data = post_trip(client, monkeypatch).json()
    hourly = forecast()["hourly"]
    start = datetime.fromisoformat(
        data["departure_at"]
    )

    cps = data["routes"][2]["by_interval"][interval][
        "checkpoints"
    ]
    for cp in cps:
        hour = round((datetime.fromisoformat(cp["eta"]) - start).total_seconds() / 3600)
        assert cp["weather"]["gust_mph"] == hourly["wind_gusts_10m"][hour], cp["mile"]
    assert {
        round((datetime.fromisoformat(cp["eta"]) - start).total_seconds() / 3600)
        for cp in cps
    } >= {0, 17}


@pytest.mark.parametrize(
    "origin, weather_status, status",
    [
        ("qxzqxzqxzqxz", 200, 422),
        ("Chicago, IL", 400, 200),
    ],
)
def test_full_trip_degraded(client, monkeypatch, origin, weather_status, status):
    monkeypatch.setattr(requests, "get", FakeHttp(weather_status=weather_status))
    resp = post_trip(client, monkeypatch, origin=origin)
    assert resp.status_code == status
    if status == 200:
        levels = {
            cp["level"]
            for r in resp.json()["routes"]
            for cp in r["by_interval"]["50"]["checkpoints"]
        }
        assert levels == {"UNKNOWN"}
