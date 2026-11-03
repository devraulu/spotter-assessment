export type Level = "LOW" | "MODERATE" | "HIGH" | "SEVERE" | "NO_TRAVEL";
export type CheckpointLevel = Level | "UNKNOWN";
export type Interval = "10" | "25" | "50";

export interface TripRequest {
  origin: string;
  destination: string;
  departure_at: string;
  load_weight_lb: number;
}

export interface Place {
  label: string;
  lat: number;
  lon: number;
}

export interface Weather {
  wind_mph: number | null;
  gust_mph: number | null;
  rain_in_hr: number | null;
  snow_in_hr: number | null;
}

export interface Checkpoint {
  idx: number;
  mile: number;
  lat: number;
  lon: number;
  eta: string;
  weather: Weather;
  levels: {
    wind: CheckpointLevel;
    rain: CheckpointLevel;
    snow: CheckpointLevel;
  };
  base_level: CheckpointLevel;
  level: CheckpointLevel;
  load_adjusted: boolean;
  reason: string;
}

export interface RouteSummary {
  miles_by_level: Record<Level, number>;
  unknown_miles: number;
  avg_risk: number | null;
  max_level: CheckpointLevel;
  has_no_travel: boolean;
  rank: number;
}

export interface Route {
  id: string;
  distance_mi: number;
  duration_s: number;
  arrival_at: string;
  geometry: { type: "LineString"; coordinates: [number, number][] }; // [lon, lat]
  by_interval: Record<
    Interval,
    { checkpoints: Checkpoint[]; summary: RouteSummary }
  >;
}

export interface Recommendation {
  route_id: string;
  decided_by:
    | "no_travel"
    | "severe_miles"
    | "high_miles"
    | "avg_risk"
    | "duration"
    | "only_route";
  reason: string;
  all_routes_no_travel: boolean;
}

export interface Heatmap {
  start: string;
  hours: number;
  points: [number, number][]; // [lat, lon]
  risk: (number | null)[][];
}

export interface TripResponse {
  origin: Place;
  destination: Place;
  departure_at: string;
  load_weight_lb: number;
  routes: Route[];
  recommendation: Record<Interval, Recommendation>;
  heatmap: Heatmap;
}

export interface PlaceSuggestion {
  id: string;
  label: string;
}

export interface ApiError {
  error: string;
  field?: string | null;
}
