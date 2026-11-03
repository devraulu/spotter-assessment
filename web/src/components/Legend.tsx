import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { LEVEL_COLORS, LEVEL_LABELS } from "@/levels";
import type { CheckpointLevel } from "@/types";

const ORDER: CheckpointLevel[] = ["LOW", "MODERATE", "HIGH", "SEVERE", "NO_TRAVEL", "UNKNOWN"];

export function LevelDot({ level, size = 12 }: { level: CheckpointLevel; size?: number }) {
  return (
    <Box
      component="span"
      sx={{ display: "inline-block", width: size, height: size, borderRadius: "50%", flexShrink: 0, bgcolor: LEVEL_COLORS[level] }}
    />
  );
}

export default function Legend() {
  return (
    <Paper elevation={8} sx={{ position: "absolute", right: 16, bottom: 16, zIndex: 1000, px: 2, py: 1.5 }}>
      <Typography variant="caption" sx={{ fontWeight: 700, display: "block", mb: 0.5 }}>
        Risk level
      </Typography>
      {ORDER.map((level) => (
        <Box key={level} sx={{ display: "flex", alignItems: "center", gap: 1, py: 0.25 }}>
          <LevelDot level={level} />
          <Typography variant="caption">{LEVEL_LABELS[level]}</Typography>
        </Box>
      ))}
    </Paper>
  );
}
