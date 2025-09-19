import { Box } from "@mui/material";
import React, { useMemo } from "react";
import { v4 } from "uuid";

import { useTranslation } from "@/i18n/client";

import { MAPBOX_TOKEN } from "@/lib/constants";
import { setGeocoderResult, setSelectedBuilderItem } from "@/lib/store/map/slice";
import type { BuilderWidgetSchema } from "@/lib/validations/project";
import {
  type BuilderPanelSchema,
  type Project,
  type ProjectLayer,
  builderPanelSchema,
} from "@/lib/validations/project";

import { useBasemap } from "@/hooks/map/MapHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import AddSectionButton from "@/components/builder/AddSectionButton";
import type { BuilderPanelSchemaWithPosition } from "@/components/builder/PanelContainer";
import { Container } from "@/components/builder/PanelContainer";
import Header from "@/components/header/Header";
import AttributionControl from "@/components/map/controls/Attribution";
import { BasemapSelector } from "@/components/map/controls/BasemapSelector";
import { Fullscren } from "@/components/map/controls/Fullscreen";
import Geocoder from "@/components/map/controls/Geocoder";
import Scalebar from "@/components/map/controls/Scalebar";
import { UserLocation } from "@/components/map/controls/UserLocation";
import { Zoom } from "@/components/map/controls/Zoom";

