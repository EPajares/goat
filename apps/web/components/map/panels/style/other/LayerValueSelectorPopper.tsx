import ClearIcon from "@mui/icons-material/Clear";
import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Checkbox,
  Chip,
  Divider,
  Fade,
  IconButton,
  InputAdornment,
  List,
  ListItemButton,
  ListItemIcon,
  Popper,
  Stack,
  TextField,
  debounce,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Loading } from "@p4b/ui/components/Loading";

import { useLayerUniqueValues } from "@/lib/api/layers";
import type { GetLayerUniqueValuesQueryParams } from "@/lib/validations/layer";

import { OverflowTypograpy } from "@/components/common/OverflowTypography";
import NoValuesFound from "@/components/map/common/NoValuesFound";
import DropdownFooter from "@/components/map/panels/style/other/DropdownFooter";

export function LayerValueSelectorPopper(props: {
  open: boolean;
  layerId: string;
  fieldName: string;
  selectedValues: string[] | null;
  onSelectedValuesChange: (values: string[] | null) => void;
  anchorEl: HTMLElement | null;
  onDone?: () => void;
}) {
  const { t } = useTranslation("common");
  const [searchText, setSearchText] = useState("");
  const [queryParams, setQueryParams] = useState<GetLayerUniqueValuesQueryParams>({
    size: 50,
    page: 1,
    order: "descendent",
  });

  const _selectedValues = useMemo(() => props.selectedValues || [], [props.selectedValues]);

  const { data, isLoading } = useLayerUniqueValues(props.layerId, props.fieldName, queryParams);

  const debouncedSetSearchText = debounce((value) => {
    const query = {
      op: "like",
      args: [
        {
          property: props.fieldName,
        },
        `%${value}%`,
      ],
    };
    if (value !== "") {
      setQueryParams((params) => ({ ...params, query: JSON.stringify(query) }));
    } else {
      setQueryParams((params) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { query, ...rest } = params;
        return rest;
      });
    }
  }, 300);

  const handleClearText = () => {
    setSearchText("");
    setQueryParams((params) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { query, ...rest } = params;
      return rest;
    });
  };

  const handleDelete = (value) => {
    const filtered = _selectedValues.filter((v) => v !== value);
    props.onSelectedValuesChange(filtered?.length > 0 ? filtered : null);
  };

  const handleClick = (item) => {
    const newValues = _selectedValues.includes(item.value)
      ? _selectedValues.filter((value) => value !== item.value)
      : [..._selectedValues, item.value];
    props.onSelectedValuesChange(newValues?.length > 0 ? newValues : null);
  };

  const handleClear = () => {
    props.onSelectedValuesChange(null);
  };

  const handleDone = () => {
    props.onDone && props.onDone();
  };

  return (
    <Popper
      open={!!open}
      anchorEl={props.anchorEl}
      transition
      sx={{ zIndex: 2000, maxWidth: "250px" }}
      placement="left"
      modifiers={[
        {
          name: "offset",
          options: {
            offset: [0, 115],
          },
        },
      ]}>
      {({ TransitionProps }) => (
        <Fade {...TransitionProps}>
          <Box sx={{ bgcolor: "background.paper", borderRadius: 1 }}>
            <Box
              sx={{
                maxHeight: "180px",
                overflowY: "auto",
                overflowX: "hidden",
                p: 2,
              }}>
              {_selectedValues.map((value) => {
                return (
                  <Chip
                    sx={{ my: 1, mr: 1 }}
                    key={value}
                    label={value}
                    onDelete={() => handleDelete(value)}
                  />
                );
              })}
            </Box>
            {_selectedValues.length > 0 && <Divider />}

            <TextField
              sx={{ p: 2 }}
              size="small"
              autoFocus
              placeholder={t("search")}
              value={searchText}
              InputProps={{
                sx: { pr: 1 },
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    {searchText && (
                      <IconButton size="small" onClick={handleClearText}>
                        <ClearIcon />
                      </IconButton>
                    )}
                  </InputAdornment>
                ),
              }}
              onChange={(e) => {
                setSearchText(e.target.value);
                debouncedSetSearchText(e.target.value);
              }}
              onKeyDown={(e) => {
                if (e.key !== "Escape") {
                  e.stopPropagation();
                }
              }}
            />
            <Box sx={{ maxHeight: "280px", overflowY: "auto" }}>
              <List dense={true} disablePadding>
                {data?.items?.map((item, index) => (
                  <ListItemButton key={index} onClick={() => handleClick(item)}>
                    <ListItemIcon sx={{ minWidth: "30px" }}>
                      <Checkbox
                        edge="start"
                        checked={_selectedValues.includes(item.value)}
                        tabIndex={-1}
                        disableRipple
                        sx={{ mr: 0 }}
                        inputProps={{
                          "aria-labelledby": `checkbox-list-label-${item}`,
                        }}
                      />
                    </ListItemIcon>

                    <OverflowTypograpy
                      variant="body2"
                      fontWeight={_selectedValues.includes(item.value) ? "bold" : "normal"}
                      tooltipProps={{
                        placement: "top",
                        arrow: true,
                        enterDelay: 700,
                      }}>
                      {item.value}
                    </OverflowTypograpy>
                  </ListItemButton>
                ))}
              </List>
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
              {!isLoading && data?.items?.length === 0 && <NoValuesFound />}
            </Box>
            <Divider />
            <Stack sx={{ pb: 3, pt: 1 }}>
              <DropdownFooter
                isValid={true}
                onCancel={handleClear}
                onApply={handleDone}
                cancelLabel={t("clear_all")}
                applyLabel={t("done")}
              />
            </Stack>
          </Box>
        </Fade>
      )}
    </Popper>
  );
}
