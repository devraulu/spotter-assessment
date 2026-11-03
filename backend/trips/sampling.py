import bisect
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

METERS_PER_MILE = 1609.344
EARTH_RADIUS_MI = 3958.8


@dataclass(frozen=True)
class Checkpoint:
    idx: int
    mile: float
    lat: float
    lon: float
    eta: datetime


def haversine_mi(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_MI * math.asin(math.sqrt(h))


def cumulative_mi(coords: list[tuple[float, float]]) -> list[float]:
    out = [0.0]
    for a, b in zip(coords, coords[1:]):
        out.append(out[-1] + haversine_mi(a, b))
    return out


def checkpoint_miles(distance_mi: float, interval: int) -> list[float]:
    miles = []
    k = 0
    while k * interval < distance_mi:
        miles.append(float(k * interval))
        k += 1
    miles.append(distance_mi)
    return miles


def point_at(coords: list[tuple[float, float]], cum: list[float], target: float) -> tuple[float, float]:
    if target <= 0:
        return coords[0]
    if target >= cum[-1]:
        return coords[-1]
    i = bisect.bisect_right(cum, target)
    seg = cum[i] - cum[i - 1]
    t = (target - cum[i - 1]) / seg if seg else 0.0
    (x1, y1), (x2, y2) = coords[i - 1], coords[i]
    return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)


def sample(
    coords: list[tuple[float, float]],
    distance_mi: float,
    duration_s: int,
    departure: datetime,
    interval: int,
) -> list[Checkpoint]:
    cum = cumulative_mi(coords)
    scale = cum[-1] / distance_mi if distance_mi else 0.0
    checkpoints = []
    for idx, mile in enumerate(checkpoint_miles(distance_mi, interval)):
        lon, lat = point_at(coords, cum, mile * scale)
        fraction = mile / distance_mi if distance_mi else 0.0
        eta = departure + timedelta(seconds=duration_s * fraction)
        checkpoints.append(Checkpoint(idx, mile, lat, lon, eta))
    return checkpoints
