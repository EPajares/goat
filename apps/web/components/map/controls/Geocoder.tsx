/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  Autocomplete,
  Divider,
  Fab,
  IconButton,
  InputBase,
  ListItemButton,
  ListItemText,
  Paper,
  Popper,
  Tooltip,
  Typography,
  debounce,
  useTheme,
} from "@mui/material";
import type { FeatureCollection } from "geojson";
import { useEffect, useMemo, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import search from "@/lib/services/geocoder";
import { match } from "@/lib/utils/match";

import type { Result } from "@/types/map/controllers";

interface Match {
  0: number;
  1: number;
}

interface TextResult {
  text: string;
  highlight: boolean;
}

function parse(text: string, matches: Match[]): TextResult[] {
  const result: TextResult[] = [];

  if (matches.length === 0) {
    result.push({
      text,
      highlight: false,
    });
  } else if (matches[0][0] > 0) {
    result.push({
      text: text.slice(0, matches[0][0]),
      highlight: false,
    });
  }

  matches.forEach((match, i) => {
    const startIndex = match[0];
    const endIndex = match[1];

    result.push({
      text: text.slice(startIndex, endIndex),
      highlight: true,
    });

    if (i === matches.length - 1) {
      if (endIndex < text.length) {
        result.push({
          text: text.slice(endIndex, text.length),
          highlight: false,
        });
      }
    } else if (endIndex < matches[i + 1][0]) {
      result.push({
        text: text.slice(endIndex, matches[i + 1][0]),
        highlight: false,
      });
    }
  });

  return result;
}

type Props = {
  endpoint?: string;
  source?: string;
  accessToken: string;
  proximity?: { longitude: number; latitude: number };
  country?: string;
  bbox?: number[];
  types?: string;
  limit?: number;
  autocomplete?: boolean;
  language?: string;
  pointZoom?: number;
  placeholder?: string;
  tooltip?: string;
  onSelect?: (feature: Result | null) => void;
};

const COORDINATE_REGEX_STRING =
  "^[-+]?([1-8]?\\d(\\.\\d+)?|90(\\.0+)?),\\s*[-+]?(180(\\.0+)?|((1[0-7]\\d)|([1-9]?\\d))(\\.\\d+)?)";
const COORDINATE_REGEX = RegExp(COORDINATE_REGEX_STRING);
export const testForCoordinates = (query: string): [true, number, number] | [false, string] => {
  const isValid = COORDINATE_REGEX.test(query.trim());

  if (!isValid) {
    return [isValid, query];
  }

  const tokens = query.trim().split(",");

  return [isValid, Number(tokens[0]), Number(tokens[1])];
};

export default function Geocoder({
  endpoint = "https://api.mapbox.com",
  source = "mapbox.places",
  pointZoom = 15,
  accessToken,
  proximity,
  country,
  bbox,
  types,
  limit,
  autocomplete,
  language,
  placeholder,
  tooltip,
  onSelect,
}: Props) {
  const [value, setValue] = useState<Result | null>(null);
  const [options, setOptions] = useState<readonly Result[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [focused, setFocused] = useState(false);
  const [collapsed, setCollapsed] = useState(true);
  const { map } = useMap();
  const theme = useTheme();
  useEffect(() => {
    // Clear selection on unmount
    return () => {
      onSelect?.(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const fetch = useMemo(
    () =>
      debounce((request: { value: string }, onresult: (_error: Error, fc: FeatureCollection) => void) => {
        const mapCenter = map?.getCenter();
        let _proximity = proximity;
        if (mapCenter && !proximity) {
          _proximity = {
            longitude: mapCenter.lng,
            latitude: mapCenter.lat,
          };
        }
        search(
          endpoint,
          source,
          accessToken,
          request.value,
          onresult,
          _proximity,
          country,
          bbox,
          types,
          limit,
          autocomplete,
          language
        );
      }, 400),
    [accessToken, autocomplete, bbox, country, endpoint, language, limit, map, proximity, source, types]
  );

  useEffect(() => {
    let active = true;
    if (inputValue === "") {
      setOptions(value ? [value] : []);
      return undefined;
    }
    const resultCoordinates = testForCoordinates(inputValue);
    if (resultCoordinates[0]) {
      const [_, latitude, longitude] = resultCoordinates;
      setOptions([
        {
          feature: {
            id: "",
            type: "Feature",
            place_type: ["coordinate"],
            relevance: 1,
            properties: {
              accuracy: "point",
            },
            text: "",
            place_name: "",
            center: [longitude, latitude],
            geometry: {
              type: "Point",
              coordinates: [longitude, latitude],
              interpolated: false,
            },
            address: "",
            context: [],
          },
          label: `${latitude}, ${longitude}`,
        },
      ]);
      return undefined;
    }
    fetch({ value: inputValue }, (error: Error, fc: FeatureCollection) => {
      if (active) {
        if (!error && fc && fc.features) {
          setOptions(
            fc.features
              .map((feature) => ({
                feature: feature,
                label: feature.place_name,
              }))
              .filter((feature) => feature.label)
          );
        }
      }
    });

    return () => {
      active = false;
    };
  }, [value, inputValue, fetch]);
  return (
    <>
      {map && (
        <>
          {collapsed && (
            <Tooltip title={tooltip || "Search"} arrow placement="right">
              <Fab
                onClick={() => {
                  setCollapsed(false);
                  setFocused(false);
                }}
                size="small"
                sx={{
                  backgroundColor: theme.palette.background.paper,
                  color: theme.palette.text.secondary,
                  "&:hover": {
                    backgroundColor: theme.palette.background.default,
                  },
                  pointerEvents: "all",
                }}>
                <Icon iconName={ICON_NAME.SEARCH} htmlColor="inherit" fontSize="small" />
              </Fab>
            </Tooltip>
          )}
          {!collapsed && (
            <Autocomplete
              sx={{
                alignItems: "flex-start",
                marginTop: theme.spacing(1),
                marginBottom: theme.spacing(1),
                pointerEvents: "all",
              }}
              id="geocoder"
              freeSolo
              filterOptions={(x) => x}
              options={options}
              autoComplete
              includeInputInList
              filterSelectedOptions
              value={value}
              inputValue={inputValue}
              PopperComponent={({ style, ...props }) => (
                <Popper
                  {...props}
                  modifiers={[
                    {
                      name: "flip",
                      options: {
                        fallbackPlacements: [],
                      },
                    },
                    {
                      name: "offset",
                      options: {
                        offset: [0, 15],
                      },
                    },
                  ]}
                  sx={{
                    boxShadow: 2,
                    pointerEvents: "all",
                  }}
                  style={{ ...style, width: 350 }}
                />
              )}
              // ListboxProps={{ className: classes.listBox }}
              clearIcon={null}
              onChange={(_event: any, newValue: Result | null) => {
                setOptions(newValue ? [newValue, ...options] : options);
                setValue(newValue);
                if (newValue?.feature?.center) {
                  if (newValue.feature?.bbox) {
                    map.fitBounds(newValue.feature.bbox, { padding: 40, maxZoom: pointZoom, duration: 1000 });
                  } else {
                    map.flyTo({
                      center: newValue.feature.center,
                      zoom: pointZoom,
                    });
                  }
                  onSelect?.(newValue);
                }
              }}
              onInputChange={(_event, newInputValue) => {
                setInputValue(newInputValue);
              }}
              renderInput={(params) => {
                const { InputLabelProps: _, InputProps: __, ...rest } = params;
                return (
                  <Paper
                    elevation={2}
                    sx={{
                      padding: theme.spacing(0.5),
                      display: "flex",
                      alignItems: "center",
                      width: 350,
                      [theme.breakpoints.down("sm")]: {
                        width: 270,
                      },
                    }}>
                    <Icon
                      iconName={ICON_NAME.SEARCH}
                      fontSize="small"
                      sx={{
                        color: focused ? theme.palette.primary.main : theme.palette.text.secondary,
                        margin: theme.spacing(2),
                      }}
                    />
                    <Divider sx={{ height: 28, margin: theme.spacing(0.5) }} orientation="vertical" />
                    <InputBase
                      {...params.InputProps}
                      {...rest}
                      sx={{
                        marginLeft: theme.spacing(1),
                        flex: 1,
                        padding: 0,
                      }}
                      placeholder={placeholder || "Enter an address or coordinates"}
                      onBlur={() => {
                        setFocused(false);
                      }}
                      onFocus={() => {
                        setFocused(true);
                      }}
                      fullWidth
                    />
                    {inputValue && (
                      <IconButton
                        type="button"
                        sx={{
                          padding: theme.spacing(1),
                        }}
                        onClick={() => {
                          setInputValue("");
                          setValue(null);
                          setOptions([]);
                          onSelect?.(null);
                        }}>
                        <Icon
                          iconName={ICON_NAME.CLOSE}
                          fontSize="small"
                          sx={{
                            color: focused ? theme.palette.primary.main : theme.palette.text.secondary,
                            margin: theme.spacing(2),
                          }}
                        />
                      </IconButton>
                    )}
                    {!inputValue && (
                      <IconButton
                        type="button"
                        sx={{
                          padding: theme.spacing(1),
                        }}
                        onClick={() => {
                          setCollapsed(true);
                        }}>
                        <Icon
                          iconName={ICON_NAME.CHEVRON_LEFT}
                          fontSize="small"
                          sx={{
                            color: focused ? theme.palette.primary.main : theme.palette.text.secondary,
                            margin: theme.spacing(2),
                          }}
                        />
                      </IconButton>
                    )}
                  </Paper>
                );
              }}
              renderOption={(props, option) => {
                const matches = match(option.label, inputValue);
                const parts = parse(option.label, matches);
                const { className: _, style: __, ...rest } = props;
                return (
                  <li {...rest} key={option.label}>
                    <ListItemButton
                      sx={{
                        paddingLeft: theme.spacing(3),
                        "&:hover": {
                          backgroundColor: theme.palette.background.default,
                        },
                      }}>
                      <ListItemText
                        primary={
                          <Typography
                            noWrap
                            sx={{
                              textOverflow: "ellipsis",
                              overflow: "hidden",
                              width: "270px",
                            }}
                            variant="body2">
                            {parts.map((part: { highlight: boolean; text: string }, index: number) => (
                              <Typography
                                key={index}
                                component="span"
                                variant="inherit"
                                sx={{
                                  fontWeight: part.highlight ? 600 : 300,
                                }}>
                                {part.text}
                              </Typography>
                            ))}
                          </Typography>
                        }
                      />
                    </ListItemButton>
                  </li>
                );
              }}
            />
          )}
        </>
      )}
    </>
  );
}
