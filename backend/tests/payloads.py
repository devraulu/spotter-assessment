from datetime import datetime, timedelta

import flexpolyline

CHICAGO = (41.88425, -87.63245)
DENVER = (39.74001, -104.99202)


def _place(label, lat, lng):
    return {
        "items": [
            {
                "title": label,
                "id": "here:cm:namedplace:1",
                "resultType": "locality",
                "address": {"label": label, "countryCode": "USA"},
                "position": {"lat": lat, "lng": lng},
            }
        ]
    }


GEOCODE = {
    "Chicago, IL": _place("Chicago, IL, United States", *CHICAGO),
    "Denver, CO": _place("Denver, CO, United States", *DENVER),
}
GEOCODE_EMPTY = {"items": []}


def _route(via, length_m, duration_s):
    return {
        "sections": [
            {
                "type": "vehicle",
                "summary": {"duration": duration_s, "length": length_m},
                "polyline": flexpolyline.encode([CHICAGO, *via, DENVER]),
                "transport": {"mode": "truck"},
            }
        ]
    }


ROUTES = {
    "routes": [
        _route([(41.26, -95.93)], 1616943, 52969),
        _route([(39.10, -94.58)], 1637971, 53596),
        _route([(41.59, -93.62), (40.81, -96.70)], 1804420, 61847),
    ]
}
NO_ROUTE = {
    "notices": [
        {
            "title": "Route calculation failed: Couldn't find a route.",
            "code": "noRouteFound",
            "severity": "critical",
        }
    ],
    "routes": [],
}

AUTOCOMPLETE = {
    "items": [
        {
            "title": "United States, IL, 60602, Chicago",
            "id": "here:cm:namedplace:21002647",
            "resultType": "locality",
            "address": {"label": "Chicago, IL, United States", "countryCode": "USA"},
        }
    ]
}

FORECAST_ERROR = {"reason": "Invalid value", "error": True}


def forecast(start=datetime(2026, 11, 3, 12), hours=49):
    zeros = [0.0] * hours
    return {
        "latitude": 41.88,
        "longitude": -87.65,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "hourly_units": {
            "time": "iso8601",
            "wind_speed_10m": "mp/h",
            "wind_gusts_10m": "mp/h",
            "rain": "inch",
            "showers": "inch",
            "snowfall": "inch",
        },
        "hourly": {
            "time": [
                (start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M")
                for h in range(hours)
            ],
            "wind_speed_10m": [round(10 + h * 0.1, 1) for h in range(hours)],
            "wind_gusts_10m": [20.0 + h for h in range(hours)],
            "rain": [0.02] + zeros[1:],
            "showers": [0.01] + zeros[1:],
            "snowfall": zeros,
        },
    }
