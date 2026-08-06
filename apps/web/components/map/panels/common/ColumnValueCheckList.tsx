import SearchIcon from "@mui/icons-material/Search";
import { Box, Checkbox, Divider, InputAdornment, MenuItem, TextField, Typography } from "@mui/material";
import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { Loading } from "@p4b/ui/components/Loading";

import { BLANK_VALUE } from "@/lib/utils/columnFilterOperators";

import { useDatasetValueSelectorMethods } from "@/hooks/map/DatasetHooks";

import NoValuesFound from "@/components/map/common/NoValuesFound";

/** Page size of the unique-values endpoint — surfaced so the list can say so. */
const VALUE_PAGE_SIZE = 100;

type ColumnValueCheckListProps = {
  layerId: string;
  fieldName: string;
  selectedValues: string[];
  onToggle: (value: string) => void;
  /**
   * Every OTHER active filter, so the list agrees with the table without
   * hiding the values already picked for this column.
   */
  cqlFilter?: object;
};

const ColumnValueCheckList: React.FC<ColumnValueCheckListProps> = ({
  layerId,
  fieldName,
  selectedValues,
  onToggle,
  cqlFilter,
}) => {
  const { t } = useTranslation("common");
  const { data, isLoading, searchText, setSearchText, debouncedSetSearchText } =
    useDatasetValueSelectorMethods({
      selectedValues,
      onSelectedValuesChange: () => undefined,
      fieldName,
      datasetId: layerId,
      cqlFilter,
    });

  const items = useMemo(() => {
    const mapped = (data?.items ?? []).map((item) => ({
      value:
        item.value === null || item.value === undefined || item.value === "" ? BLANK_VALUE : item.value,
      count: item.count,
    }));
    // Ticked values pin to the top so a long list never hides your own choice.
    const selected = new Set(selectedValues);
    return [...mapped.filter((i) => selected.has(i.value)), ...mapped.filter((i) => !selected.has(i.value))];
  }, [data?.items, selectedValues]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <Box sx={{ px: 2, py: 2, flexShrink: 0 }}>
        <TextField
          size="small"
          fullWidth
          autoFocus
          placeholder={t("search")}
          value={searchText}
          onChange={(event) => {
            setSearchText(event.target.value);
            debouncedSetSearchText(event.target.value);
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Separates the search from the values it filters. */}
      <Divider sx={{ flexShrink: 0 }} />

      <Box sx={{ flex: 1, minHeight: 80, overflowY: "auto", py: 1 }}>
        {isLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 4 }}>
            <Loading size={40} />
          </Box>
        )}
        {!isLoading && items.length === 0 && <NoValuesFound />}
        {!isLoading &&
          items.map((item) => {
            const checked = selectedValues.includes(item.value);
            return (
              <MenuItem key={item.value} sx={{ px: 2, py: 2 }} onClick={() => onToggle(item.value)}>
                <Checkbox sx={{ mr: 2, p: 0 }} size="small" checked={checked} tabIndex={-1} disableRipple />
                <Typography
                  variant="body2"
                  fontWeight="bold"
                  sx={{
                    flex: 1,
                    minWidth: 0,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    ...(item.value === BLANK_VALUE && { fontStyle: "italic" }),
                  }}>
                  {item.value === BLANK_VALUE ? t("empty_value", { defaultValue: "(empty)" }) : item.value}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                  {item.count.toLocaleString()}
                </Typography>
              </MenuItem>
            );
          })}
      </Box>

      {!isLoading && items.length >= VALUE_PAGE_SIZE && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: "block", px: 2, py: 2, flexShrink: 0 }}>
          {t("showing_most_frequent_values", {
            count: VALUE_PAGE_SIZE,
            defaultValue: "Showing the {{count}} most frequent values. Search to find others.",
          })}
        </Typography>
      )}
    </Box>
  );
};

export default ColumnValueCheckList;
