import SearchIcon from "@mui/icons-material/Search";
import {
  Checkbox,
  FormControl,
  InputAdornment,
  ListSubheader,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useMemo, useState } from "react";

import { type ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { SelectorItem } from "@/types/map/common";

import FormLabelHelper from "@/components/common/FormLabelHelper";

type SelectorProps = {
  selectedItems: SelectorItem[] | SelectorItem | undefined;
  setSelectedItems: (items: SelectorItem[] | SelectorItem | undefined) => void;
  items: SelectorItem[];
  multiple?: boolean;
  tooltip?: string;
  placeholder?: string;
  enableSearch?: boolean;
  label?: string;
  allSelectedLabel?: string;
  errorMessage?: string;
  emptyMessage?: string;
  emptyMessageIcon?: ICON_NAME;
  disabled?: boolean;
};

const containsText = (text: string, searchText: string) =>
  text.toLowerCase().indexOf(searchText.toLowerCase()) > -1;

const Selector = (props: SelectorProps) => {
  const theme = useTheme();
  const [searchText, setSearchText] = useState("");
  const {
    selectedItems,
    items,
    setSelectedItems,
    enableSearch,
    placeholder,
    label,
    tooltip,
    multiple,
    allSelectedLabel,
    emptyMessage,
    emptyMessageIcon,
    errorMessage,
    disabled,
  } = props;
  const [focused, setFocused] = useState(false);
  const displayedItems = useMemo(() => {
    if (!enableSearch) return items;
    const filtered = items.filter((item) => {
      return containsText(item.label, searchText);
    });
    return filtered;
  }, [enableSearch, items, searchText]);

  const selectedValue = useMemo(() => {
    if (!multiple && !Array.isArray(selectedItems)) {
      return selectedItems ? selectedItems.value : "";
    } else {
      return selectedItems && Array.isArray(selectedItems) ? selectedItems?.map((item) => item.value) : [];
    }
  }, [multiple, selectedItems]);

  return (
    <FormControl size="small" fullWidth>
      {label && (
        <FormLabelHelper
          label={label}
          color={
            disabled
              ? theme.palette.secondary.main
              : focused
                ? theme.palette.primary.main
                : theme.palette.text.secondary
          }
          tooltip={tooltip}
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
        IconComponent={() => null}
        sx={{ pr: 1 }}
        displayEmpty
        disabled={disabled}
        error={!!errorMessage}
        multiple={multiple}
        defaultValue={multiple ? [] : ("" as unknown)} //todo: fix this
        value={selectedValue || (multiple ? [] : "")}
        onChange={(e) => {
          if (multiple) {
            const value = e.target.value as string[] | number[];
            setSelectedItems(items.filter((item) => value.includes(item.value as never)));
          }
          if (!multiple) {
            const value = e.target.value as string | number;
            const selected = items.find((item) => item.value === value);
            setSelectedItems(selected);
          }
        }}
        onClose={() => {
          setFocused(false);
          setSearchText("");
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        renderValue={() => {
          // {PLACEHOLDER RENDER}
          if (!selectedItems || (Array.isArray(selectedItems) && selectedItems?.length === 0))
            return <Typography variant="body2">{placeholder}</Typography>;

          // {SINGLE ITEM RENDER}
          if (!multiple && !Array.isArray(selectedItems) && selectedItems)
            return (
              <div style={{ display: "flex", alignItems: "center" }}>
                {selectedItems.icon && (
                  <Icon
                    iconName={selectedItems.icon}
                    style={{
                      fontSize: "14px",
                      color: theme.palette.text.secondary,
                    }}
                    sx={{ mr: 2 }}
                    color="inherit"
                  />
                )}
                <Typography variant="body2" fontWeight="bold">
                  {selectedItems.label}
                </Typography>
              </div>
            );
          return (
            <Typography
              variant="body2"
              fontWeight="bold"
              style={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}>
              {Array.isArray(selectedItems) &&
              selectedItems.length === displayedItems.length &&
              allSelectedLabel
                ? allSelectedLabel
                : Array.isArray(selectedItems)
                  ? selectedItems.map((item) => item.label).join(", ")
                  : selectedItems.label}
            </Typography>
          );
        }}>
        {enableSearch && (
          <ListSubheader sx={{ px: 2, pt: 1 }}>
            <TextField
              size="small"
              autoFocus
              placeholder="Search"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key !== "Escape") {
                  e.stopPropagation();
                }
              }}
            />
          </ListSubheader>
        )}
        {emptyMessage && emptyMessageIcon && displayedItems.length === 0 && (
          <Stack
            direction="column"
            spacing={2}
            sx={{
              my: 2,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}>
            {emptyMessageIcon && (
              <Icon iconName={emptyMessageIcon} fontSize="small" htmlColor={theme.palette.text.secondary} />
            )}
            {emptyMessage && (
              <Typography variant="body2" fontWeight="bold" color={theme.palette.text.secondary}>
                {emptyMessage}
              </Typography>
            )}
          </Stack>
        )}

        {displayedItems.map((item) => (
          <MenuItem sx={{ px: 2, py: 2 }} key={item.value} value={item.value}>
            {multiple && Array.isArray(selectedValue) && (
              <Checkbox
                sx={{ mr: 2, p: 0 }}
                size="small"
                checked={selectedValue?.findIndex((selected) => selected === item.value) > -1}
              />
            )}
            {item.icon && (
              <Icon
                iconName={item.icon}
                style={{
                  fontSize: "14px",
                  color: theme.palette.text.secondary,
                }}
                sx={{ mr: 2 }}
                color="inherit"
              />
            )}
            <Typography
              variant="body2"
              fontWeight="bold"
              style={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}>
              {item.label}
            </Typography>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default Selector;
