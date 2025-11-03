"use client";

import type { DragOverEvent, DragStartEvent } from "@dnd-kit/core";
import { DndContext, DragOverlay } from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { Box, Stack, debounce, useTheme } from "@mui/material";
import "maplibre-gl/dist/maplibre-gl.css";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MapRef, ViewStateChangeEvent } from "react-map-gl/maplibre";
import { MapProvider } from "react-map-gl/maplibre";
import { toast } from "react-toastify";
import { v4 } from "uuid";

import { useTranslation } from "@/i18n/client";

import {
  updateProject,
  updateProjectInitialViewState,
  useProject,
  useProjectInitialViewState,
  useProjectScenarioFeatures,
} from "@/lib/api/projects";
import { PATTERN_IMAGES } from "@/lib/constants/pattern-images";
import { DrawProvider } from "@/lib/providers/DrawProvider";
import { setSelectedBuilderItem } from "@/lib/store/map/slice";
import { addOrUpdateMarkerImages, addPatternImages } from "@/lib/transformers/map-image";
import { createSnapToCursorModifier } from "@/lib/utils/dnd-modifier";
import type { FeatureLayerPointProperties } from "@/lib/validations/layer";
import { type BuilderWidgetSchema, builderWidgetSchema, projectSchema } from "@/lib/validations/project";
import { widgetSchemaMap } from "@/lib/validations/widget";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useJobStatus } from "@/hooks/jobs/JobStatus";
import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useBasemap } from "@/hooks/map/MapHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import BuilderConfigPanel from "@/components/builder/ConfigPanel";
import { DraggableItem } from "@/components/builder/widgets/common/DraggableItem";
import { LoadingPage } from "@/components/common/LoadingPage";
import Header from "@/components/header/Header";
import MapViewer from "@/components/map/MapViewer";
import DataProjectLayout from "@/components/map/layouts/desktop/DataProjectLayout";
import PublicProjectLayout from "@/components/map/layouts/desktop/PublicProjectLayout";

const UPDATE_VIEW_STATE_DEBOUNCE_TIME = 200;

