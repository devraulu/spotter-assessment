import pytest

from trips import views
from trips.ratelimit import RateLimiter


@pytest.fixture(autouse=True)
def fresh_rate_limiter(monkeypatch):
    monkeypatch.setattr(views, "limiter", RateLimiter(views.limiter.limit, views.limiter.window_s))
    monkeypatch.setattr(views, "places_limiter", RateLimiter(views.places_limiter.limit, views.places_limiter.window_s))
