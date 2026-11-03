import { useEffect, useMemo, useState } from "react";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { toast } from "sonner";
import { TripError, useTrip } from "@/api";
import HeatmapSlider from "@/components/HeatmapSlider";
import IntervalToggle from "@/components/IntervalToggle";
import RouteMap from "@/components/RouteMap";
import RouteSummaryCards from "@/components/RouteSummaryCards";
import TripForm from "@/components/TripForm";
import type { Interval, TripRequest } from "@/types";
import type { TripField } from "@/validation";

const PANEL_WIDTH = 470;

function errorMessage(error: Error): string {
  if (!(error instanceof TripError))
    return "Couldn't reach the server. Is the backend running?";
  if (error.status === 429)
    return "Too many requests. Wait a minute and try again.";
  return error.message;
}

const sameRequest = (a: TripRequest | null, b: TripRequest) =>
  a !== null && JSON.stringify(a) === JSON.stringify(b);

export default function App() {
  const [request, setRequest] = useState<TripRequest | null>(null);
  const [interval, setSelectedInterval] = useState<Interval>("10");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapHour, setHeatmapHour] = useState(0);
  const { data, error, isError, isFetching, refetch, dataUpdatedAt } =
    useTrip(request);

  const serverError = useMemo(
    () =>
      error instanceof TripError && error.field
        ? { field: error.field as TripField, message: error.message }
        : null,
    [error],
  );

  useEffect(() => {
    if (error) toast.error(errorMessage(error), { id: "trip" });
  }, [error]);

  useEffect(() => {
    if (!data) return;
    const rec = data.recommendation[interval];
    if (rec.all_routes_no_travel)
      toast.warning("Every route has No Travel conditions.", { id: "trip" });
    else
      toast.success(
        `${data.routes.length} route(s) found. Recommended: ${rec.route_id}.`,
        { id: "trip" },
      );
  }, [dataUpdatedAt]);

  const selected = selectedId ?? data?.recommendation[interval].route_id ?? "";

  function handleSubmit(next: TripRequest) {
    if (sameRequest(request, next) && isError) {
      refetch();
      return;
    }
    setSelectedId(null);
    setHeatmapHour(0);
    setRequest(next);
  }

  return (
    <Box
      sx={{
        position: "relative",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
      }}
    >
      <RouteMap
        trip={data ?? null}
        interval={interval}
        selectedId={selected}
        onSelect={setSelectedId}
        heatmapHour={heatmapHour}
        showHeatmap={showHeatmap}
      />

      <Paper
        component="aside"
        elevation={12}
        sx={{
          position: "absolute",
          top: 16,
          left: 16,
          zIndex: 1000,
          width: PANEL_WIDTH,
          maxHeight: "calc(100% - 32px)",
          overflowY: "auto",
          p: 3,
          display: "flex",
          flexDirection: "column",
          gap: 2.5,
          borderRadius: "24px",
        }}
      >
        <header>
          <Typography
            variant="h5"
            component="h1"
            sx={{
              fontWeight: 800,
              fontSize: "1.4rem",
              background: "linear-gradient(90deg, #1d4ed8, #4f46e5)",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            Truck Routing
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compare routes by weather risk for your load and departure time.
          </Typography>
        </header>

        <TripForm
          onSubmit={handleSubmit}
          loading={isFetching}
          serverError={serverError}
        />

        {data ? (
          <>
            <Divider />
            <IntervalToggle value={interval} onChange={setSelectedInterval} />
            <RouteSummaryCards
              trip={data}
              interval={interval}
              selectedId={selected}
              onSelect={setSelectedId}
            />
            <HeatmapSlider
              start={data.heatmap.start}
              hours={data.heatmap.hours}
              hour={heatmapHour}
              onHourChange={setHeatmapHour}
              show={showHeatmap}
              onShowChange={setShowHeatmap}
            />
          </>
        ) : (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ bgcolor: "grey.50", p: 2, borderRadius: 3 }}
          >
            Enter a trip to see up to three truck routes ranked by weather risk.
          </Typography>
        )}
      </Paper>
    </Box>
  );
}
