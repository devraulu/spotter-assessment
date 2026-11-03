import Box from "@mui/material/Box";
import Slider from "@mui/material/Slider";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Typography from "@mui/material/Typography";
import { formatLocal } from "@/time";

interface Props {
  start: string;
  hours: number;
  hour: number;
  onHourChange: (hour: number) => void;
  show: boolean;
  onShowChange: (show: boolean) => void;
}

const LABELED = [0, 24, 48];

export default function HeatmapSlider({
  start,
  hours,
  hour,
  onHourChange,
  show,
  onShowChange,
}: Props) {
  const at = (h: number) =>
    formatLocal(
      new Date(new Date(start).getTime() + h * 3600_000).toISOString(),
    );
  const marks = Array.from({ length: hours }, (_, h) => ({
    value: h,
    label: LABELED.includes(h) ? (h === 0 ? "0 h" : `+${h} h`) : undefined,
  }));

  return (
    <Box
      sx={{
        border: 1,
        borderColor: "divider",
        borderRadius: 3,
        px: 2,
        py: 1.5,
      }}
    >
      <Stack
        direction="row"
        sx={{ alignItems: "center", justifyContent: "space-between" }}
      >
        <div>
          <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>
            Heatmap
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {show
              ? `${at(hour)} · +${hour} h after departure`
              : "Risk along every route over the next 48 hours"}
          </Typography>
        </div>
        <Switch
          checked={show}
          onChange={(e) => onShowChange(e.target.checked)}
          slotProps={{ input: { "aria-label": "Show heatmap" } }}
        />
      </Stack>

      {show && (
        <Slider
          value={hour}
          min={0}
          max={hours - 1}
          step={1}
          marks={marks}
          onChange={(_, v) => onHourChange(v as number)}
          valueLabelDisplay="auto"
          valueLabelFormat={at}
          aria-label="Hours after departure"
          getAriaValueText={at}
          sx={{
            mt: 1,
            mx: 1,
            width: "calc(100% - 16px)",
            // '& .MuiSlider-markLabel[data-index="0"]': { transform: "none" },
            // [`& .MuiSlider-markLabel[data-index="${hours - 1}"]`]: {
            //   transform: "translateX(-100%)",
            // },
          }}
        />
      )}
    </Box>
  );
}
