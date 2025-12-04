import { IconButton, Stack, Tooltip, Typography, useTheme } from "@mui/material";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { useParams } from "next/navigation";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useMap } from "react-map-gl/maplibre";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { setIsMapGetInfoActive, setMapCursor, setToolboxStartingPoints } from "@/lib/store/map/slice";

import type { SelectorItem } from "@/types/map/common";

import { useLayerByGeomType } from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Selector from "@/components/map/panels/common/Selector";
import LayerNumberOfFeaturesAlert from "@/components/map/panels/toolbox/common/LayerNumberOfFeaturesAlert";

const StartingPoints = ({ maxStartingPoints }: { maxStartingPoints: number | undefined }) => {
  const { map } = useMap();
  const theme = useTheme();
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const startingPoints = useAppSelector((state) => state.map.toolboxStartingPoints);

  const handleZoomToStartingPoint = (coordinate: [number, number]) => {
    if (!map) return;
    map.flyTo({ center: coordinate, zoom: 16 });
  };

  const handleDeleteStartingPoint = (index: number) => {
    if (!startingPoints?.length) return;
    const newStartingPoints = startingPoints.filter((_, i) => i !== index);
    dispatch(setToolboxStartingPoints(undefined));
    dispatch(setToolboxStartingPoints(newStartingPoints));
  };

  useEffect(() => {
    const handleMapClick = (event) => {
      const coordinate = [event.lngLat.lng, event.lngLat.lat] as [number, number];
      if (maxStartingPoints === 1) {
        dispatch(setToolboxStartingPoints(undefined));
      }
      dispatch(setToolboxStartingPoints([coordinate]));
    };
    if (!map) return;
    map.on("click", handleMapClick);
    return () => {
      map.off("click", handleMapClick);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <Table size="small" aria-label="starting point table" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell align="left" sx={{ backgroundColor: "transparent" }}>
              <Typography variant="caption" fontWeight="bold">
                Lon
              </Typography>
            </TableCell>
            <TableCell align="left" sx={{ backgroundColor: "transparent" }}>
              <Typography variant="caption" fontWeight="bold">
                Lat
              </Typography>
            </TableCell>
            <TableCell align="right" sx={{ backgroundColor: "transparent" }}>
              {" "}
            </TableCell>
          </TableRow>
        </TableHead>
      </Table>
      {/* { Second table as workaround to make the table body scrollable} */}
      <TableContainer style={{ marginTop: 0, maxHeight: 250 }}>
        <Table size="small" aria-label="starting point table">
          <TableBody>
            {!startingPoints?.length && (
              <TableRow>
                <TableCell align="center" colSpan={3}>
                  <Typography variant="caption" fontWeight="bold">
                    {t("no_starting_points_added")}
                  </Typography>
                </TableCell>
              </TableRow>
            )}

            {!startingPoints
              ? null
              : startingPoints.map((point, index) => (
                  <TableRow key={v4()}>
                    <TableCell align="center" sx={{ px: 2 }}>
                      <Typography variant="caption" fontWeight="bold">
                        {point[0].toFixed(4)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center" sx={{ px: 2 }}>
                      <Typography variant="caption" fontWeight="bold">
                        {point[1].toFixed(4)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ px: 2 }}>
                      <Stack direction="row" alignItems="center" justifyContent="end" spacing={1}>
                        <Tooltip title={t("zoom_to_starting_point")} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleZoomToStartingPoint(point)}
                            sx={{
                              "&:hover": {
                                color: theme.palette.primary.main,
                              },
                            }}>
                            <Icon
                              iconName={ICON_NAME.ZOOM_IN}
                              style={{ fontSize: "12px" }}
                              htmlColor="inherit"
                            />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t("delete_starting_point")} placement="top">
                          <IconButton
                            size="small"
                            sx={{
                              "&:hover": {
                                color: theme.palette.error.main,
                              },
                            }}
                            onClick={() => handleDeleteStartingPoint(index)}>
                            <Icon
                              iconName={ICON_NAME.TRASH}
                              style={{ fontSize: "12px" }}
                              htmlColor="inherit"
                            />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};

interface StartingPointOptionsProps {
  isActive: boolean;
  startingPointMethod: SelectorItem;
  setStartingPointMethod: (item: SelectorItem) => void;
  startingPointMethods: SelectorItem[];
  startingPointLayer: SelectorItem | undefined;
  setStartingPointLayer: (item: SelectorItem | undefined) => void;
  currentStartingPoints?: number;
  maxStartingPoints?: number;
}

const StartingPointSelectors: React.FC<StartingPointOptionsProps> = ({
  isActive,
  startingPointMethod,
  setStartingPointMethod,
  startingPointMethods,
  startingPointLayer,
  setStartingPointLayer,
  currentStartingPoints,
  maxStartingPoints,
}) => {
  const dispatch = useAppDispatch();
  const { projectId } = useParams();
  const { t } = useTranslation("common");
  const { filteredLayers } = useLayerByGeomType(["feature"], ["point"], projectId as string);

  useEffect(() => {
    if (isActive && startingPointMethod.value === "map") {
      dispatch(setIsMapGetInfoActive(false));
      dispatch(setMapCursor("crosshair"));
    } else {
      dispatch(setIsMapGetInfoActive(true));
      dispatch(setMapCursor(undefined));
    }
  }, [dispatch, isActive, startingPointMethod.value]);

  return (
    <>
      <Selector
        selectedItems={startingPointMethod}
        setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
          dispatch(setToolboxStartingPoints(undefined));
          setStartingPointLayer(undefined);
          setStartingPointMethod(item as SelectorItem);
        }}
        items={startingPointMethods}
        label={t("select_starting_point_method")}
        placeholder={t("select_starting_point_method_placeholder")}
        tooltip={t("select_starting_point_method_tooltip")}
      />

      {startingPointMethod.value === "browser_layer" && isActive && (
        <Selector
          selectedItems={startingPointLayer}
          setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
            setStartingPointLayer(item as SelectorItem);
          }}
          items={filteredLayers}
          emptyMessage={t("no_point_layer_found")}
          emptyMessageIcon={ICON_NAME.LAYERS}
          label={t("select_point_layer")}
          placeholder={t("select_point_layer_placeholder")}
          tooltip={t("select_point_layer_tooltip")}
        />
      )}

      {startingPointMethod.value === "map" && isActive && (
        <StartingPoints maxStartingPoints={maxStartingPoints} />
      )}
      <>
        {!!maxStartingPoints && !!currentStartingPoints && currentStartingPoints > maxStartingPoints && (
          <LayerNumberOfFeaturesAlert
            currentFeatures={currentStartingPoints}
            maxFeatures={maxStartingPoints}
            texts={{
              maxFeaturesText: t("starting_point_max_points"),
              filterLayerFeaturesActionText:
                startingPointMethod.value === "browser_layer"
                  ? t("please_filter_layer_features")
                  : t("please_delete_starting_points"),
            }}
          />
        )}
      </>
    </>
  );
};

export default StartingPointSelectors;
