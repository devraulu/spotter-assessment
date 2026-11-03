import { useState } from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { usePlaceSuggestions } from "@/api";
import { useDebouncedValue } from "@/hooks";

interface Props {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

const DEBOUNCE_MS = 300;

const shortLabel = (label: string) => label.replace(/, United States$/, "");

export default function PlaceAutocomplete({
  id,
  label,
  value,
  onChange,
  error,
}: Props) {
  const [typed, setTyped] = useState("");
  const query = useDebouncedValue(typed, DEBOUNCE_MS);
  const { data = [], isFetching } = usePlaceSuggestions(query);
  const options = [...new Set(data.map((s) => shortLabel(s.label)))];

  return (
    <Autocomplete
      id={id}
      freeSolo
      options={options}
      filterOptions={(o) => o}
      inputValue={value}
      onInputChange={(_, next, reason) => {
        onChange(next);
        if (reason === "input") setTyped(next);
      }}
      loading={isFetching}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          error={Boolean(error)}
          helperText={error}
        />
      )}
    />
  );
}
