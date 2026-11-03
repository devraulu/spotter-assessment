from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from trips.providers import Geocoder, Router, WeatherProvider
from trips.risk import SCORES, assess
from trips.sampling import METERS_PER_MILE, Checkpoint, sample
from trips.summary import RouteStats, recommend, summarize
from trips.types import HourlyWeather, Place

INTERVALS = (10, 25, 50)
HEATMAP_HOURS = 48


@dataclass(frozen=True)
class TripRequest:
    origin: str
    destination: str
    departure_at: datetime
    load_weight_lb: float


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def coord_key(lat: float, lon: float, places: int = 2) -> tuple[float, float]:
    return (round(lat, places), round(lon, places))


def weather_at(forecast: HourlyWeather | None, when: datetime) -> dict:
    empty = {"wind_mph": None, "gust_mph": None, "rain_in_hr": None, "snow_in_hr": None}
    if forecast is None or not forecast.times:
        return empty
    i = round((when - forecast.times[0]).total_seconds() / 3600)
    if not 0 <= i < len(forecast.times):
        return empty
    return {
        "wind_mph": forecast.wind_mph[i],
        "gust_mph": forecast.gust_mph[i],
        "rain_in_hr": forecast.rain_in[i],
        "snow_in_hr": forecast.snow_in[i],
    }


def place_json(place: Place) -> dict:
    return {"label": place.label, "lat": place.lat, "lon": place.lon}


def checkpoint_json(cp: Checkpoint, forecasts: dict, weight_lb: float) -> dict:
    weather = weather_at(forecasts.get(coord_key(cp.lat, cp.lon)), cp.eta)
    a = assess(weather["wind_mph"], weather["rain_in_hr"], weather["snow_in_hr"], weight_lb)
    return {
        "idx": cp.idx,
        "mile": round(cp.mile, 1),
        "lat": round(cp.lat, 5),
        "lon": round(cp.lon, 5),
        "eta": iso_z(cp.eta),
        "weather": weather,
        "levels": a.levels,
        "base_level": a.base_level,
        "level": a.level,
        "load_adjusted": a.load_adjusted,
        "reason": a.reason,
    }


def build_heatmap(start: datetime, checkpoints: list[Checkpoint], forecasts: dict, weight_lb: float) -> dict:
    points = {}
    for cp in checkpoints:
        points.setdefault(coord_key(cp.lat, cp.lon, 1), cp)

    risk = []
    for cp in points.values():
        forecast = forecasts.get(coord_key(cp.lat, cp.lon))
        row = []
        for h in range(HEATMAP_HOURS + 1):
            w = weather_at(forecast, start + timedelta(hours=h))
            level = assess(w["wind_mph"], w["rain_in_hr"], w["snow_in_hr"], weight_lb).level
            row.append(SCORES.get(level))
        risk.append(row)

    return {
        "start": iso_z(start),
        "hours": HEATMAP_HOURS + 1,
        "points": [[round(cp.lat, 5), round(cp.lon, 5)] for cp in points.values()],
        "risk": risk,
    }


def plan_trip(req: TripRequest, geocoder: Geocoder, router: Router, weather: WeatherProvider) -> dict:
    origin = geocoder.geocode(req.origin)
    destination = geocoder.geocode(req.destination)
    routes = router.truck_routes(origin, destination, req.departure_at, req.load_weight_lb)
    departure = req.departure_at.astimezone(UTC)
    weight = req.load_weight_lb

    samples: dict[tuple[int, int], list[Checkpoint]] = {}
    for i, route in enumerate(routes):
        for n in INTERVALS:
            samples[i, n] = sample(route.coordinates, route.distance_m / METERS_PER_MILE, route.duration_s, departure, n)

    all_checkpoints = [cp for cps in samples.values() for cp in cps]
    coords = list(dict.fromkeys(coord_key(cp.lat, cp.lon) for cp in all_checkpoints))
    end = max([departure + timedelta(hours=HEATMAP_HOURS)] + [cp.eta for cp in all_checkpoints])
    forecasts = weather.hourly(coords, departure, end)

    routes_json = [
        {
            "id": f"r{i + 1}",
            "distance_mi": round(route.distance_m / METERS_PER_MILE, 1),
            "duration_s": route.duration_s,
            "arrival_at": iso_z(departure + timedelta(seconds=route.duration_s)),
            "geometry": {
                "type": "LineString",
                "coordinates": [[round(lon, 5), round(lat, 5)] for lon, lat in route.coordinates],
            },
            "by_interval": {},
        }
        for i, route in enumerate(routes)
    ]

    recommendation = {}
    for n in INTERVALS:
        stats = []
        for i, route_json in enumerate(routes_json):
            cps = samples[i, n]
            cps_json = [checkpoint_json(cp, forecasts, weight) for cp in cps]
            summary = summarize([cp.mile for cp in cps], [c["level"] for c in cps_json])
            stats.append(RouteStats(route_json["id"], summary, route_json["duration_s"]))
            route_json["by_interval"][str(n)] = {
                "checkpoints": cps_json,
                "summary": {
                    "miles_by_level": summary.miles_by_level,
                    "unknown_miles": summary.unknown_miles,
                    "avg_risk": summary.avg_risk,
                    "max_level": summary.max_level,
                    "has_no_travel": summary.has_no_travel,
                },
            }
        ranks, recommendation[str(n)] = recommend(stats)
        for route_json in routes_json:
            route_json["by_interval"][str(n)]["summary"]["rank"] = ranks[route_json["id"]]

    heatmap_start = departure.replace(minute=0, second=0, microsecond=0)
    heatmap_checkpoints = [cp for i in range(len(routes)) for cp in samples[i, 10]]

    return {
        "origin": place_json(origin),
        "destination": place_json(destination),
        "departure_at": iso_z(departure),
        "load_weight_lb": weight,
        "routes": routes_json,
        "recommendation": recommendation,
        "heatmap": build_heatmap(heatmap_start, heatmap_checkpoints, forecasts, weight),
    }