export default function MapPage({ params: { projectId } }) {
  const theme = useTheme();
  const { t, i18n } = useTranslation("common");
  const mapRef = useRef<MapRef | null>(null);
  const mapMode = useAppSelector((state) => state.map.mapMode);
  const dispatch = useAppDispatch();

  const {
    project: _project,
    isLoading: isProjectLoading,
    isError: projectError,
    mutate: mutateProject,
  } = useProject(projectId);
  const {
    initialView,
    isLoading: isInitialViewLoading,
    isError: projectInitialViewError,
  } = useProjectInitialViewState(projectId);

  const {
    isLoading: areProjectLayersLoading,
    isError: projectLayersError,
    layers: projectLayers,
    mutate: mutateProjectLayers,
  } = useFilteredProjectLayers(projectId, ["table"], []);

  const project = useMemo(() => {
    if (!_project) return undefined;
    const parsedProject = projectSchema.safeParse(_project);
    if (parsedProject.success) {
      return parsedProject.data;
    } else {
      console.error("Invalid project data:", parsedProject.error);
      return undefined;
    }
  }, [_project]);

  const { activeBasemap } = useBasemap(project);

  const { isProjectEditor, isLoading: isAuthZLoading } = useAuthZ();

  const { scenarioFeatures } = useProjectScenarioFeatures(projectId, project?.active_scenario_id);
  const isLoading = useMemo(
    () => isProjectLoading || isInitialViewLoading || areProjectLayersLoading || isAuthZLoading,
    [isProjectLoading, isInitialViewLoading, areProjectLayersLoading, isAuthZLoading]
  );

  const hasError = useMemo(
    () => projectError || projectInitialViewError || projectLayersError,
    [projectError, projectInitialViewError, projectLayersError]
  );

  const updateViewState = useMemo(
    () =>
      debounce((e: ViewStateChangeEvent) => {
        updateProjectInitialViewState(projectId, {
          zoom: e.viewState.zoom,
          latitude: e.viewState.latitude,
          longitude: e.viewState.longitude,
          pitch: e.viewState.pitch,
          bearing: e.viewState.bearing,
          min_zoom: initialView?.min_zoom ?? 0,
          max_zoom: initialView?.max_zoom ?? 24,
        });
      }, UPDATE_VIEW_STATE_DEBOUNCE_TIME),
    [initialView?.max_zoom, initialView?.min_zoom, projectId]
  );

  const handleMapLoad = useCallback(() => {
    if (mapRef.current) {
      // get all icon layers and add icons to map using addOrUpdateMarkerImages method
      projectLayers?.forEach((layer) => {
        if (layer.type === "feature" && layer.feature_layer_geometry_type === "point") {
          const pointFeatureProperties = layer.properties as FeatureLayerPointProperties;
          addOrUpdateMarkerImages(layer.id, pointFeatureProperties, mapRef.current);
        }
      });

      // load pattern images
      addPatternImages(PATTERN_IMAGES ?? [], mapRef.current);
    }
  }, [projectLayers]);

  useEffect(() => {
    // icons are added to the style, so if the basestyle changes we have to reload icons to the style
    // it takes forever for certain styles to load so we have to wait a bit.
    // Couldn't find an event that catches the basemap change
    const debouncedHandleMapLoad = debounce(handleMapLoad, 200);
    debouncedHandleMapLoad();
  }, [activeBasemap.url, handleMapLoad]);

  useJobStatus(() => {
    mutateProjectLayers();
    mutateProject();
  });

  // Widget Drag and Drop
  const [activeWidget, setActiveWidget] = useState<BuilderWidgetSchema | null>(null);

  const selectedBuilderItem = useAppSelector((state) => state.map.selectedBuilderItem);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleProjectUpdate = async (key: string, value: any, refresh = false) => {
    try {
      const projectToUpdate = JSON.parse(JSON.stringify(project));
      projectToUpdate[key] = value;
      mutateProject(projectToUpdate, refresh);
      await updateProject(projectId, { [key]: value });
    } catch (error) {
      toast.error(t("error_updating_project"));
      mutateProject();
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    const widget = event.active.data?.current;
    if (widget?.config?.type) {
      // There are two possibilities here. Either user has dragged a new widget or an existing one
      // New widgets don't have a setup configuration defined.
      // In that case we have to create a new object with a unique id ready to be pushed in the builder_config when over panels
      if (!widget?.config?.setup) {
        const widgetSchema = widgetSchemaMap[widget.config.type];
        if (!widgetSchema) {
          console.error(`Widget schema for type ${widget.config.type} not found`);
          return;
        }
        const newWidget = widgetSchema.safeParse({
          type: widget.config.type,
        });

        if (newWidget.success) {
          // Add a default title based on the language
          const newWidgetData = newWidget.data;
          if (newWidgetData?.setup?.title && i18n.exists(`common:${newWidgetData.type}`)) {
            newWidgetData.setup.title = i18n.t(`common:${newWidgetData.type}`);
          }
          const newBuilderWidget = builderWidgetSchema.safeParse({
            id: v4(),
            type: "widget",
            config: newWidgetData,
          });
          if (newBuilderWidget.success) {
            setActiveWidget(newBuilderWidget.data);
          } else {
            console.error(
              `Widget schema for type ${widget.config.type} is not valid`,
              newBuilderWidget.error
            );
            return;
          }
        } else {
          console.error(`Widget schema for type ${widget.config.type} is not valid`, newWidget.error);
          return;
        }
      } else {
        setActiveWidget(widget as BuilderWidgetSchema);
      }
    }
  };

  const handleDragEnd = () => {
    setActiveWidget(null);
    handleProjectUpdate("builder_config", project?.builder_config, true);
  };

  const handleDragOver = (event: DragOverEvent) => {
    if (!activeWidget || !project?.builder_config) {
      return;
    }

    const { over } = event;
    if (!over) {
      return;
    }

    const builderConfig = { ...project.builder_config };
    let updatedPanels = [...builderConfig.interface];

    // 1. Find the current panel of the activeWidget (if it exists)
    let currentPanelId: string | undefined;
    let currentPanelIndex: number = -1;
    let currentWidgetIndex: number = -1;

    builderConfig.interface.forEach((panel, pIndex) => {
      const index = panel.widgets.findIndex((w) => w.id === activeWidget.id);
      if (index !== -1) {
        currentPanelId = panel.id;
        currentPanelIndex = pIndex;
        currentWidgetIndex = index;
        return; // Exit forEach once found
      }
    });

    // Determine the target location based on 'over' element type
    if (over.data?.current?.type === "panel") {
      const overPanel = over.data.current;
      const overPanelIndex = updatedPanels.findIndex((p) => p.id === overPanel.id);

      if (overPanelIndex === -1) return; // Should not happen if over.data.current.type is 'panel'

      // If activeWidget is not in any panel, or moving to a different panel
      if (!currentPanelId || currentPanelId !== overPanel.id) {
        // Remove activeWidget from its original panel if it was there
        if (currentPanelId && currentPanelIndex !== -1) {
          updatedPanels = updatedPanels.map((panel, index) => {
            if (index === currentPanelIndex) {
              return {
                ...panel,
                widgets: panel.widgets.filter((w) => w.id !== activeWidget.id),
              };
            }
            return panel;
          });
        }

        // Add the activeWidget to the end of the target panel
        updatedPanels = updatedPanels.map((panel, index) => {
          if (index === overPanelIndex) {
            // Only add if not already present (prevents duplicates during drag over)
            if (!panel.widgets.some((w) => w.id === activeWidget.id)) {
              return {
                ...panel,
                widgets: [...panel.widgets, activeWidget],
              };
            }
          }
          return panel;
        });
      }
      // else, if activeWidget is already in the overPanel, we do nothing special here
      // as panel drop means adding to end. Sorting within panel is handled by widget drop.
    } else if (over.data?.current?.type === "widget") {
      const overWidget = over.data.current as BuilderWidgetSchema; // The widget we are hovering over

      const targetPanelIndex = updatedPanels.findIndex((panel) =>
        panel.widgets.some((w) => w.id === overWidget.id)
      );

      if (targetPanelIndex === -1) return; // Target panel not found

      const targetPanel = updatedPanels[targetPanelIndex];
      const overWidgetIndex = targetPanel.widgets.findIndex((w) => w.id === overWidget.id);

      // If the widget is moving within the SAME panel
      if (currentPanelId === targetPanel.id) {
        // Use arrayMove to reorder widgets within the same panel
        const newWidgets = arrayMove(
          targetPanel.widgets,
          currentWidgetIndex, // from index
          overWidgetIndex // to index
        );

        // Update the panel with the reordered widgets
        updatedPanels = updatedPanels.map((panel, index) => {
          if (index === targetPanelIndex) {
            return {
              ...panel,
              widgets: newWidgets,
            };
          }
          return panel;
        });
      } else {
        // If the widget is moving between DIFFERENT panels (widget to widget drop)
        // Remove activeWidget from its original panel if it was there
        if (currentPanelId && currentPanelIndex !== -1) {
          updatedPanels = updatedPanels.map((panel, index) => {
            if (index === currentPanelIndex) {
              return {
                ...panel,
                widgets: panel.widgets.filter((w) => w.id !== activeWidget.id),
              };
            }
            return panel;
          });
        }

        // Add the activeWidget to the target panel at the overWidget's position
        updatedPanels = updatedPanels.map((panel, index) => {
          if (index === targetPanelIndex) {
            const newWidgets = [...panel.widgets];
            // Ensure activeWidget is not already in this specific spot
            if (!newWidgets.some((w) => w.id === activeWidget.id)) {
              newWidgets.splice(overWidgetIndex, 0, activeWidget);
            }
            return {
              ...panel,
              widgets: newWidgets,
            };
          }
          return panel;
        });
      }
    }

    const newBuilderConfig = {
      ...builderConfig,
      interface: updatedPanels,
    };

    // Only update if the configuration has actually changed
    if (JSON.stringify(newBuilderConfig) !== JSON.stringify(project.builder_config)) {
      handleProjectUpdate("builder_config", newBuilderConfig, false);
      if (selectedBuilderItem?.id !== activeWidget?.id) {
        // Set activeWidget (new ones) to selectedBuilderItem
        dispatch(setSelectedBuilderItem(activeWidget));
      }
    }
  };

  return (
    <>
      {isLoading && <LoadingPage />}
      {!isLoading && !hasError && project && (
        <MapProvider>
          <DrawProvider>
            <Stack component="div" width="100%" height="100%" overflow="hidden">
              <Header
                showHambugerMenu={false}
                mapHeader={true}
                project={project}
                onProjectUpdate={handleProjectUpdate}
              />
              <Box
                sx={{
                  display: "flex",
                  height: "100%",
                  width: "100%",
                  [theme.breakpoints.down("sm")]: {
                    marginLeft: "0",
                    width: `100%`,
                  },
                }}>
                <DndContext
                  onDragOver={handleDragOver}
                  onDragStart={handleDragStart}
                  onDragEnd={handleDragEnd}
                  autoScroll>
                  {mapMode === "data" && (
                    <DataProjectLayout project={project} onProjectUpdate={handleProjectUpdate} />
                  )}
                  <Box
                    sx={{
                      padding: mapMode === "builder" ? "20px" : "0",
                      width: "100%",
                      height: "100%",
                      position: "relative",
                    }}>
                    {mapMode === "builder" && (
                      <Box
                        sx={{
                          position: "absolute",
                          inset: "20px",
                        }}>
                        <PublicProjectLayout
                          projectLayers={projectLayers}
                          project={project}
                          onProjectUpdate={handleProjectUpdate}
                        />
                      </Box>
                    )}
                    <MapViewer
                      layers={projectLayers}
                      mapRef={mapRef}
                      scenarioFeatures={scenarioFeatures}
                      maxExtent={project?.max_extent || undefined}
                      initialViewState={{
                        zoom: initialView?.zoom ?? 3,
                        latitude: initialView?.latitude ?? 48.13,
                        longitude: initialView?.longitude ?? 11.57,
                        pitch: initialView?.pitch ?? 0,
                        bearing: initialView?.bearing ?? 0,
                        fitBoundsOptions: {
                          minZoom: initialView?.min_zoom ?? 0,
                          maxZoom: initialView?.max_zoom ?? 24,
                        },
                      }}
                      mapStyle={activeBasemap?.url}
                      {...(isProjectEditor ? { onMoveEnd: updateViewState } : {})}
                      isEditor={isProjectEditor}
                    />
                  </Box>
                  {mapMode === "builder" && (
                    <BuilderConfigPanel project={project} onProjectUpdate={handleProjectUpdate} />
                  )}

                  {mapMode === "builder" && (
                    <DragOverlay dropAnimation={null} modifiers={[createSnapToCursorModifier("topCenter")]}>
                      {activeWidget?.config?.type ? (
                        <DraggableItem widgetType={activeWidget?.config?.type} isDragging={true} />
                      ) : null}
                    </DragOverlay>
                  )}
                </DndContext>
              </Box>
            </Stack>
          </DrawProvider>
        </MapProvider>
      )}
    </>
  );
}
