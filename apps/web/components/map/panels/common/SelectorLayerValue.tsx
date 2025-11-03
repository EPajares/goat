import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Checkbox,
  Divider,
  FormControl,
  InputAdornment,
  ListSubheader,
  MenuItem,
  Select,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";

import { Loading } from "@p4b/ui/components/Loading";

import { useTranslation } from "@/i18n/client";

import { useDatasetValueSelectorMethods } from "@/hooks/map/DatasetHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import NoValuesFound from "@/components/map/common/NoValuesFound";

export type SelectorProps = {
  selectedValues: string[] | string | null;
  onSelectedValuesChange: (values: string[] | string | null) => void;
  layerId: string;
  fieldName: string;
  label?: string;
  tooltip?: string;
  disabled?: boolean;
  multiple?: boolean;
  placeholder?: string;
  onFocus?: () => void;
  onClose?: () => void;
  cqlFilter?: object | undefined;
  clearable?: boolean;
};

const SelectorLayerValue = (props: SelectorProps) => {
  const theme = useTheme();
  const [focused, setFocused] = useState(false);
  const { t } = useTranslation("common");
  const { data, isLoading, searchText, setSearchText, debouncedSetSearchText } =
    useDatasetValueSelectorMethods({
      selectedValues: props.multiple ? (props.selectedValues as string[]) : [props.selectedValues as string],
      onSelectedValuesChange: props.onSelectedValuesChange,
      fieldName: props.fieldName,
      datasetId: props.layerId,
      cqlFilter: props.cqlFilter,
    });

  // Prepare selected values array
  const selectedValuesArray = props.multiple
    ? ((props.selectedValues as string[]) || []).filter((v) => v != null)
    : props.selectedValues
      ? [props.selectedValues as string]
      : [];

  const selectedValuesSet = new Set(selectedValuesArray);

  // Create combined items list with selected values first
  const selectedItems = selectedValuesArray.map((selectedValue) => {
    const existingItem = data?.items?.find((item) => item.value === selectedValue);
    return existingItem || { value: selectedValue };
  });

  const otherItems = data?.items?.filter((item) => !selectedValuesSet.has(item.value)) || [];
  const itemsToDisplay = [...selectedItems, ...otherItems];

  return (
    <FormControl size="small" fullWidth>
      {props.label && (
        <FormLabelHelper
          label={props.label}
          color={
            props.disabled ? theme.palette.secondary.main : focused ? theme.palette.primary.main : "inherit"
          }
          tooltip={props.tooltip}
        />
      )}
      <Select
        fullWidth
        MenuProps={{
          autoFocus: false,
          sx: { width: "120px" },
          slotProps: {
            paper: {
              sx: {
                maxHeight: "350px",
                overflowY: "auto",
              },
            },
          },
        }}
        multiple={props.multiple ? true : false}
        disabled={props.disabled}
        IconComponent={() => null}
        sx={{ pr: 1 }}
        displayEmpty
        value={props.selectedValues as unknown}
        defaultValue={props.multiple ? [] : ""}
        onChange={(e) => {
          props.onSelectedValuesChange(e.target.value as string[] | string | null);
        }}
        onClose={() => {
          setFocused(false);
          if (props.onClose) {
            props.onClose();
          }
        }}
        onFocus={() => {
          setFocused(true);
          if (props.onFocus) {
            props.onFocus();
          }
        }}
        onBlur={() => setFocused(false)}
        renderValue={() => {
          if (!props.selectedValues && !props.multiple)
            return <Typography variant="body2">{props.placeholder ?? t("select_value")}</Typography>;
          if (props.multiple && Array.isArray(props.selectedValues) && props.selectedValues.length === 0)
            return <Typography variant="body2">{props.placeholder ?? t("select_values")}</Typography>;
          return (
            <>
              {props.selectedValues && (
                <Typography variant="body2" fontWeight="bold">
                  {props.multiple && Array.isArray(props.selectedValues)
                    ? props.selectedValues.filter((v) => !!v).join(", ")
                    : props.selectedValues}
                </Typography>
              )}
            </>
          );
        }}>
        <ListSubheader sx={{ px: 2, pt: 1 }}>
          <TextField
            size="small"
            autoFocus
            placeholder={t("search")}
            value={searchText}
            onChange={(e) => {
              setSearchText(e.target.value);
              debouncedSetSearchText(e.target.value);
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            onKeyDown={(e) => {
              if (e.key !== "Escape") {
                e.stopPropagation();
              }
            }}
          />
        </ListSubheader>
        {isLoading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}>
            <Loading size={40} />
          </Box>
        )}
        {!isLoading && itemsToDisplay.length === 0 && <NoValuesFound />}

        {props.clearable && [
          <MenuItem
            sx={{ px: 2 }}
            value={props.multiple ? [] : ""}
            onClick={() => props.onSelectedValuesChange(props.multiple ? [] : null)}
            key="__none__">
            {props.multiple && (
              <Checkbox sx={{ mr: 2, p: 0 }} size="small" checked={selectedValuesArray.length === 0} />
            )}
            <Typography variant="body2" fontWeight="bold">
              {t("none")}
            </Typography>
          </MenuItem>,
          <Divider sx={{ my: 1 }} key="__divider__" />,
        ]}

        {itemsToDisplay.map((item) => (
          <MenuItem sx={{ px: 2 }} key={item.value} value={item.value}>
            {props.multiple && (
              <Checkbox
                sx={{ mr: 2, p: 0 }}
                size="small"
                checked={selectedValuesArray.includes(item.value)}
              />
            )}
            <Typography variant="body2" fontWeight="bold">
              {item.value}
            </Typography>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default SelectorLayerValue;
