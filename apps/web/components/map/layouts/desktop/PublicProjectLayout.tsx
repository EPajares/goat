import { Box } from "@mui/material";
import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { v4 } from "uuid";

import { MAPBOX_TOKEN } from "@/lib/constants";
import { setSelectedLayers } from "@/lib/store/layer/slice";
import {
  removeTemporaryFilter,
  setActiveRightPanel,
  setGeocoderResult,
  setSelectedBuilderItem,
} from "@/lib/store/map/slice";
import type { BuilderWidgetSchema } from "@/lib/validations/project";
import {
  type BuilderPanelSchema,
  type Project,
  type ProjectLayer,
  type ProjectLayerGroup,
  builderPanelSchema,
} from "@/lib/validations/project";

import { MapSidebarItemID } from "@/types/map/common";

import { useLayerStyleChange } from "@/hooks/map/LayerStyleHooks";
import { useBasemap } from "@/hooks/map/MapHooks";
import { useMeasureTool } from "@/hooks/map/useMeasureTool";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import AddSectionButton from "@/components/builder/AddSectionButton";
import type { BuilderPanelSchemaWithPosition } from "@/components/builder/PanelContainer";
import { Container } from "@/components/builder/PanelContainer";
import { ProjectInfo } from "@/components/builder/widgets/information/ProjectInfo";
import { FloatingPanel } from "@/components/common/FloatingPanel";
import Header from "@/components/header/Header";
import AttributionControl from "@/components/map/controls/Attribution";
import { BasemapSelector } from "@/components/map/controls/BasemapSelector";
import { Fullscren } from "@/components/map/controls/Fullscreen";
import Geocoder from "@/components/map/controls/Geocoder";
import Scalebar from "@/components/map/controls/Scalebar";
import { UserLocation } from "@/components/map/controls/UserLocation";
import { Zoom } from "@/components/map/controls/Zoom";
import { MeasureButton, MeasureResultsPanel } from "@/components/map/controls/measure";
import ViewContainer from "@/components/map/panels/Container";
import PropertiesPanel from "@/components/map/panels/properties/Properties";
import SimpleLayerStyle from "@/components/map/panels/style/SimpleLayerStyle";

