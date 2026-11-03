from dataclasses import dataclass

LOW = "LOW"
MODERATE = "MODERATE"
HIGH = "HIGH"
SEVERE = "SEVERE"
NO_TRAVEL = "NO_TRAVEL"
UNKNOWN = "UNKNOWN"

SCORES = {LOW: 0, MODERATE: 1, HIGH: 2, SEVERE: 3, NO_TRAVEL: 4}


def max_level(*levels: str) -> str:
    return max(levels, key=SCORES.__getitem__)


def wind_level(mph: float) -> str:
    if mph >= 55:
        return NO_TRAVEL
    if mph >= 45:
        return SEVERE
    if mph >= 35:
        return HIGH
    if mph >= 25:
        return MODERATE
    return LOW


def rain_level(in_hr: float) -> str:
    if in_hr > 1.00:
        return NO_TRAVEL
    if in_hr >= 0.50:
        return SEVERE
    if in_hr >= 0.25:
        return HIGH
    if in_hr >= 0.10:
        return MODERATE
    return LOW


def snow_level(in_hr: float) -> str:
    if in_hr > 3.0:
        return NO_TRAVEL
    if in_hr >= 2.0:
        return SEVERE
    if in_hr >= 1.0:
        return HIGH
    if in_hr >= 0.5:
        return MODERATE
    return LOW


def load_level(wind_mph: float, weight_lb: float) -> str:
    if 45 <= wind_mph < 55 and weight_lb > 30_000:
        return NO_TRAVEL
    if 35 <= wind_mph < 45 and weight_lb > 40_000:
        return SEVERE
    return LOW


@dataclass(frozen=True)
class Assessment:
    levels: dict[str, str]
    base_level: str
    level: str
    load_adjusted: bool
    reason: str


def assess(
    wind_mph: float | None, rain_in_hr: float | None, snow_in_hr: float | None, weight_lb: float
) -> Assessment:
    if wind_mph is None or rain_in_hr is None or snow_in_hr is None:
        unknown = {"wind": UNKNOWN, "rain": UNKNOWN, "snow": UNKNOWN}
        return Assessment(unknown, UNKNOWN, UNKNOWN, False, "Weather data unavailable")

    levels = {
        "wind": wind_level(wind_mph),
        "rain": rain_level(rain_in_hr),
        "snow": snow_level(snow_in_hr),
    }
    base = max_level(*levels.values())
    level = max_level(base, load_level(wind_mph, weight_lb))
    load_adjusted = SCORES[level] > SCORES[base]

    if load_adjusted:
        limit = "30,000" if level == NO_TRAVEL else "40,000"
        reason = f"Wind {wind_mph:g} mph with load over {limit} lb"
    elif level == LOW:
        reason = "No significant weather"
    elif levels["wind"] == level:
        reason = f"Wind {wind_mph:g} mph"
    elif levels["rain"] == level:
        reason = f"Rain {rain_in_hr:.2f} in/hr"
    else:
        reason = f"Snow {snow_in_hr:.1f} in/hr"

    return Assessment(levels, base, level, load_adjusted, reason)
