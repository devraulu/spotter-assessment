import type { CheckpointLevel, Level } from "@/types";

export const LEVELS: Level[] = ["LOW", "MODERATE", "HIGH", "SEVERE", "NO_TRAVEL"];

export const LEVEL_COLORS: Record<CheckpointLevel, string> = {
  LOW: "#16a34a",
  MODERATE: "#eab308",
  HIGH: "#f97316",
  SEVERE: "#dc2626",
  NO_TRAVEL: "#581c87",
  UNKNOWN: "#9ca3af",
};

export const LEVEL_LABELS: Record<CheckpointLevel, string> = {
  LOW: "Low",
  MODERATE: "Moderate",
  HIGH: "High",
  SEVERE: "Severe",
  NO_TRAVEL: "No Travel",
  UNKNOWN: "Unknown",
};

export function segmentLevel(a: CheckpointLevel, b: CheckpointLevel): CheckpointLevel {
  const known = [a, b].filter((l): l is Level => l !== "UNKNOWN");
  if (known.length === 0) return "UNKNOWN";
  return known.reduce((max, l) => (LEVELS.indexOf(l) > LEVELS.indexOf(max) ? l : max));
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  return `${h} h ${m} m`;
}
