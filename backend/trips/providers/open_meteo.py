import logging
from datetime import UTC, datetime, timedelta

import requests

from trips.providers import Coord
from trips.types import HourlyWeather

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CHUNK_SIZE = 100
HOURLY = "wind_speed_10m,wind_gusts_10m,rain,showers,snowfall"


def _add(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else round(a + b, 3)


def parse_forecast(data: dict | list) -> list[HourlyWeather]:
    locations = data if isinstance(data, list) else [data]
    result = []
    for loc in locations:
        h = loc["hourly"]
        offset = timedelta(seconds=loc["utc_offset_seconds"])
        times = [
            (datetime.fromisoformat(t) - offset).replace(tzinfo=UTC) for t in h["time"]
        ]
        result.append(
            HourlyWeather(
                times=times,
                wind_mph=h["wind_speed_10m"],
                gust_mph=h["wind_gusts_10m"],
                rain_in=[_add(r, s) for r, s in zip(h["rain"], h["showers"])],
                snow_in=h["snowfall"],
            )
        )
    return result


def _hour(dt: datetime, round_up: bool) -> str:
    dt = dt.astimezone(UTC)
    floored = dt.replace(minute=0, second=0, microsecond=0)
    if round_up and floored < dt:
        floored += timedelta(hours=1)
    return floored.strftime("%Y-%m-%dT%H:%M")


class OpenMeteoClient:
    def __init__(self, timeout: float = 15):
        self.timeout = timeout

    def hourly(
        self, coords: list[Coord], start: datetime, end: datetime
    ) -> dict[Coord, HourlyWeather]:
        result = {}
        for i in range(0, len(coords), CHUNK_SIZE):
            chunk = coords[i : i + CHUNK_SIZE]
            params = {
                "latitude": ",".join(str(lat) for lat, _ in chunk),
                "longitude": ",".join(str(lon) for _, lon in chunk),
                "hourly": HOURLY,
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "UTC",
                "start_hour": _hour(start, round_up=False),
                "end_hour": _hour(end, round_up=True),
            }
            try:
                resp = requests.get(FORECAST_URL, params=params, timeout=self.timeout)
                resp.raise_for_status()
                result.update(zip(chunk, parse_forecast(resp.json())))
            except (requests.RequestException, ValueError, KeyError) as e:
                logger.warning("Open-Meteo chunk failed: %s", e)
        return result
