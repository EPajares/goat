import { Box, Collapse, Stack, useTheme } from "@mui/material";
import React, { useEffect, useMemo } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { MAPBOX_TOKEN } from "@/lib/constants";
import { setActiveLeftPanel, setActiveRightPanel, setGeocoderResult } from "@/lib/store/map/slice";
import { layerType } from "@/lib/validations/common";
import { FeatureName } from "@/lib/validations/organization";
import type { Project } from "@/lib/validations/project";

import { MapSidebarItemID } from "@/types/map/common";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useActiveLayer, useFilteredProjectLayers, useLayerActions } from "@/hooks/map/LayerPanelHooks";
import { useBasemap } from "@/hooks/map/MapHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import MapSidebar from "@/components/map/Sidebar";
import AttributionControl from "@/components/map/controls/Attribution";
import { BasemapSelector } from "@/components/map/controls/BasemapSelector";
import { Fullscren } from "@/components/map/controls/Fullscreen";
import Geocoder from "@/components/map/controls/Geocoder";
import Scalebar from "@/components/map/controls/Scalebar";
import { Zoom } from "@/components/map/controls/Zoom";
import Legend from "@/components/map/panels/Legend";
import Filter from "@/components/map/panels/filter/Filter";
import LayerPanel from "@/components/map/panels/layer/Layer";
import PropertiesPanel from "@/components/map/panels/properties/Properties";
import Scenario from "@/components/map/panels/scenario/Scenario";
import LayerStyle from "@/components/map/panels/style/LayerStyle";
import Toolbox from "@/components/map/panels/toolbox/Toolbox";

import type { MapSidebarProps } from "../../Sidebar";

const sidebarWidth = 52;
const toolbarHeight = 52;

interface DataProjectLayoutProps {
  project: Project;
  isPublic?: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (key: string, value: any, refresh?: boolean) => void;
}

