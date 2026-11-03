import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  CircleMarker,
  MapContainer,
  Pane,
  Polyline,
  Popup,
  TileLayer,
  Tooltip,
  ZoomControl,
  useMap,
} from "react-leaflet";
import L, { type LatLngExpression } from "leaflet";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { LevelDot } from "@/components/Legend";
import Legend from "@/components/Legend";
import { LEVEL_COLORS, LEVEL_LABELS, formatDuration } from "@/levels";
import { checkpointsAtHour, heatmapRows } from "@/heatmap";
import { routeSegments, type Segment } from "@/segments";
import { formatLocal } from "@/time";
import type {
  Checkpoint,
  CheckpointLevel,
  Interval,
  Route,
  TripResponse,
} from "@/types";

interface LayerProps {
  trip: TripResponse;
  interval: Interval;
  selectedId: string;
  onSelect: (routeId: string) => void;
  heatmapHour: number;
  showHeatmap: boolean;
}

const DOT_RADIUS: Record<Interval, number> = { "10": 2.5, "25": 3.5, "50": 4 };

const PANES = {
  routes: 410,
  recommended: 420,
  otherSegments: 425,
  outline: 430,
  segments: 440,
  checkpoints: 450,
} as const;
type PaneName = keyof typeof PANES;

function MapPane({ name, children }: { name: PaneName; children: ReactNode }) {
  return (
    <Pane name={name} style={{ zIndex: PANES[name], pointerEvents: "none" }}>
      {children}
    </Pane>
  );
}

function useSvgRenderers() {
  const [renderers] = useState(() => {
    const r = {} as Record<PaneName, L.SVG>;
    for (const name of Object.keys(PANES) as PaneName[]) {
      r[name] = L.svg({ pane: name });
    }
    return r;
  });
  return renderers;
}

const FIT_PADDING = {
  paddingTopLeft: [510, 40] as [number, number],
  paddingBottomRight: [40, 40] as [number, number],
};

function FitToRoutes({ routes }: { routes: Route[] }) {
  const map = useMap();
  useEffect(() => {
    const bounds = L.latLngBounds(
      routes.flatMap((r) =>
        r.geometry.coordinates.map(
          ([lon, lat]) => [lat, lon] as LatLngExpression,
        ),
      ),
    );
    if (bounds.isValid()) map.fitBounds(bounds, FIT_PADDING);
  }, [map, routes]);
  return null;
}

const fmt = (value: number | null, unit: string) =>
  value === null ? "n/a" : `${value} ${unit}`;

function Condition({
  name,
  value,
  level,
}: {
  name: string;
  value: string;
  level: CheckpointLevel;
}) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
      <LevelDot level={level} size={8} />
      {name} {value} · {LEVEL_LABELS[level]}
    </Box>
  );
}

function CheckpointDetails({
  routeId,
  cp,
}: {
  routeId: string;
  cp: Checkpoint;
}) {
  const w = cp.weather;
  return (
    <Typography component="div" variant="caption" sx={{ lineHeight: 1.7 }}>
      <Box sx={{ fontWeight: 700 }}>
        Route {routeId} · Mile {cp.mile} · {LEVEL_LABELS[cp.level]}
      </Box>
      <div>ETA {formatLocal(cp.eta)}</div>
      <Condition
        name="Wind"
        value={`${fmt(w.wind_mph, "mph")} (gusts ${fmt(w.gust_mph, "mph")})`}
        level={cp.levels.wind}
      />
      <Condition
        name="Rain"
        value={fmt(w.rain_in_hr, "in/hr")}
        level={cp.levels.rain}
      />
      <Condition
        name="Snow"
        value={fmt(w.snow_in_hr, "in/hr")}
        level={cp.levels.snow}
      />
      <Box sx={{ mt: 0.5 }}>{cp.reason}</Box>
      {cp.load_adjusted && (
        <Box sx={{ fontWeight: 700 }}>
          Raised from {LEVEL_LABELS[cp.base_level]} by load weight
        </Box>
      )}
    </Typography>
  );
}

const latLngs = (route: Route) =>
  route.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);

const HEAT_CASING = { color: "#0f172a", weight: 7, opacity: 0.35 };