export interface PublicProjectLayoutProps {
  project?: Project;
  projectLayers?: ProjectLayer[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (key: string, value: any, refresh?: boolean) => void;
  // add property isEditing to the interface
  viewOnly?: boolean;
}

const PublicProjectLayout = ({
  projectLayers = [],
  project,
  onProjectUpdate,
  viewOnly,
}: PublicProjectLayoutProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();

  const { translatedBaseMaps, activeBasemap } = useBasemap(project);
  const selectedPanel = useAppSelector((state) => state.map.selectedBuilderItem) as BuilderPanelSchema;
  const builderConfig = project?.builder_config;
  const panels = useMemo(() => builderConfig?.interface ?? [], [builderConfig]);
  const PANEL_SIZE = 300;

  // Count total number of panels top, bottom, left, right using useMemo
  const topPanels = useMemo(() => panels.filter((panel) => panel.position === "top"), [panels]);
  const bottomPanels = useMemo(() => panels.filter((panel) => panel.position === "bottom"), [panels]);
  const leftPanels = useMemo(() => panels.filter((panel) => panel.position === "left"), [panels]);
  const rightPanels = useMemo(() => panels.filter((panel) => panel.position === "right"), [panels]);

  const panelsWithPosition: BuilderPanelSchemaWithPosition[] = useMemo(() => {
    return panels.map((panel, index) => {
      // Count the number of left, right, top, bottom panels before the current panel
      const leftPanelsBefore = panels.slice(0, index).filter((p) => p.position === "left").length;
      const rightPanelsBefore = panels.slice(0, index).filter((p) => p.position === "right").length;
      const topPanelsBefore = panels.slice(0, index).filter((p) => p.position === "top").length;
      const bottomPanelsBefore = panels.slice(0, index).filter((p) => p.position === "bottom").length;

      switch (panel.position) {
        case "left":
          return {
            ...panel,
            orientation: "vertical",
            element: {
              left: PANEL_SIZE * leftPanelsBefore,
              top: PANEL_SIZE * topPanelsBefore,
              bottom: PANEL_SIZE * bottomPanelsBefore,
              width: PANEL_SIZE,
            },
          };
        case "right":
          return {
            ...panel,
            orientation: "vertical",
            element: {
              right: PANEL_SIZE * rightPanelsBefore,
              top: PANEL_SIZE * topPanelsBefore,
              bottom: PANEL_SIZE * bottomPanelsBefore,
              width: PANEL_SIZE,
            },
          };
        case "top":
          return {
            ...panel,
            orientation: "horizontal",
            element: {
              top: 0,
              left: PANEL_SIZE * leftPanelsBefore,
              right: PANEL_SIZE * rightPanelsBefore,
              height: PANEL_SIZE,
            },
          };
        case "bottom":
          return {
            ...panel,
            orientation: "horizontal",
            element: {
              bottom: 0,
              left: PANEL_SIZE * leftPanelsBefore,
              right: PANEL_SIZE * rightPanelsBefore,
              height: PANEL_SIZE,
            },
          };
        default:
          return {
            ...panel,
            element: {
              left: 0,
              top: 0,
              right: 0,
              bottom: 0,
            },
          };
      }
    });
  }, [panels]);

  // Check if a panel can be added to a specific position
  const canAddPanel = (position: "top" | "bottom" | "left" | "right") => {
    const topPanelCount = topPanels.length;
    const bottomPanelCount = bottomPanels.length;
    const leftPanelCount = leftPanels.length;
    const rightPanelCount = rightPanels.length;
    // Rules for top and bottom panels
    if ((position === "top" || position === "bottom") && (topPanelCount || bottomPanelCount)) {
      return false;
    }
    // Rules for left and right panels
    if ((position === "left" || position === "right") && leftPanelCount + rightPanelCount >= 2) {
      return false;
    }

    return true;
  };
  const handleChangeOrder = (panelId: string, direction: "left" | "right" | "top" | "bottom") => {
    const prevPanels = panels;
    const newPanels = [...prevPanels];
    const currentIndex = newPanels.findIndex((p) => p.id === panelId);
    if (currentIndex === -1) return prevPanels;

    const currentPanel = newPanels[currentIndex];
    const position = currentPanel.position;
    let targetIndex = currentIndex;

    // Helper function to find nearest panel in direction
    const findNeighbor = (start: number, step: number, condition: (p: BuilderPanelSchema) => boolean) => {
      let i = start + step;
      while (i >= 0 && i < newPanels.length) {
        if (condition(newPanels[i])) return i;
        i += step;
      }
      return -1;
    };

    if (position === "top" || position === "bottom") {
      // Horizontal movement for top/bottom panels
      const step = direction === "left" ? -1 : 1;
      targetIndex = findNeighbor(currentIndex, step, (p) => p.position === "left" || p.position === "right");
    } else if (position === "left" || position === "right") {
      if (direction === "left" || direction === "right") {
        // Horizontal movement within side group
        const sameSidePanels = newPanels
          .map((p, i) => ({ p, i }))
          .filter(({ p }) => p.position === position)
          .sort((a, b) => a.i - b.i);

        const groupIndex = sameSidePanels.findIndex(({ p }) => p.id === panelId);
        if (groupIndex === -1) return prevPanels;

        const newGroupIndex = direction === "left" ? groupIndex - 1 : groupIndex + 1;
        if (newGroupIndex >= 0 && newGroupIndex < sameSidePanels.length) {
          targetIndex = sameSidePanels[newGroupIndex].i;
        }
      } else {
        // Vertical movement to top/bottom
        const targetPosition = direction === "top" ? "top" : "bottom";
        const existing = newPanels.findIndex((p) => p.position === targetPosition);

        if (existing === -1) {
          // Convert to top/bottom panel
          newPanels[currentIndex].position = targetPosition;
          return [...newPanels];
        } else {
          // Swap with existing top/bottom panel
          targetIndex = existing;
        }
      }
    }

    if (targetIndex !== currentIndex && targetIndex !== -1) {
      [newPanels[currentIndex], newPanels[targetIndex]] = [newPanels[targetIndex], newPanels[currentIndex]];
    }

    const builderConfig = {
      interface: newPanels,
      settings: { ...project?.builder_config?.settings },
    };

    onProjectUpdate?.("builder_config", builderConfig);
  };

  const handlePanelClick = (panel: BuilderPanelSchema) => {
    if (viewOnly) return;
    dispatch(setSelectedBuilderItem(panel));
  };

  const onWidgetDelete = (widgetId: string) => {
    if (viewOnly) return;
    const updatedPanels = panels.map((panel) => {
      if (panel.widgets) {
        panel.widgets = panel.widgets.filter((widget) => widget.id !== widgetId);
      }
      return panel;
    });
    const builderConfig = {
      interface: updatedPanels,
      settings: { ...project?.builder_config?.settings },
    };
    onProjectUpdate?.("builder_config", builderConfig);
    dispatch(setSelectedBuilderItem(undefined));
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const onWidgetUpdate = (updatedWidget: BuilderWidgetSchema) => {
    if (viewOnly) return;
    const updatedPanels = panels.map((panel) => {
      if (panel.widgets) {
        panel.widgets = panel.widgets.map((widget) => {
          if (widget.id === updatedWidget.id) {
            return { ...widget, ...updatedWidget };
          }
          return widget;
        });
      }
      return panel;
    });
    const builderConfig = {
      interface: updatedPanels,
      settings: { ...project?.builder_config?.settings },
    };
    onProjectUpdate?.("builder_config", builderConfig);
    dispatch(setSelectedBuilderItem(updatedWidget));
  };

  // Add a new panel to the specified position
  const onAddSection = async (position: "top" | "bottom" | "left" | "right") => {
    if (canAddPanel(position)) {
      const newPanelObj = {
        position: position,
        config: {},
        type: "panel",
        widgets: [],
        id: v4(),
      };
      const _newPanel = builderPanelSchema.safeParse(newPanelObj);
      if (_newPanel.success) {
        const newPanel = _newPanel.data;
        const updatedPanels = [...panels, newPanel];
        const builderConfig = {
          interface: updatedPanels,
          settings: { ...project?.builder_config?.settings },
        };
        await onProjectUpdate?.("builder_config", builderConfig);
      } else {
        console.error("Invalid panel data:", _newPanel.error);
      }
    }
  };

  const addSectionStylePosition = useMemo(() => {
    const style = {
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
    };
    const panelCounts = {
      top: topPanels.length,
      bottom: bottomPanels.length,
      left: leftPanels.length,
      right: rightPanels.length,
    };
    Object.keys(panelCounts).forEach((key) => {
      if (panelCounts[key] > 0) {
        style[key] = panelCounts[key] * PANEL_SIZE;
      }
    });
    return style;
  }, [topPanels, bottomPanels, leftPanels, rightPanels]);

  return (
    <Box sx={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
      {project && builderConfig?.settings?.toolbar && (
        <Header
          showHambugerMenu={false}
          mapHeader={true}
          project={project}
          viewOnly
          showInfo={builderConfig?.settings?.project_info}
        />
      )}
      <Box
        display="flex"
        sx={{
          zIndex: 1,
          position: "relative",
          height: "100%",
          flexGrow: 1,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          pointerEvents: "none",
        }}>
        <Box
          sx={{
            width: "100%",
            height: "100%",
            position: "absolute",
            zIndex: 2,
          }}>
          {/* Left Panel */}
          {panelsWithPosition?.length > 0 && (
            <>
              {panelsWithPosition.map((panel: BuilderPanelSchemaWithPosition) => (
                <Container
                  key={panel.id}
                  panel={panel}
                  projectLayers={projectLayers}
                  viewOnly={viewOnly}
                  selected={selectedPanel?.type === "panel" && selectedPanel?.id === panel.id}
                  onChangeOrder={handleChangeOrder}
                  onWidgetDelete={onWidgetDelete}
                  onWidgetUpdate={onWidgetUpdate}
                  onClick={() => handlePanelClick(panel)}
                />
              ))}
            </>
          )}
          {/* Center Content */}
          {!viewOnly && (
            <Box
              sx={{
                flexGrow: 1,
                position: "absolute",
                ...addSectionStylePosition,
              }}>
              {/* Render AddSectionButton only if the panel can be added */}
              {["top", "bottom", "left", "right"].map((position) => {
                const canAdd = canAddPanel(position as "top" | "bottom" | "left" | "right");
                return (
                  canAdd && (
                    <AddSectionButton
                      key={position}
                      position={position as "top" | "bottom" | "left" | "right"}
                      onClick={() => onAddSection(position as "top" | "bottom" | "left" | "right")}
                    />
                  )
                );
              })}
            </Box>
          )}

          {/* Top-Left Controls */}
          {builderConfig?.settings.location && (
            <Box
              sx={{
                position: "absolute",
                left: leftPanels.length * PANEL_SIZE,
                top: topPanels.length * PANEL_SIZE,
                m: 2,
                zIndex: 2,
              }}>
              <Geocoder
                accessToken={MAPBOX_TOKEN}
                placeholder={t("enter_an_address")}
                tooltip={t("search")}
                onSelect={(result) => {
                  dispatch(setGeocoderResult(result));
                }}
              />
            </Box>
          )}
          {/* Top-Right Controls  */}
          <Box
            sx={{
              position: "absolute",
              right: rightPanels.length * PANEL_SIZE,
              top: topPanels.length * PANEL_SIZE,
              m: 2,
              zIndex: 2,
            }}>
            {builderConfig?.settings.zoom_controls && (
              <Zoom tooltipZoomIn={t("zoom_in")} tooltipZoomOut={t("zoom_out")} />
            )}
            {builderConfig?.settings.fullscreen && (
              <Fullscren tooltipOpen={t("fullscreen")} tooltipExit={t("exit_fullscreen")} />
            )}
            {builderConfig?.settings.find_my_location && <UserLocation tooltip={t("find_location")} />}
          </Box>
          {/* Bottom-Right Controls */}
          <Box
            sx={{
              position: "absolute",
              right: rightPanels.length * PANEL_SIZE,
              bottom: bottomPanels.length * PANEL_SIZE,
              zIndex: 2,
            }}>
            {builderConfig?.settings.basemap && (
              <Box sx={{ m: 2 }}>
                <BasemapSelector
                  styles={translatedBaseMaps}
                  active={activeBasemap.value}
                  basemapChange={async (basemap) => {
                    await onProjectUpdate?.("basemap", basemap);
                  }}
                />
              </Box>
            )}
            <AttributionControl />
          </Box>
          {/* Bottom-Left Controls */}
          {builderConfig?.settings.scalebar && (
            <Box
              sx={{
                position: "absolute",
                left: leftPanels.length * PANEL_SIZE,
                zIndex: 2,
                bottom: bottomPanels.length * PANEL_SIZE,
                m: 2,
                pointerEvents: "none",
              }}>
              <Scalebar />
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default PublicProjectLayout;
