import { segmentLevel } from "@/levels";
import type { Checkpoint, CheckpointLevel } from "@/types";

export interface Segment {
  fromMile: number;
  toMile: number;
  level: CheckpointLevel;
  positions: [number, number][]; // [lat, lon]
}

const EARTH_RADIUS_MI = 3958.8;
const rad = (deg: number) => (deg * Math.PI) / 180;

function haversineMi([lon1, lat1]: [number, number], [lon2, lat2]: [number, number]): number {
  const h =
    Math.sin(rad(lat2 - lat1) / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(rad(lon2 - lon1) / 2) ** 2;
  return 2 * EARTH_RADIUS_MI * Math.asin(Math.sqrt(h));
}

export function routeSegments(coords: [number, number][], distanceMi: number, checkpoints: Checkpoint[]): Segment[] {
  const cum = [0];
  for (let i = 1; i < coords.length; i++) cum.push(cum[i - 1] + haversineMi(coords[i - 1], coords[i]));
  const scale = distanceMi ? cum[cum.length - 1] / distanceMi : 0;

  const after: number[] = [];
  let j = 0;
  for (const cp of checkpoints) {
    while (j < cum.length && cum[j] <= cp.mile * scale) j++;
    after.push(j);
  }

  const segments: Segment[] = [];
  for (let i = 0; i < checkpoints.length - 1; i++) {
    const a = checkpoints[i];
    const b = checkpoints[i + 1];
    const inner = coords.slice(after[i], after[i + 1]).map(([lon, lat]) => [lat, lon] as [number, number]);
    segments.push({
      fromMile: a.mile,
      toMile: b.mile,
      level: segmentLevel(a.level, b.level),
      positions: [[a.lat, a.lon], ...inner, [b.lat, b.lon]],
    });
  }
  return segments;
}
