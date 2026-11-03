import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import type { Interval } from "@/types";

const INTERVALS: Interval[] = ["10", "25", "50"];

interface Props {
  value: Interval;
  onChange: (interval: Interval) => void;
}

export default function IntervalToggle({ value, onChange }: Props) {
  return (
    <Stack direction="column">
      <Typography
        variant="overline"
        color="text.secondary"
        sx={{ fontWeight: 700 }}
      >
        Checkpoint every
      </Typography>
      <ToggleButtonGroup
        exclusive
        fullWidth
        size="small"
        color="primary"
        value={value}
        onChange={(_, next: Interval | null) => next && onChange(next)}
        aria-label="Checkpoint interval"
      >
        {INTERVALS.map((n) => (
          <ToggleButton key={n} value={n} sx={{ fontWeight: 700 }}>
            {n} mi
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </Stack>
  );
}
