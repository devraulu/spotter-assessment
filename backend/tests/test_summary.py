import pytest

from trips.risk import HIGH, LOW, MODERATE, NO_TRAVEL, SEVERE, UNKNOWN
from trips.summary import RouteStats, Summary, recommend, segment_level, summarize


@pytest.mark.parametrize("a, b, expected", [
    (LOW, HIGH, HIGH),
    (UNKNOWN, MODERATE, MODERATE),
    (SEVERE, UNKNOWN, SEVERE),
    (UNKNOWN, UNKNOWN, UNKNOWN),
])
def test_segment_level(a, b, expected):
    assert segment_level(a, b) == expected


def test_summarize():
    s = summarize([0, 10, 20, 25], [LOW, HIGH, UNKNOWN, UNKNOWN])
    assert s.miles_by_level == {LOW: 0, MODERATE: 0, HIGH: 20, SEVERE: 0, NO_TRAVEL: 0}
    assert (s.unknown_miles, s.avg_risk, s.max_level, s.has_no_travel) == (5, 2.0, HIGH, False)


def stats(route_id, nt=0.0, severe=0.0, high=0.0, avg=0.0, duration=3600):
    miles = {LOW: 0.0, MODERATE: 0.0, HIGH: high, SEVERE: severe, NO_TRAVEL: nt}
    return RouteStats(route_id, Summary(miles, 0.0, avg, LOW, nt > 0), duration)


@pytest.mark.parametrize("routes, best, decided_by, reason", [
    ([stats("r1")], "r1", "only_route", "Only route available"),
    ([stats("r1", nt=5), stats("r2", severe=90)], "r2", "no_travel", "Avoids No Travel miles (5 vs 0)"),
    ([stats("r1"), stats("r2", severe=50), stats("r3", severe=25)], "r1", "severe_miles",
     "Fewest Severe miles (0 vs 50 vs 25)"),
    ([stats("r1", high=12.5), stats("r2", high=3)], "r2", "high_miles", "Fewest High miles (12.5 vs 3)"),
    ([stats("r1", avg=0.4), stats("r2", avg=0.12)], "r2", "avg_risk", "Lowest average risk (0.40 vs 0.12)"),
    ([stats("r1", duration=54000), stats("r2", duration=50400)], "r2", "duration", "Fastest (15.0 h vs 14.0 h)"),
])
def test_recommend(routes, best, decided_by, reason):
    ranks, rec = recommend(routes)
    assert (rec["route_id"], rec["decided_by"], rec["reason"]) == (best, decided_by, reason)
    assert ranks[best] == 1


@pytest.mark.parametrize("routes, expected", [
    ([stats("r1", nt=1), stats("r2", nt=2)], True),
    ([stats("r1", nt=1), stats("r2")], False),
])
def test_all_routes_no_travel(routes, expected):
    assert recommend(routes)[1]["all_routes_no_travel"] is expected
