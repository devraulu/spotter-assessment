import json
import math
from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from trips.pipeline import TripRequest, plan_trip
from trips.providers import NotFoundError, ProviderError
from trips.providers.here import HereClient
from trips.providers.open_meteo import OpenMeteoClient
from trips.ratelimit import RateLimiter

REQUIRED = ("origin", "destination", "departure_at", "load_weight_lb")

limiter = RateLimiter(limit=10, window_s=60)
places_limiter = RateLimiter(limit=60, window_s=60)

MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 100


class ValidationError(Exception):
    def __init__(self, field: str | None, message: str):
        super().__init__(message)
        self.field = field


def parse_request(body: bytes, now: datetime) -> TripRequest:
    try:
        data = json.loads(body)
    except ValueError:
        raise ValidationError(None, "Request body must be valid JSON")
    if not isinstance(data, dict):
        raise ValidationError(None, "Request body must be a JSON object")

    for field in REQUIRED:
        if data.get(field) in (None, ""):
            raise ValidationError(field, f"{field} is required")

    for field in ("origin", "destination"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValidationError(field, f"{field} must be a non-empty string")

    weight = data["load_weight_lb"]
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
        raise ValidationError(
            "load_weight_lb", "load_weight_lb must be a number greater than 0"
        )

    try:
        departure = datetime.fromisoformat(data["departure_at"])
    except (TypeError, ValueError):
        departure = None
    if departure is None or departure.tzinfo is None:
        raise ValidationError(
            "departure_at", "departure_at must be ISO 8601 with a UTC offset"
        )
    if departure < now - timedelta(hours=1):
        raise ValidationError(
            "departure_at", "departure_at cannot be more than 1 hour in the past"
        )

    return TripRequest(
        data["origin"].strip(), data["destination"].strip(), departure, weight
    )


def rate_limited(limiter: RateLimiter, request) -> JsonResponse | None:
    retry_after = limiter.check(request.META.get("REMOTE_ADDR", ""))
    if not retry_after:
        return None
    resp = JsonResponse({"error": "Too many requests, try again shortly"}, status=429)
    resp["Retry-After"] = str(math.ceil(retry_after))
    return resp


def get_providers():
    here = HereClient(settings.HERE_API_KEY)
    return here, here, OpenMeteoClient()


@csrf_exempt
@require_POST
def trips(request):
    if blocked := rate_limited(limiter, request):
        return blocked

    try:
        trip = parse_request(request.body, datetime.now(UTC))
    except ValidationError as e:
        return JsonResponse({"error": str(e), "field": e.field}, status=400)

    geocoder, router, weather = get_providers()
    try:
        return JsonResponse(plan_trip(trip, geocoder, router, weather))
    except NotFoundError as e:
        return JsonResponse({"error": str(e)}, status=422)
    except ProviderError as e:
        return JsonResponse({"error": str(e)}, status=502)


def get_suggester():
    return HereClient(settings.HERE_API_KEY)


@require_GET
def places(request):
    if blocked := rate_limited(places_limiter, request):
        return blocked

    query = request.GET.get("q", "").strip()
    if len(query) > MAX_QUERY_LENGTH:
        return JsonResponse(
            {"error": f"q must be at most {MAX_QUERY_LENGTH} characters", "field": "q"},
            status=400,
        )
    if len(query) < MIN_QUERY_LENGTH:
        return JsonResponse({"suggestions": []})

    try:
        suggestions = get_suggester().suggest(query)
    except ProviderError as e:
        return JsonResponse({"error": str(e)}, status=502)
    return JsonResponse(
        {"suggestions": [{"id": s.id, "label": s.label} for s in suggestions]}
    )
