import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ApiError, PlaceSuggestion, TripRequest, TripResponse } from "@/types";

const MIN_PLACE_QUERY = 3;

export class TripError extends Error {
  status: number;
  field: string | null;

  constructor(status: number, body: ApiError) {
    super(body.error);
    this.status = status;
    this.field = body.field ?? null;
  }
}

async function parseError(resp: Response): Promise<TripError> {
  const body = await resp.json().catch(() => ({ error: `Request failed (${resp.status})` }));
  return new TripError(resp.status, body);
}

export async function fetchTrip(req: TripRequest): Promise<TripResponse> {
  const resp = await fetch("/api/trips", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok) throw await parseError(resp);
  return resp.json();
}

export async function fetchPlaces(query: string, signal?: AbortSignal): Promise<PlaceSuggestion[]> {
  const resp = await fetch(`/api/places?q=${encodeURIComponent(query)}`, { signal });
  if (!resp.ok) throw await parseError(resp);
  return (await resp.json()).suggestions;
}

export function useTrip(request: TripRequest | null) {
  return useQuery({
    queryKey: ["trip", request?.origin, request?.destination, request?.departure_at, request?.load_weight_lb],
    queryFn: () => fetchTrip(request!),
    enabled: request !== null,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    retry: false,
  });
}

export function usePlaceSuggestions(query: string) {
  const q = query.trim();
  return useQuery({
    queryKey: ["places", q],
    queryFn: ({ signal }) => fetchPlaces(q, signal),
    enabled: q.length >= MIN_PLACE_QUERY,
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    retry: false,
    placeholderData: keepPreviousData,
  });
}
