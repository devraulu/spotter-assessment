import { useState, type ChangeEvent } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import PlaceAutocomplete from "@/components/PlaceAutocomplete";
import { localToOffsetIso, nextHourLocal } from "@/time";
import type { TripRequest } from "@/types";
import {
  validateTrip,
  type FieldErrors,
  type TripField,
  type TripFormValues,
} from "@/validation";

interface Props {
  onSubmit: (request: TripRequest) => void;
  loading: boolean;
  serverError: { field: TripField; message: string } | null;
}

export default function TripForm({ onSubmit, loading, serverError }: Props) {
  const [values, setValues] = useState<TripFormValues>({
    origin: "Chicago, IL",
    destination: "Denver, CO",
    departure: nextHourLocal(),
    weight: "42000",
  });
  const [clientErrors, setClientErrors] = useState<FieldErrors>({});
  const [dismissed, setDismissed] = useState<Props["serverError"]>(null);

  const errors: FieldErrors = { ...clientErrors };
  if (serverError && serverError !== dismissed)
    errors[serverError.field] ??= serverError.message;

  function update(key: keyof TripFormValues, field: TripField, value: string) {
    setValues((v) => ({ ...v, [key]: value }));
    setClientErrors((e) => ({ ...e, [field]: undefined }));
    if (serverError?.field === field) setDismissed(serverError);
  }

  function handleSubmit(e: ChangeEvent) {
    e.preventDefault();
    const found = validateTrip(values);
    setClientErrors(found);
    if (Object.keys(found).length > 0) return;
    onSubmit({
      origin: values.origin.trim(),
      destination: values.destination.trim(),
      departure_at: localToOffsetIso(values.departure),
      load_weight_lb: Number(values.weight),
    });
  }

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      noValidate
      sx={{ display: "flex", flexDirection: "column", gap: 2 }}
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
        <PlaceAutocomplete
          id="origin"
          label="Origin"
          value={values.origin}
          onChange={(v) => update("origin", "origin", v)}
          error={errors.origin}
        />
        <PlaceAutocomplete
          id="destination"
          label="Destination"
          value={values.destination}
          onChange={(v) => update("destination", "destination", v)}
          error={errors.destination}
        />
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 1.5 }}>
        <TextField
          id="departure_at"
          label="Departure"
          type="datetime-local"
          size="small"
          value={values.departure}
          onChange={(e) => update("departure", "departure_at", e.target.value)}
          error={Boolean(errors.departure_at)}
          helperText={errors.departure_at}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <TextField
          id="load_weight_lb"
          label="Load (lb)"
          type="number"
          size="small"
          value={values.weight}
          onChange={(e) => update("weight", "load_weight_lb", e.target.value)}
          error={Boolean(errors.load_weight_lb)}
          helperText={errors.load_weight_lb}
          slotProps={{ htmlInput: { min: 1, step: 1 } }}
        />
      </Box>

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={loading}
        sx={{
          py: 1.5,
        }}
      >
        {loading ? "Checking routes…" : "Find safest route"}
      </Button>
    </Box>
  );
}