export interface PublicProjectLayoutProps {
  project?: Project;
  projectLayers?: ProjectLayer[];
  projectLayerGroups?: ProjectLayerGroup[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (key: string, value: any, refresh?: boolean) => void;
  // add property isEditing to the interface
  viewOnly?: boolean;
}

const PublicProjectLayout = ({
  projectLayers = [],
  projectLayerGroups = [],
  project,
  onProjectUpdate,
  viewOnly,
}: PublicProjectLayoutProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  // Layer style change hook
  const { handleStyleChange } = useLayerStyleChange(projectLayers, viewOnly);

  // Measure tool - using the reusable hook
  const measureTool = useMeasureTool();

  const { translatedBaseMaps, activeBasemap } = useBasemap(project);
  const temporaryFilters = useAppSelector((state) => state.map.temporaryFilters);
  const selectedPanel = useAppSelector((state) => state.map.selectedBuilderItem) as BuilderPanelSchema;
  const collapsedPanels = useAppSelector((state) => state.map.collapsedPanels);
  const builderConfig = project?.builder_config;
  const panels = useMemo(() => builderConfig?.interface ?? [], [builderConfig]);
  const PANEL_SIZE = 300;
  const COLLAPSED_SIZE = 40; // Should match the collapsedSize in Container component
  const activeRight = useAppSelector((state) => state.map.activeRightPanel);

  // Layer settings logic (public version)
  const selectedLayerIds = useAppSelector((state) => state.layers.selectedLayerIds || []);
  const activeLayer = useMemo(() => {
    if (selectedLayerIds.length === 1) {
      return projectLayers.find((l) => l.id === selectedLayerIds[0]);
    }
    return null;
  }, [selectedLayerIds, projectLayers]);

  const activeRightComponent = useMemo(() => {
    // Check for layer configuration panel ID (public version - only Properties and Style)
    const layerSettingsIds = [MapSidebarItemID.PROPERTIES, MapSidebarItemID.STYLE];

    if (activeRight && layerSettingsIds.includes(activeRight) && activeLayer) {
      let title = "Layer Settings";
      let content: React.ReactNode = null;

      if (activeRight === MapSidebarItemID.PROPERTIES) {
        title = `${t("data_source_info")}: ${activeLayer.name || t("layer")}`;
        content = <PropertiesPanel activeLayer={activeLayer} />;
      } else if (activeRight === MapSidebarItemID.STYLE) {
        title = `${t("style")}: ${activeLayer.name || t("layer")}`;
        content = <SimpleLayerStyle activeLayer={activeLayer} onStyleChange={handleStyleChange} />;
      }

      return { title, content };
    }
    return null;
  }, [activeRight, activeLayer, handleStyleChange, t]);

  const handleClose = () => {
    dispatch(setSelectedLayers([]));
    dispatch(setActiveRightPanel(undefined));
  };

  // Count total number of panels top, bottom, left, right using useMemo
  const topPanels = useMemo(() => panels.filter((panel) => panel.position === "top"), [panels]);
  const bottomPanels = useMemo(() => panels.filter((panel) => panel.position === "bottom"), [panels]);
  const leftPanels = useMemo(() => panels.filter((panel) => panel.position === "left"), [panels]);
  const rightPanels = useMemo(() => panels.filter((panel) => panel.position === "right"), [panels]);

  // Helper function to get actual panel size considering collapsed state
  const getPanelSize = (panel: BuilderPanelSchema) => {
    const isCollapsed = !!collapsedPanels?.[panel.id];
    return isCollapsed ? COLLAPSED_SIZE : PANEL_SIZE;
  };

  // Calculate the actual occupied space for each position considering collapsed panels
  const getOccupiedSpace = useMemo(() => {
    const leftSpace = leftPanels.reduce((total, panel) => total + getPanelSize(panel), 0);
    const rightSpace = rightPanels.reduce((total, panel) => total + getPanelSize(panel), 0);
    const topSpace = topPanels.reduce((total, panel) => total + getPanelSize(panel), 0);
    const bottomSpace = bottomPanels.reduce((total, panel) => total + getPanelSize(panel), 0);

    return { left: leftSpace, right: rightSpace, top: topSpace, bottom: bottomSpace };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leftPanels, rightPanels, topPanels, bottomPanels, collapsedPanels]);

  const panelsWithPosition: BuilderPanelSchemaWithPosition[] = useMemo(() => {
    return panels.map((panel, index) => {
      // Calculate cumulative space for each position before current panel
      let leftSpaceBefore = 0;
      let rightSpaceBefore = 0;
      let topSpaceBefore = 0;
      let bottomSpaceBefore = 0;

      for (let i = 0; i < index; i++) {
        const prevPanel = panels[i];
        const prevPanelSize = getPanelSize(prevPanel);

        switch (prevPanel.position) {
          case "left":
            leftSpaceBefore += prevPanelSize;
            break;
          case "right":
            rightSpaceBefore += prevPanelSize;
            break;
          case "top":
            topSpaceBefore += prevPanelSize;
            break;
          case "bottom":
            bottomSpaceBefore += prevPanelSize;
            break;
        }
      }

      switch (panel.position) {
        case "left":
          return {
            ...panel,
            orientation: "vertical",
            element: {
              left: leftSpaceBefore,
              top: topSpaceBefore,
              bottom: bottomSpaceBefore,
              width: PANEL_SIZE,
            },
          };
        case "right":
          return {
            ...panel,
            orientation: "vertical",
            element: {
              right: rightSpaceBefore,
              top: topSpaceBefore,
              bottom: bottomSpaceBefore,
              width: PANEL_SIZE,
            },
          };
        case "top":
          return {
            ...panel,
            orientation: "horizontal",
            element: {
              top: topSpaceBefore,
              left: leftSpaceBefore,
              right: rightSpaceBefore,
              height: PANEL_SIZE,
            },
          };
        case "bottom":
          return {
            ...panel,
            orientation: "horizontal",
            element: {
              bottom: bottomSpaceBefore,
              left: leftSpaceBefore,
              right: rightSpaceBefore,
              height: PANEL_SIZE, // Keep original height for smooth transition
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [panels, collapsedPanels]);

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
    // Remove any temporary filters associated with the deleted widget
    const associatedFilters = temporaryFilters.filter((filter) => filter.id === widgetId);
    associatedFilters.forEach((filter) => {
      dispatch(removeTemporaryFilter(filter.id));
    });
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
    return {
      top: getOccupiedSpace.top,
      left: getOccupiedSpace.left,
      right: getOccupiedSpace.right,
      bottom: getOccupiedSpace.bottom,
    };
  }, [getOccupiedSpace]);

  // Calculate control positions based on actual occupied space
  const controlPositions = useMemo(() => {
    return {
      topLeft: {
        left: getOccupiedSpace.left,
        top: getOccupiedSpace.top,
      },
      topRight: {
        right: getOccupiedSpace.right,
        top: getOccupiedSpace.top,
      },
      bottomRight: {
        right: getOccupiedSpace.right,
        bottom: getOccupiedSpace.bottom,
      },
      bottomLeft: {
        left: getOccupiedSpace.left,
        bottom: getOccupiedSpace.bottom,
      },
    };
  }, [getOccupiedSpace]);

  return (
    <Box sx={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
      {project && builderConfig?.settings?.toolbar && (
        <Header showHambugerMenu={false} mapHeader={true} project={project} viewOnly />
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
                  projectLayerGroups={projectLayerGroups}
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
                transition: "all 0.3s",
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
                ...controlPositions.topLeft,
                m: 2,
                zIndex: 2,
                transition: "all 0.3s",
              }}>
              <Geocoder
                accessToken={MAPBOX_TOKEN}
                placeholder={t("enter_an_address")}
                tooltip={t("search")}
                onSelect={(result) => {
                  dispatch(setGeocoderResult(result));
                }}
              />
              {builderConfig?.settings.measure && <MeasureButton {...measureTool} />}
            </Box>
          )}
          {/* Top-Right Controls  */}
          <Box
            sx={{
              position: "absolute",
              ...controlPositions.topRight,
              m: 2,
              zIndex: 2,
              transition: "all 0.3s",
            }}>
            {project && builderConfig?.settings?.project_info && (
              <ProjectInfo project={project} viewOnly={viewOnly} onProjectUpdate={onProjectUpdate} />
            )}
          </Box>
          {/* Right Floating Panel - Measure Results and Layer Settings */}
          {(builderConfig?.settings.measure || activeRightComponent) && (
            <Box
              sx={{
                position: "absolute",
                right: getOccupiedSpace.right + 16,
                top: getOccupiedSpace.top + 16,
                bottom: getOccupiedSpace.bottom + 16,
                zIndex: 10000,
                pointerEvents: "none",
                transition: "all 0.3s",
                display: "flex",
                flexDirection: "row",
                alignItems: "flex-start",
                gap: 2,
              }}>
              {/* Measurement Results Panel */}
              {builderConfig?.settings.measure && <MeasureResultsPanel {...measureTool} />}
              {/* Layer Settings Panel */}
              {activeRightComponent && (
                <FloatingPanel width={400} minHeight="auto" maxHeight="50vh" fillHeight>
                  <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
                    <ViewContainer
                      title={activeRightComponent.title}
                      disablePadding={true}
                      close={handleClose}
                      body={activeRightComponent.content}
                    />
                  </Box>
                </FloatingPanel>
              )}
            </Box>
          )}

          {/* Bottom-Right Controls */}
          <Box
            sx={{
              position: "absolute",
              ...controlPositions.bottomRight,
              m: 2,
              zIndex: 2,
              transition: "all 0.3s",
            }}>
            {builderConfig?.settings.zoom_controls && (
              <Zoom tooltipZoomIn={t("zoom_in")} tooltipZoomOut={t("zoom_out")} />
            )}
            {builderConfig?.settings.fullscreen && (
              <Fullscren tooltipOpen={t("fullscreen")} tooltipExit={t("exit_fullscreen")} />
            )}
            {builderConfig?.settings.find_my_location && <UserLocation tooltip={t("find_location")} />}
            {builderConfig?.settings.basemap && (
              <BasemapSelector
                styles={translatedBaseMaps}
                active={activeBasemap.value}
                basemapChange={async (basemap) => {
                  await onProjectUpdate?.("basemap", basemap);
                }}
              />
            )}
            <AttributionControl />
          </Box>
          {/* Bottom-Left Controls */}
          {builderConfig?.settings.scalebar && (
            <Box
              sx={{
                position: "absolute",
                ...controlPositions.bottomLeft,
                zIndex: 2,
                m: 2,
                pointerEvents: "none",
                transition: "all 0.3s",
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
