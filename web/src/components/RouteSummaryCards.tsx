import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { LevelDot } from "@/components/Legend";
import { LEVELS, LEVEL_LABELS, formatDuration } from "@/levels";
import { formatLocal } from "@/time";
import type { Interval, TripResponse } from "@/types";

interface Props {
  trip: TripResponse;
  interval: Interval;
  selectedId: string;
  onSelect: (routeId: string) => void;
}

export default function RouteSummaryCards({ trip, interval, selectedId, onSelect }: Props) {
  const rec = trip.recommendation[interval];
  const routes = [...trip.routes].sort(
    (a, b) => a.by_interval[interval].summary.rank - b.by_interval[interval].summary.rank,
  );

  return (
    <Stack spacing={1.5}>
      {rec.all_routes_no_travel && (
        <Alert severity="error" variant="outlined">
          Every route has No Travel conditions. No route is safe at this departure time.
        </Alert>
      )}

      {routes.map((route) => {
        const s = route.by_interval[interval].summary;
        const recommended = route.id === rec.route_id;
        const selected = route.id === selectedId;
        return (
          <Card
            key={route.id}
            variant="outlined"
            sx={{
              borderColor: selected ? "primary.main" : recommended ? "primary.light" : "divider",
              borderWidth: selected ? 2 : 1,
              bgcolor: recommended ? "rgba(37, 99, 235, 0.05)" : "background.paper",
            }}
          >
            <CardActionArea onClick={() => onSelect(route.id)} aria-pressed={selected}>
              <CardContent>
                <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
                    Route {route.id} · Rank {s.rank}
                  </Typography>
                  {recommended && <Chip label="Recommended" color="primary" size="small" />}
                </Stack>
                {recommended && (
                  <Typography variant="caption" color="primary.dark" sx={{ display: "block" }}>
                    {rec.reason}
                  </Typography>
                )}

                <Typography variant="body2" sx={{ mt: 1 }}>
                  {route.distance_mi} mi · {formatDuration(route.duration_s)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Arrives {formatLocal(route.arrival_at)}
                </Typography>

                <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", columnGap: 2, mt: 1 }}>
                  {LEVELS.map((level) => (
                    <Stack key={level} direction="row" spacing={0.75} sx={{ alignItems: "center" }}>
                      <LevelDot level={level} size={10} />
                      <Typography variant="caption">
                        {LEVEL_LABELS[level]}: {s.miles_by_level[level]} mi
                      </Typography>
                    </Stack>
                  ))}
                  {s.unknown_miles > 0 && (
                    <Stack direction="row" spacing={0.75} sx={{ alignItems: "center" }}>
                      <LevelDot level="UNKNOWN" size={10} />
                      <Typography variant="caption">Unknown: {s.unknown_miles} mi</Typography>
                    </Stack>
                  )}
                </Box>
                <Typography variant="caption" sx={{ display: "block", mt: 1 }}>
                  Avg risk {s.avg_risk ?? "n/a"} · Worst {LEVEL_LABELS[s.max_level]}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        );
      })}
    </Stack>
  );
}
