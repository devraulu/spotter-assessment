import json

from trips import views
from trips.ratelimit import RateLimiter


def test_sliding_window():
    now = [0.0]
    limiter = RateLimiter(limit=2, window_s=60, clock=lambda: now[0])

    steps = [
        ("a", 0, 0),
        ("a", 1, 0),
        ("a", 2, 58),
        ("b", 2, 0),
        ("a", 60, 0),
        ("a", 60.5, 0.5),
    ]
    for key, t, expected in steps:
        now[0] = t
        assert limiter.check(key) == expected, (key, t)


def test_view_returns_429_with_retry_after(client):
    limit = views.limiter.limit
    responses = [client.post("/api/trips", "{}", content_type="application/json") for _ in range(limit + 1)]

    assert [r.status_code for r in responses] == [400] * limit + [429]
    assert int(responses[-1]["Retry-After"]) > 0
    assert json.loads(responses[-1].content) == {"error": "Too many requests, try again shortly"}
