# Truck Routing

A web app that helps a truck driver pick the safest route between two places, taking into account weather, load weight and travel time.

Live: https://spotter.rauluis.com

Given an origin, destination, departure time and load weight, the app:

- fetches up to three truck routes,
- samples checkpoints along each route every 10, 25 or 50 miles and estimates when the truck reaches each one,
- looks up the hourly forecast at each checkpoint for that arrival time and assigns a risk level,
- recommends one route,
- shows the routes, checkpoints and per-segment risk on a map, plus a 48-hour risk heatmap along the corridor.

## Stack

- **Backend:** Django (plain JSON views, no DRF), managed with uv
- **Frontend:** React, TypeScript, Vite, Material UI, Leaflet, TanStack Query
- **Data:** HERE (geocoding, autocomplete, truck routing) and Open-Meteo (hourly forecasts)
- **Hosting:** the backend runs on Cloud Run; the frontend is a Cloudflare Worker that serves the static build and proxies `/api/*` to the backend

```
backend/   Django API (api/ settings, trips/ domain code, tests/)
frontend/  React app and the Cloudflare Worker (worker/)
```

## Risk rules

Each checkpoint gets a level for wind (sustained mph), rain (in/hr) and snow (in/hr). The checkpoint's level is the worst of the three.

| Level     | Wind (mph) | Rain (in/hr) | Snow (in/hr) |
|-----------|------------|--------------|--------------|
| Low       | < 25       | < 0.10       | < 0.5        |
| Moderate  | 25–34      | 0.10–0.24    | 0.5–0.9      |
| High      | 35–44      | 0.25–0.49    | 1.0–1.9      |
| Severe    | 45–54      | 0.50–1.00    | 2.0–3.0      |
| No Travel | ≥ 55       | > 1.00       | > 3.0        |

Heavier loads can raise a checkpoint's level:

- Wind of 35–44 mph with a load over 40,000 lb becomes **Severe**.
- Wind of 45–54 mph with a load over 30,000 lb becomes **No Travel**.

The level between two checkpoints is the worse of its two ends, and each route's miles are totalled per level.

## Recommendation

Routes are ranked by the following criteria, in order. A later criterion is only used to break a tie on the ones before it:

1. Avoids No Travel miles
2. Fewest Severe miles
3. Fewest High miles
4. Lowest average risk, weighted by miles
5. Shortest travel time

The response says which criterion decided the recommendation and shows the values being compared, for example "Fewest High miles (20 vs 45 vs 60)".

## Design decisions

- **Provider interfaces.** Geocoding, autocomplete, routing and weather are defined as `Protocol`s in `trips/providers/`. HERE and Open-Meteo implement them, and the pipeline only depends on the interfaces. Swapping a provider, or using a fake one in tests, doesn't touch the pipeline.
- **Pure domain code.** Risk assessment, sampling, summaries and ranking are plain functions with no I/O, tested with table-driven tests in `backend/tests/`.
- **Forecast at the arrival time, not the departure time.** Each checkpoint's ETA is estimated from its share of the route's total duration, and the forecast hour closest to that ETA is used. The heatmap is the one place that shows a fixed hour across the whole corridor.
- **One request per trip.** `POST /api/trips` returns all three sampling intervals and the heatmap together, so changing the interval or moving the heatmap slider doesn't call the API again. The cost is a larger response.
- **Sharing forecasts between routes.** Checkpoint coordinates are rounded to about 1 km and deduplicated before calling Open-Meteo. This saves calls because the alternative routes usually overlap heavily. Locations are sent to Open-Meteo in batches.
- **Missing weather becomes Unknown.** If a forecast request fails, the affected checkpoints are marked Unknown and left out of the average instead of failing the whole trip.
- **Protecting the HERE quota.** HERE's free tier has a monthly request limit. Autocomplete is debounced on the client and needs at least 3 characters. The backend rate-limits each client IP (10 trip requests and 60 place lookups per minute). The limiter keeps its counts in memory, which is enough with only a couple of instances.
- **No state library on the frontend.** React state plus TanStack Query is enough at this size. API calls are wrapped in hooks in `api.ts` so components don't depend on fetch details. Map layers are drawn as SVG in Leaflet.

## Running locally

Requirements: Python 3.13 with [uv](https://docs.astral.sh/uv/), Node 24 with pnpm 11, and a [HERE API key](https://platform.here.com/).

```bash
cp backend/.env.example backend/.env   # set HERE_API_KEY and SECRET_KEY
cd backend && uv sync && cd ..
cd frontend && pnpm install && cd ..
make dev    # Django on :8000, Vite on :5173 (proxies /api to Django)
make test   # backend tests
```

## Deployment

On every push to `main`, GitHub Actions runs the tests and then deploys the backend to Cloud Run with `gcloud run deploy --source backend`. It authenticates through Workload Identity Federation, so no service-account key is stored in GitHub. Secrets live in Secret Manager.

The frontend is built and deployed by Cloudflare's Git integration using `frontend/wrangler.jsonc`. The backend URL is set there in `BACKEND_URL`.

## Known limitations and next steps

- **No caching across requests.** Forecasts for the same corridor are fetched again on every search.
- **One large response.** The interval and heatmap data could be requested separately when the user asks for them.
- **Search isn't kept in the URL.** The search parameters could be stored in the URL so results can be shared and survive a page reload.
- **Simple ETA estimate.** It assumes a constant pace along the route and ignores required rest breaks.
