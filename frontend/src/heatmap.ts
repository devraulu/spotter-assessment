import { LEVELS } from "@/levels";
import type { Checkpoint, Heatmap } from "@/types";

const cell = (lat: number, lon: number) =>
  `${Math.round(lat * 10)},${Math.round(lon * 10)}`;

function nearest(points: [number, number][], lat: number, lon: number): number {
  let best = 0;
  let bestDist = Infinity;
  points.forEach(([pLat, pLon], i) => {
    const d = (pLat - lat) ** 2 + (pLon - lon) ** 2;
    if (d < bestDist) [best, bestDist] = [i, d];
  });
  return best;
}

export function heatmapRows(heatmap: Heatmap, checkpoints: Checkpoint[]): number[] {
  const byCell = new Map(
    heatmap.points.map(([lat, lon], i) => [cell(lat, lon), i]),
  );
  return checkpoints.map(
    (cp) =>
      byCell.get(cell(cp.lat, cp.lon)) ??
      nearest(heatmap.points, cp.lat, cp.lon),
  );
}

export function checkpointsAtHour(
  heatmap: Heatmap,
  checkpoints: Checkpoint[],
  rows: number[],
  hour: number,
): Checkpoint[] {
  return checkpoints.map((cp, i) => {
    const score = heatmap.risk[rows[i]][hour];
    return { ...cp, level: score === null ? "UNKNOWN" : LEVELS[score] };
  });
}
