export interface TripFormValues {
  origin: string;
  destination: string;
  departure: string;
  weight: string;
}

export type TripField = "origin" | "destination" | "departure_at" | "load_weight_lb";
export type FieldErrors = Partial<Record<TripField, string>>;

export function validateTrip(v: TripFormValues, now = new Date()): FieldErrors {
  const errors: FieldErrors = {};

  if (!v.origin.trim()) errors.origin = "Enter an origin.";
  if (!v.destination.trim()) errors.destination = "Enter a destination.";
  else if (v.origin.trim().toLowerCase() === v.destination.trim().toLowerCase())
    errors.destination = "Destination must be different from the origin.";

  const departure = new Date(v.departure);
  if (!v.departure || Number.isNaN(departure.getTime())) errors.departure_at = "Pick a departure date and time.";
  else if (departure.getTime() < now.getTime() - 3600_000)
    errors.departure_at = "Departure can't be more than 1 hour in the past.";

  const weight = Number(v.weight);
  if (!v.weight.trim() || !Number.isFinite(weight) || weight <= 0)
    errors.load_weight_lb = "Enter a load weight greater than 0 lb.";

  return errors;
}
