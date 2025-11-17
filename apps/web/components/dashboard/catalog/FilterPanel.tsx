import ClearIcon from "@mui/icons-material/Clear";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SearchIcon from "@mui/icons-material/Search";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Checkbox,
  Chip,
  Divider,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import type { ICON_NAME } from "@p4b/ui/components/Icon";
import { Icon } from "@p4b/ui/components/Icon";
import { Loading } from "@p4b/ui/components/Loading";

import { type DatasetMetadataValue } from "@/lib/validations/layer";

import NoValuesFound from "@/components/map/common/NoValuesFound";

interface FilterPanelProps {
  filterType: string;
  filterValues: string[] | null;
  icon?: ICON_NAME;
  values: DatasetMetadataValue[];
  isLoading: boolean;
  onToggle?: (value: string) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filterType,
  filterValues,
  values,
  isLoading,
  icon,
  onToggle,
}) => {
  const { t, i18n } = useTranslation(["common", "countries", "languages"]);
  const theme = useTheme();
  const [searchText, setSearchText] = useState("");
  const handleClearText = () => {
    setSearchText("");
  };

  const filteredValues = useMemo(() => {
    return values.filter((value) => {
      return value.value.toLowerCase().includes(searchText.toLowerCase());
    });
  }, [values, searchText]);

  const getItemLabel = (filterType: string, item: { value: string }) => {
    let key = `common:metadata.${filterType}.${item.value}`;
    if (filterType === "language_code") {
      key = `languages:${item.value}`;
    } else if (filterType === "geographical_code") {
      key = `countries:${item.value}`;
    }
    return i18n.exists(key) ? t(key) : item.value;
  };

  return (
    <Accordion elevation={0} disableGutters defaultExpanded>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls={`${filterType}-panel-content`}
        id={`${filterType}-panel-header`}>
        <Stack direction="row" sx={{ py: 0, pl: 1 }} alignItems="center" spacing={4}>
          {icon && (
            <Icon sx={{ ml: 2 }} iconName={icon} fontSize="small" htmlColor={theme.palette.text.secondary} />
          )}
          <Typography variant="body1">
            {i18n.exists(`common:metadata.headings.${filterType}`)
              ? t(`common:metadata.headings.${filterType}`)
              : filterType}
          </Typography>
        </Stack>
      </AccordionSummary>
      <Divider sx={{ my: 0, py: 0 }} />
      <AccordionDetails sx={{ p: 0 }}>
        {!isLoading && values.length > 10 && (
          <TextField
            id={`${filterType}-search`}
            sx={{ p: 2 }}
            size="small"
            autoFocus
            fullWidth
            disabled={isLoading}
            placeholder={t("common:search")}
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
            }}
            onKeyDown={(e) => {
              if (e.key !== "Escape") {
                e.stopPropagation();
              }
            }}
          />
        )}
        <Box
          sx={{
            maxHeight: "240px",
            overflowY: "auto",
            overflowX: "hidden",
            py: 2,
          }}>
          {filteredValues.length > 0 && (
            <List sx={{ py: 0 }}>
              {filteredValues.map((item) => {
                const labelId = `checkbox-list-label-${item.value}`;
                return (
                  <ListItem key={item.value} disablePadding>
                    <ListItemButton
                      role={undefined}
                      onClick={() => {
                        onToggle && onToggle(item.value);
                      }}
                      selected={!!filterValues && filterValues.includes(item.value)}
                      dense>
                      <Stack direction="row" alignItems="center" justifyContent="space-between" width="100%">
                        <Stack direction="row" alignItems="center" sx={{ pl: 3 }}>
                          <ListItemIcon
                            sx={{
                              minWidth: 35,
                              color: "inherit",
                            }}>
                            <Checkbox
                              edge="start"
                              size="small"
                              checked={!!filterValues && filterValues.includes(item.value)}
                              tabIndex={-1}
                              disableRipple
                              inputProps={{ "aria-labelledby": labelId }}
                            />
                          </ListItemIcon>
                          <ListItemText
                            sx={{
                              wordWrap: "break-word",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                            id={labelId}
                            primary={
                              <Typography
                                variant="body2"
                                fontWeight={
                                  !!filterValues && filterValues.includes(item.value) ? "bold" : "regular"
                                }>
                                {getItemLabel(filterType, item)}
                              </Typography>
                            }
                          />
                        </Stack>
                        <Chip
                          sx={{
                            ml: 2,
                            backgroundColor:
                              !!filterValues && filterValues.includes(item.value)
                                ? theme.palette.primary.main
                                : theme.palette.text.secondary,
                            color: theme.palette.background.paper,
                            fontWeight: "bold",
                          }}
                          label={item.count}
                          size="small"
                          color="secondary"
                        />
                      </Stack>
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          )}
          {isLoading && (
            <Box
              sx={{
                minHeight: "80px",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}>
              <Loading size={40} />
            </Box>
          )}
          {!isLoading && filteredValues && filteredValues.length === 0 && (
            <Box sx={{ py: 6 }}>
              <NoValuesFound text={t("common:no_options_for_this_filter")} />
            </Box>
          )}
        </Box>
      </AccordionDetails>
    </Accordion>
  );
};

export default FilterPanel;
