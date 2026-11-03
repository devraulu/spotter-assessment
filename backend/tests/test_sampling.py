from datetime import UTC, datetime, timedelta

import pytest

from trips.sampling import checkpoint_miles, sample

DEPARTURE = datetime(2026, 11, 3, 12, tzinfo=UTC)


@pytest.mark.parametrize("distance, interval, expected", [
    (25, 10, [0, 10, 20, 25]),
    (20, 10, [0, 10, 20]),
    (5, 10, [0, 5]),
    (60, 25, [0, 25, 50, 60]),
])
def test_checkpoint_miles(distance, interval, expected):
    assert checkpoint_miles(distance, interval) == expected


def test_sample_scales_geometry_and_interpolates_eta():
    coords = [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0)]
    cps = sample(coords, distance_mi=100, duration_s=7200, departure=DEPARTURE, interval=50)

    assert [cp.mile for cp in cps] == [0, 50, 100]
    assert cps[1].lon == pytest.approx(0.5)
    assert (cps[-1].lon, cps[-1].lat) == coords[-1]
    assert [cp.eta - DEPARTURE for cp in cps] == [timedelta(0), timedelta(hours=1), timedelta(hours=2)]