function RouteLayers({
  trip,
  interval,
  selectedId,
  onSelect,
  heatmapHour,
  showHeatmap,
}: LayerProps) {
  const recommendedId = trip.recommendation[interval].route_id;
  const svg = useSvgRenderers();

  const selected = trip.routes.find((r) => r.id === selectedId);
  const others = trip.routes.filter((r) => r.id !== selectedId);
  const checkpoints = selected?.by_interval[interval].checkpoints ?? [];

  const rows = useMemo(
    () =>
      new Map(
        trip.routes.map((r) => [
          r.id,
          heatmapRows(trip.heatmap, r.by_interval["10"].checkpoints),
        ]),
      ),
    [trip],
  );

  const segmentsFor = (route: Route): Segment[] => {
    const levels = showHeatmap
      ? checkpointsAtHour(
          trip.heatmap,
          route.by_interval["10"].checkpoints,
          rows.get(route.id)!,
          heatmapHour,
        )
      : route.by_interval[interval].checkpoints;
    return routeSegments(route.geometry.coordinates, route.distance_mi, levels);
  };

  const heatTime = formatLocal(
    new Date(
      new Date(trip.heatmap.start).getTime() + heatmapHour * 3600_000,
    ).toISOString(),
  );

  const routeLabel = (route: Route) =>
    `Route ${route.id}${route.id === recommendedId ? " (recommended)" : ""} · ${route.distance_mi} mi · ${formatDuration(
      route.duration_s,
    )} · Rank ${route.by_interval[interval].summary.rank}`;

  const segmentTooltip = (route: Route, seg: Segment) => (
    <Tooltip sticky pane="tooltipPane">
      {routeLabel(route)}
      <br />
      Miles {seg.fromMile}–{seg.toMile}
      {showHeatmap ? ` at ${heatTime}` : ""}:{" "}
      <strong>{LEVEL_LABELS[seg.level]}</strong>
    </Tooltip>
  );

  return (
    <>
      <FitToRoutes routes={trip.routes} />

      {(["routes", "recommended"] as const).map((pane) => (
        <MapPane key={pane} name={pane}>
          {others
            .filter(
              (r) => (r.id === recommendedId) === (pane === "recommended"),
            )
            .map((route) => (
              <Polyline
                key={route.id}
                renderer={svg[pane]}
                positions={latLngs(route)}
                pathOptions={
                  showHeatmap
                    ? HEAT_CASING
                    : pane === "recommended"
                      ? { color: "#1d4ed8", weight: 9, opacity: 0.85 }
                      : { color: "#475569", weight: 6, opacity: 0.55 }
                }
                eventHandlers={{ click: () => onSelect(route.id) }}
              >
                <Tooltip sticky pane="tooltipPane">{routeLabel(route)}</Tooltip>
              </Polyline>
            ))}
        </MapPane>
      ))}

      <MapPane name="otherSegments">
        {showHeatmap &&
          others.flatMap((route) =>
            segmentsFor(route).map((seg, i) => (
              <Polyline
                key={`${route.id}-${i}`}
                renderer={svg.otherSegments}
                positions={seg.positions}
                pathOptions={{
                  color: LEVEL_COLORS[seg.level],
                  weight: 4,
                  opacity: 0.8,
                  lineCap: "butt",
                }}
                eventHandlers={{ click: () => onSelect(route.id) }}
              >
                {segmentTooltip(route, seg)}
              </Polyline>
            )),
          )}
      </MapPane>

      <MapPane name="outline">
        {selected && (
          <Polyline
            renderer={svg.outline}
            positions={latLngs(selected)}
            pathOptions={{ color: "#0f172a", weight: 14, opacity: 0.9 }}
            interactive={false}
          />
        )}
      </MapPane>

      <MapPane name="segments">
        {selected &&
          segmentsFor(selected).map((seg, i) => (
            <Polyline
              key={i}
              renderer={svg.segments}
              positions={seg.positions}
              pathOptions={{
                color: LEVEL_COLORS[seg.level],
                weight: 9,
                opacity: 1,
                lineCap: "butt",
              }}
            >
              {segmentTooltip(selected, seg)}
            </Polyline>
          ))}
      </MapPane>

      <MapPane name="checkpoints">
        {!showHeatmap &&
          checkpoints.map((cp) => (
            <CircleMarker
              key={cp.idx}
              renderer={svg.checkpoints}
              center={[cp.lat, cp.lon]}
              radius={DOT_RADIUS[interval]}
              pathOptions={{
                color: "#ffffff",
                weight: 1,
                fillColor: "#0f172a",
                fillOpacity: 1,
              }}
            >
              <Tooltip pane="tooltipPane">
                <CheckpointDetails routeId={selectedId} cp={cp} />
              </Tooltip>
              <Popup pane="popupPane">
                <CheckpointDetails routeId={selectedId} cp={cp} />
              </Popup>
            </CircleMarker>
          ))}
      </MapPane>
    </>
  );
}

export default function RouteMap(
  props: Omit<LayerProps, "trip"> & { trip: TripResponse | null },
) {
  return (
    <Box sx={{ position: "absolute", inset: 0 }}>
      <MapContainer
        center={[39.8, -95]}
        zoom={5}
        zoomControl={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ZoomControl position="topright" />
        {props.trip && <RouteLayers {...props} trip={props.trip} />}
      </MapContainer>
      <Legend />
    </Box>
  );
}
