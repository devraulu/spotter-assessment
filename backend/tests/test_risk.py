import pytest

from trips.risk import (
    HIGH, LOW, MODERATE, NO_TRAVEL, SEVERE, UNKNOWN,
    assess, rain_level, snow_level, wind_level,
)


@pytest.mark.parametrize("mph, expected", [
    (24.9, LOW), (25, MODERATE), (34.9, MODERATE), (35, HIGH),
    (44.9, HIGH), (45, SEVERE), (54.9, SEVERE), (55, NO_TRAVEL),
])
def test_wind_level(mph, expected):
    assert wind_level(mph) == expected


@pytest.mark.parametrize("in_hr, expected", [
    (0.0999, LOW), (0.10, MODERATE), (0.25, HIGH),
    (0.50, SEVERE), (1.00, SEVERE), (1.01, NO_TRAVEL),
])
def test_rain_level(in_hr, expected):
    assert rain_level(in_hr) == expected


@pytest.mark.parametrize("in_hr, expected", [
    (0.49, LOW), (0.5, MODERATE), (1.0, HIGH),
    (2.0, SEVERE), (3.0, SEVERE), (3.01, NO_TRAVEL),
])
def test_snow_level(in_hr, expected):
    assert snow_level(in_hr) == expected


@pytest.mark.parametrize("wind, weight, base, level, adjusted", [
    (45, 30_000, SEVERE, SEVERE, False),
    (45, 30_001, SEVERE, NO_TRAVEL, True),
    (35, 40_000, HIGH, HIGH, False),
    (35, 40_001, HIGH, SEVERE, True),
    (34.9, 40_001, MODERATE, MODERATE, False),
    (55, 1, NO_TRAVEL, NO_TRAVEL, False),
])
def test_load_rules(wind, weight, base, level, adjusted):
    a = assess(wind, 0, 0, weight)
    assert (a.base_level, a.level, a.load_adjusted) == (base, level, adjusted)


@pytest.mark.parametrize("wind, rain, snow, weight, level, reason", [
    (10, 0, 0, 20_000, LOW, "No significant weather"),
    (38, 0.02, 0, 42_000, SEVERE, "Wind 38 mph with load over 40,000 lb"),
    (48, 0, 0, 35_000, NO_TRAVEL, "Wind 48 mph with load over 30,000 lb"),
    (10, 0.3, 0, 20_000, HIGH, "Rain 0.30 in/hr"),
    (10, 0, 2.5, 20_000, SEVERE, "Snow 2.5 in/hr"),
    (30, 0.6, 1.2, 20_000, SEVERE, "Rain 0.60 in/hr"),
    (None, 0, 0, 20_000, UNKNOWN, "Weather data unavailable"),
])
def test_assess(wind, rain, snow, weight, level, reason):
    a = assess(wind, rain, snow, weight)
    assert (a.level, a.reason) == (level, reason)