const DataProjectLayout = ({ project, onProjectUpdate }: DataProjectLayoutProps) => {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const projectId = project.id;
  const { translatedBaseMaps, activeBasemap } = useBasemap(project);
  const activeLeft = useAppSelector((state) => state.map.activeLeftPanel);
  const activeRight = useAppSelector((state) => state.map.activeRightPanel);
  const { activeLayer } = useActiveLayer(projectId);
  const { isProjectEditor, isAppFeatureEnabled } = useAuthZ();
  const { layers: projectLayers, mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);
  const { toggleLayerVisibility } = useLayerActions(projectLayers);

  const leftSidebar: MapSidebarProps = {
    topItems: [
      {
        id: MapSidebarItemID.LAYERS,
        icon: ICON_NAME.LAYERS,
        name: t("layers"),
        component: <LayerPanel projectId={projectId} />,
      },
      {
        id: MapSidebarItemID.LEGEND,
        icon: ICON_NAME.LEGEND,
        name: t("legend"),
        component: <Legend projectLayers={projectLayers} />,
      },
    ],
    bottomItems: [],
    width: sidebarWidth,
    position: "left",
  };

  const rightSidebar: MapSidebarProps = {
    topItems: [
      {
        id: MapSidebarItemID.PROPERTIES,
        icon: ICON_NAME.SLIDERS,
        name: t("properties"),
        component: <PropertiesPanel projectId={projectId} />,
        disabled: !activeLayer,
      },
      {
        id: MapSidebarItemID.FILTER,
        icon: ICON_NAME.FILTER,
        name: t("filter"),
        component: <Filter projectId={projectId} />,
        disabled:
          !activeLayer ||
          (activeLayer?.type !== layerType.Values.feature && activeLayer?.type !== layerType.Values.table),
      },
      {
        id: MapSidebarItemID.STYLE,
        icon: ICON_NAME.STYLE,
        name: t("layer_design"),
        component: <LayerStyle projectId={projectId} />,
        disabled:
          !activeLayer ||
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ![layerType.Values.feature, layerType.Values.raster].includes(activeLayer.type as any),
      },
      {
        id: MapSidebarItemID.TOOLBOX,
        icon: ICON_NAME.TOOLBOX,
        name: t("tools"),
        component: <Toolbox />,
      },
      {
        id: MapSidebarItemID.SCENARIO,
        icon: ICON_NAME.SCENARIO,
        name: t("scenario"),
        component: <Scenario projectId={projectId} />,
        disabled: !isAppFeatureEnabled(FeatureName.SCENARIO),
      },
    ],
    width: sidebarWidth,
    position: "right",
  };

  const activeRightComponent = useMemo(() => {
    if (activeRight) {
      return rightSidebar.topItems?.find((item) => item.id === activeRight && !item.disabled)?.component;
    }
    return undefined;
  }, [activeRight, rightSidebar.topItems]);

  const activeLeftComponent = useMemo(() => {
    if (activeLeft) {
      return leftSidebar.topItems?.find((item) => item.id === activeLeft)?.component;
    }
    return undefined;
  }, [activeLeft, leftSidebar.topItems]);

  useEffect(() => {
    if (
      activeRight !== undefined &&
      !activeLayer &&
      (activeRight === MapSidebarItemID.PROPERTIES ||
        activeRight === MapSidebarItemID.STYLE ||
        activeRight === MapSidebarItemID.FILTER)
    ) {
      dispatch(setActiveRightPanel(undefined));
    }
  }, [activeRight, activeLayer, dispatch]);

  return (
    <>
      {isProjectEditor && (
        <Box
          sx={{
            ".MuiDrawer-paper": {
              height: `calc(100% - ${toolbarHeight}px)`,
              marginTop: `${toolbarHeight}px`,
            },
            [theme.breakpoints.down("sm")]: {
              display: "none",
            },
          }}>
          <MapSidebar
            {...leftSidebar}
            active={activeLeft}
            onClick={(item) => {
              if (item.link) {
                window.open(item.link, "_blank");
                return;
              } else {
                dispatch(setActiveLeftPanel(item.id === activeLeft ? undefined : item.id));
              }
            }}
          />
        </Box>
      )}

      <Stack
        direction="row"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          height: "100%",
          position: "absolute",
          top: 0,
          pointerEvents: "none",
          ...(isProjectEditor && { left: sidebarWidth }),
          [theme.breakpoints.down("sm")]: {
            left: "0",
          },
        }}>
        {isProjectEditor && (
          <Collapse
            timeout={200}
            orientation="horizontal"
            in={activeLeft !== undefined}
            sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
            onExited={() => {
              dispatch(setActiveLeftPanel(undefined));
            }}>
            {activeLeft !== undefined && (
              <Box
                sx={{
                  height: `calc(100% - ${toolbarHeight}px)`,
                  marginTop: `${toolbarHeight}px`,
                  width: 300,
                  pointerEvents: "all",
                }}>
                {activeLeftComponent}
              </Box>
            )}
          </Collapse>
        )}
        {/* Left Controls */}
        <Stack
          direction="column"
          sx={{
            height: `calc(100% - ${toolbarHeight}px)`,
            justifyContent: "space-between",
            marginTop: `${toolbarHeight}px`,
            padding: theme.spacing(4),
          }}>
          <Stack direction="column">
            <Geocoder
              accessToken={MAPBOX_TOKEN}
              placeholder={t("enter_an_address")}
              tooltip={t("search")}
              onSelect={(result) => {
                dispatch(setGeocoderResult(result));
              }}
            />
          </Stack>
          <Stack direction="column">
            {!isProjectEditor && (
              <Stack direction="column">
                <Legend
                  projectLayers={projectLayers}
                  isFloating
                  showAllLayers
                  onVisibilityChange={async (layer) => {
                    const { layers: _layers, layerToUpdate: _layerToUpdate } = toggleLayerVisibility(layer);
                    await mutateProjectLayers(_layers, false);
                  }}
                />
              </Stack>
            )}
            <Scalebar />
          </Stack>
        </Stack>
      </Stack>
      <Stack
        direction="row"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          height: "100%",
          position: "absolute",
          top: 0,
          pointerEvents: "none",
          right: isProjectEditor ? sidebarWidth : 0,
          [theme.breakpoints.down("sm")]: {
            right: "0",
          },
        }}>
        <Stack
          direction="column"
          sx={{
            height: `calc(100% - ${toolbarHeight}px)`,
            justifyContent: "space-between",
            marginTop: `${toolbarHeight}px`,
            pt: theme.spacing(4),
          }}>
          <Stack direction="column" sx={{ pr: 4, pointerEvents: "none" }}>
            <Zoom tooltipZoomIn={t("zoom_in")} tooltipZoomOut={t("zoom_out")} />
            <Fullscren tooltipOpen={t("fullscreen")} tooltipExit={t("exit_fullscreen")} />
          </Stack>
          <Stack direction="column">
            <Box sx={{ pr: 4 }}>
              <BasemapSelector
                styles={translatedBaseMaps}
                active={activeBasemap.value}
                basemapChange={async (basemap) => {
                  await onProjectUpdate?.("basemap", basemap);
                }}
              />
            </Box>
            <AttributionControl />
          </Stack>
        </Stack>
        {isProjectEditor && (
          <Collapse
            timeout={200}
            orientation="horizontal"
            in={activeRight !== undefined}
            onExit={() => {
              dispatch(setActiveRightPanel(undefined));
            }}>
            {activeRight !== undefined && (
              <Box
                sx={{
                  height: `calc(100% - ${toolbarHeight}px)`,
                  marginTop: `${toolbarHeight}px`,
                  width: 300,
                  pointerEvents: "all",
                }}>
                {activeRightComponent}
              </Box>
            )}
          </Collapse>
        )}
      </Stack>
      {isProjectEditor && (
        <Box
          sx={{
            ".MuiDrawer-paper": {
              height: `calc(100% - ${toolbarHeight}px)`,
              marginTop: `${toolbarHeight}px`,
            },
            [theme.breakpoints.down("sm")]: {
              display: "none",
            },
          }}>
          <MapSidebar
            {...rightSidebar}
            active={activeRight}
            onClick={(item) => {
              if (item.link) {
                window.open(item.link, "_blank");
                return;
              } else {
                dispatch(setActiveRightPanel(item.id === activeRight ? undefined : item.id));
              }
            }}
          />
        </Box>
      )}
    </>
  );
};

export default DataProjectLayout;
