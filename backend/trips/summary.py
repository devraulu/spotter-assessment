from dataclasses import dataclass

from trips.risk import HIGH, NO_TRAVEL, SCORES, SEVERE, UNKNOWN, max_level


@dataclass(frozen=True)
class Summary:
    miles_by_level: dict[str, float]
    unknown_miles: float
    avg_risk: float | None
    max_level: str
    has_no_travel: bool


def segment_level(a: str, b: str) -> str:
    known = [level for level in (a, b) if level != UNKNOWN]
    return max_level(*known) if known else UNKNOWN


def summarize(miles: list[float], levels: list[str]) -> Summary:
    by_level = {level: 0.0 for level in SCORES}
    unknown = 0.0
    for i in range(len(miles) - 1):
        length = miles[i + 1] - miles[i]
        level = segment_level(levels[i], levels[i + 1])
        if level == UNKNOWN:
            unknown += length
        else:
            by_level[level] += length

    known_miles = sum(by_level.values())
    avg = round(sum(SCORES[l] * m for l, m in by_level.items()) / known_miles, 2) if known_miles else None
    known_levels = [l for l in levels if l != UNKNOWN]
    by_level = {l: round(m, 1) for l, m in by_level.items()}
    return Summary(
        miles_by_level=by_level,
        unknown_miles=round(unknown, 1),
        avg_risk=avg,
        max_level=max_level(*known_levels) if known_levels else UNKNOWN,
        has_no_travel=by_level[NO_TRAVEL] > 0,
    )


@dataclass(frozen=True)
class RouteStats:
    route_id: str
    summary: Summary
    duration_s: int


RANK_KEYS = ["no_travel", "severe_miles", "high_miles", "avg_risk", "duration"]

REASON_LABELS = {
    "no_travel": "Avoids No Travel miles",
    "severe_miles": "Fewest Severe miles",
    "high_miles": "Fewest High miles",
    "avg_risk": "Lowest average risk",
    "duration": "Fastest",
}


def rank_key(r: RouteStats) -> tuple:
    s = r.summary
    avg = s.avg_risk if s.avg_risk is not None else float("inf")
    return (s.has_no_travel, s.miles_by_level[SEVERE], s.miles_by_level[HIGH], avg, r.duration_s)


def _display(key: str, r: RouteStats) -> str:
    s = r.summary
    if key == "no_travel":
        return f"{s.miles_by_level[NO_TRAVEL]:g}"
    if key == "severe_miles":
        return f"{s.miles_by_level[SEVERE]:g}"
    if key == "high_miles":
        return f"{s.miles_by_level[HIGH]:g}"
    if key == "avg_risk":
        return "n/a" if s.avg_risk is None else f"{s.avg_risk:.2f}"
    return f"{r.duration_s / 3600:.1f} h"


def recommend(routes: list[RouteStats]) -> tuple[dict[str, int], dict]:
    ranked = sorted(routes, key=rank_key)
    ranks = {r.route_id: i + 1 for i, r in enumerate(ranked)}
    best = ranked[0]
    all_no_travel = all(r.summary.has_no_travel for r in routes)

    if len(routes) == 1:
        return ranks, {
            "route_id": best.route_id,
            "decided_by": "only_route",
            "reason": "Only route available",
            "all_routes_no_travel": all_no_travel,
        }

    first, second = rank_key(ranked[0]), rank_key(ranked[1])
    decided_by = next((k for k, a, b in zip(RANK_KEYS, first, second) if a != b), "duration")
    values = " vs ".join(_display(decided_by, r) for r in routes)
    return ranks, {
        "route_id": best.route_id,
        "decided_by": decided_by,
        "reason": f"{REASON_LABELS[decided_by]} ({values})",
        "all_routes_no_travel": all_no_travel,
    }
