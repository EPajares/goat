import { Box, Stack } from "@mui/material";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import {
  addProjectLayers,
  createProjectLayerGroup,
  deleteProjectLayerGroup,
  updateProjectLayerGroup,
  updateProjectLayerTree,
  useProjectLayerGroups,
  useProjectLayers,
} from "@/lib/api/projects";
import { useFolders } from "@/lib/api/folders";
import { SYSTEM_LAYERS_IDS } from "@/lib/constants";
import { DEFAULT_BASEMAP } from "@/lib/constants/basemaps";
import { setSelectedLayers } from "@/lib/store/layer/slice";
import { setActiveRightPanel } from "@/lib/store/map/slice";
import { DATA_PANEL_HEIGHT_CONSUMER_ATTR, DATA_PANEL_HEIGHT_VAR } from "@/components/map/panels/DataPanel";
import type { CustomBasemap, Project, ProjectLayerTreeUpdate } from "@/lib/validations/project";

import { MapSidebarItemID } from "@/types/map/common";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useBasemap } from "@/hooks/map/MapHooks";
import { useCustomBasemapMutations } from "@/hooks/map/useCustomBasemapMutations";
import { useMeasureTool } from "@/hooks/map/useMeasureTool";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { FloatingPanel } from "@/components/common/FloatingPanel";
import FeatureEditPanel from "@/components/map/panels/FeatureEditPanel";
import AttributionControl from "@/components/map/controls/Attribution";
import { BasemapSelector } from "@/components/map/controls/BasemapSelector";
import { CustomBasemapDialog } from "@/components/map/controls/CustomBasemapDialog";
import { Fullscren } from "@/components/map/controls/Fullscreen";
import Scalebar from "@/components/map/controls/Scalebar";
import { Toolbox as ToolboxCtrl } from "@/components/map/controls/Toolbox";
import { Zoom } from "@/components/map/controls/Zoom";
import { MeasureButton, MeasureResultsPanel } from "@/components/map/controls/measure";
import SearchControl from "@/components/map/controls/search/SearchControl";
import { useEditorSearchLayers } from "@/components/map/controls/search/editorSearchLayers";
import LayerSettingsPanel from "@/components/map/panels/layer/LayerSettingsPanel";
import { MapFixedPopupSlot } from "@/components/map/popover/MapFixedPopupSlot";
import { ProjectLayerTree } from "@/components/map/panels/layer/ProjectLayerTree";
import Toolbox from "@/components/map/panels/toolbox/CombinedToolbox";

const toolbarHeight = 52;
const panelWidth = 300;
const GAP_SIZE = 16;

interface DataProjectLayoutProps {
  project: Project;
  isPublic?: boolean;
  // Accepts (key, value, refresh?) or (partial, refresh?) — see handleProjectUpdate in app/map/[projectId]/page.tsx.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (keyOrPartial: any, valueOrRefresh?: any, refresh?: boolean) => void;
}

const DataProjectLayout = ({ project, onProjectUpdate }: DataProjectLayoutProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const projectId = project.id;

  // Measure tool - using the reusable hook
  const measureTool = useMeasureTool();

  // Fetch project data with SWR
  const { layers: allProjectLayers, mutate: mutateProjectLayers } = useProjectLayers(projectId);
  const { layerGroups: projectLayerGroups, mutate: mutateProjectLayerGroups } =
    useProjectLayerGroups(projectId);

  // Filter out system layers
  const projectLayers = useMemo(() => {
    return allProjectLayers?.filter((layer) => !SYSTEM_LAYERS_IDS.includes(layer.layer_id)) || [];
  }, [allProjectLayers]);

  // Queryables for the search scope are only fetched once the control is opened.
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [searchPanelOpen, setSearchPanelOpen] = useState(false);
  const { searchLayers, layersById: searchLayersById } = useEditorSearchLayers(
    projectLayers,
    searchExpanded
  );
  const searchSource = useMemo(
    () => ({ mode: "editor" as const, placesEnabled: true as const, layers: searchLayers }),
    [searchLayers]
  );

  const { translatedBaseMaps, activeBasemap, setActiveBasemap } = useBasemap(project);
  // When editing a non-active basemap we preview it ephemerally (Redux only, no
  // persist); this remembers what to restore when the dialog closes.
  const basemapBeforeEdit = useRef<string | null>(null);

  const { addCustomBasemap, editCustomBasemap, deleteCustomBasemap } =
    useCustomBasemapMutations(project, onProjectUpdate);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<CustomBasemap | null>(null);

  const activeRight = useAppSelector((state) => state.map.activeRightPanel);
  const featureEditorActive = useAppSelector((state) => state.featureEditor.activeLayerId);
  const featureEditorMode = useAppSelector((state) => state.featureEditor.mode);
  const featureEditorActiveFeature = useAppSelector((state) => state.featureEditor.activeFeatureId);
  const showFeatureEditPanel = featureEditorActive && (featureEditorMode === "draw" || !!featureEditorActiveFeature);
  // Panel height is read via CSS variable --data-panel-height for real-time updates
  const isDataPanelOpen = useAppSelector((state) => state.map.isDataPanelOpen);
  const mapMode = useAppSelector((state) => state.map.mapMode);
  const dataPanelVisible = mapMode === "data" && isDataPanelOpen;
  const { isOrgEditor } = useAuthZ();
  const { folders } = useFolders({});
  const projectFolder = useMemo(
    () => (project.folder_id && folders ? folders.find((f) => f.id === project.folder_id) : undefined),
    [folders, project.folder_id]
  );
  const isProjectEditor = useMemo(() => {
    // my_role from the single GET endpoint is authoritative when present
    if (project.my_role) {
      return project.my_role === "project-owner" || project.my_role === "project-editor";
    }
    // Folder grant fallback (e.g. shared via folder, not individual project share)
    if (projectFolder) {
      if (projectFolder.is_owned) return true;
      if (projectFolder.role === "folder-editor") return true;
      if (projectFolder.role === "folder-viewer") return false;
    }
    return isOrgEditor;
  }, [project.my_role, projectFolder, isOrgEditor]);

  // 1. Redux Global Selection
  // Assume array of IDs (number/string)
  const selectedLayerIds = useAppSelector((state) => state.layers.selectedLayerIds || []);

  const handleLayerDuplicate = async (layerId: string) => {
    try {
      await addProjectLayers(projectId, [layerId]);
      mutateProjectLayers();
    } catch (error) {
      toast.error(t("error_duplicating_layer"));
      throw error;
    }
  };

  // Wrapper functions to match ProjectLayerTree expectations
  const handleCreateGroup = async (groupData: { name: string; parent_id?: number }) => {
    await createProjectLayerGroup(projectId, groupData);
    if (projectLayerGroups) {
      mutateProjectLayerGroups();
    }
  };

  const handleUpdateGroup = async (groupData: { name?: string; groupId?: number }) => {
    if (groupData.groupId && groupData.name) {
      await updateProjectLayerGroup(projectId, groupData.groupId, { name: groupData.name });
      if (projectLayerGroups) {
        mutateProjectLayerGroups();
      }
    }
  };

  const handleDeleteGroup = async (groupData: { groupId?: number }) => {
    if (groupData.groupId) {
      await deleteProjectLayerGroup(projectId, groupData.groupId);
      if (projectLayerGroups) {
        mutateProjectLayerGroups();
      }
    }
  };

  // Unified tree update handler - handles all tree changes
  const handleTreeUpdate = async (updatePayload: ProjectLayerTreeUpdate) => {
    try {
      // First, do optimistic updates to both caches to prevent visual flicker
      if (allProjectLayers) {
        // Update layers with new order, parent relationships, and properties
        const updatedLayers = allProjectLayers.map((layer) => {
          const updateItem = updatePayload.items.find(
            (item) => item.id === layer.id && item.type === "layer"
          );
          if (updateItem) {
            return {
              ...layer,
              order: updateItem.order,
              layer_project_group_id: updateItem.parent_id || null,
              // Update properties if provided (includes legend.collapsed, visibility, etc.)
              properties: updateItem.properties
                ? { ...layer.properties, ...updateItem.properties }
                : layer.properties,
            };
          }
          return layer;
        });
        mutateProjectLayers(updatedLayers, false);
      }

      if (projectLayerGroups) {
        // Update groups with new order, parent relationships, and properties
        const updatedGroups = projectLayerGroups.map((group) => {
          const updateItem = updatePayload.items.find(
            (item) => item.id === group.id && item.type === "group"
          );
          if (updateItem) {
            return {
              ...group,
              order: updateItem.order,
              parent_id: updateItem.parent_id || null,
              // Update properties if provided (includes expanded, visibility, etc.)
              properties: updateItem.properties
                ? { ...group.properties, ...updateItem.properties }
                : group.properties,
            };
          }
          return group;
        });
        mutateProjectLayerGroups(updatedGroups, false);
      }

      // Then sync with server using the batch update endpoint
      await updateProjectLayerTree(projectId, updatePayload);
    } catch (error) {
      console.error("Failed to update tree", error);
      toast.error(t("error_updating_tree"));

      // Revert optimistic updates on error by refreshing from server
      mutateProjectLayers();
      mutateProjectLayerGroups();
    }
  };

  const rightSidebar = {
    topItems: [
      {
        id: MapSidebarItemID.TOOLBOX,
        icon: ICON_NAME.TOOLBOX,
        name: t("tools"),
        component: <Toolbox />,
      },
    ],
  };

  // --- DYNAMIC CONTENT ---
  const activeRightComponent = useMemo(() => {
    // Check for ANY layer configuration panel ID
    const layerSettingsIds = [MapSidebarItemID.PROPERTIES, MapSidebarItemID.FILTER, MapSidebarItemID.STYLE];

    if (activeRight && layerSettingsIds.includes(activeRight)) {
      // Return the new panel component
      return <LayerSettingsPanel projectId={projectId} projectLayers={projectLayers || []} />;
    }

    // B. STANDARD TOOLS
    return rightSidebar.topItems?.find((item) => item.id === activeRight)?.component;
  }, [activeRight, rightSidebar.topItems, projectId, projectLayers]);

  // --- INTERACTION LOGIC ---

  const handleToolboxToggle = async (open: boolean) => {
    if (open) {
      dispatch(setActiveRightPanel(MapSidebarItemID.TOOLBOX));
      dispatch(setSelectedLayers([])); // Clear tree
    } else {
      dispatch(setActiveRightPanel(undefined));
    }
  };

  // Keep Panel state consistent
  useEffect(() => {
    const layerSettingsIds = [MapSidebarItemID.PROPERTIES, MapSidebarItemID.FILTER, MapSidebarItemID.STYLE];
    const hasSelectedLayers = selectedLayerIds.length > 0;
    const hasValidSelectedLayer = selectedLayerIds.some((selectedId) =>
      projectLayers.some((layer) => layer.id === selectedId)
    );

    if (layerSettingsIds.includes(activeRight as MapSidebarItemID) && (!hasSelectedLayers || !hasValidSelectedLayer)) {
      dispatch(setSelectedLayers([]));
      dispatch(setActiveRightPanel(undefined));
    }
  }, [activeRight, selectedLayerIds, projectLayers, dispatch]);

  // Width occupied by the right-side stack (measure results, feature
  // editor panel, active right component). Used to size the fixed-popup
  // host below so it doesn't extend behind the panels.
  const measureVisible =
    measureTool.measureOpen || measureTool.measurements.length > 0;
  const rightStackWidth = useMemo(() => {
    const FEATURE_EDIT_PANEL_WIDTH = 320;
    const MEASURE_PANEL_WIDTH = 320;
    const widths: number[] = [];
    if (measureVisible) widths.push(MEASURE_PANEL_WIDTH);
    if (showFeatureEditPanel) widths.push(FEATURE_EDIT_PANEL_WIDTH);
    if (activeRight) widths.push(panelWidth);
    if (widths.length === 0) return 0;
    return widths.reduce((a, b) => a + b, 0) + GAP_SIZE * (widths.length - 1);
  }, [measureVisible, showFeatureEditPanel, activeRight]);

  return (
    <>
      <Box
      {...{ [DATA_PANEL_HEIGHT_CONSUMER_ATTR]: "" }}
        sx={{
          position: "absolute",
          top: toolbarHeight + 10,
          height: `calc(100% - ${toolbarHeight + 20}px - var(${DATA_PANEL_HEIGHT_VAR}, 0px))`,
          left: 10,
          zIndex: (theme) => theme.zIndex.drawer + 1,
          pointerEvents: "none",
        }}>
        <Stack
          direction="column"
          sx={{
            height: "100%",
            alignItems: "flex-start",
            flexWrap: "wrap",
            alignContent: "flex-start",
            rowGap: 4,
            columnGap: 2,
            overflow: "hidden",
          }}>
          <FloatingPanel width={panelWidth} maxHeight="100%">
            <ProjectLayerTree
              projectId={projectId}
              projectLayers={projectLayers || []}
              projectLayerGroups={projectLayerGroups || []}
              isLoading={false}
              onTreeUpdate={handleTreeUpdate}
              onLayerDuplicate={handleLayerDuplicate}
              onCreateGroup={handleCreateGroup}
              onUpdateGroup={handleUpdateGroup}
              onDeleteGroup={handleDeleteGroup}
              viewMode={isProjectEditor ? "edit" : "view"}
            />
          </FloatingPanel>
          <Box sx={{ marginTop: "auto" }}>
            <Scalebar />
          </Box>
        </Stack>
        <Box
          sx={{
            position: "absolute",
            left: `${panelWidth + GAP_SIZE}px`,
            top: 0,
          }}>
          <SearchControl
            source={searchSource}
            layersById={searchLayersById}
            bbox={project?.max_extent ?? undefined}
            onExpandedChange={setSearchExpanded}
            onPanelOpenChange={setSearchPanelOpen}
          />
          {/* The results card is translucent and grows over this stack, so the
              buttons below it step aside while it is open. */}
          {!searchPanelOpen && (
            <>
              {isProjectEditor && (
                <ToolboxCtrl onToggle={handleToolboxToggle} open={activeRight === MapSidebarItemID.TOOLBOX} />
              )}
              <MeasureButton {...measureTool} />
            </>
          )}
        </Box>
      </Box>

      {/* RIGHT OVERLAY */}
      <Stack
        {...{ [DATA_PANEL_HEIGHT_CONSUMER_ATTR]: "" }}
        direction="column"
        sx={{
          position: "absolute",
          top: toolbarHeight + 10,
          height: `calc(100% - ${toolbarHeight + 20}px - var(${DATA_PANEL_HEIGHT_VAR}, 0px))`,
          right: dataPanelVisible && activeRightComponent ? `${panelWidth + GAP_SIZE + 10}px` : 10,
          zIndex: (theme) => theme.zIndex.drawer + 1,
          pointerEvents: "none",
          alignItems: "flex-end",
        }}>
        {!dataPanelVisible && (
          <Stack
            direction="row"
            spacing={2}
            sx={{
              alignItems: "flex-start",
              flex: 1,
              minHeight: 0,
              overflow: "hidden",
            }}>
            <MeasureResultsPanel {...measureTool} />
            {showFeatureEditPanel && (
              <FloatingPanel width={320} maxHeight="100%" fillHeight>
                <FeatureEditPanel />
              </FloatingPanel>
            )}
            {activeRightComponent && (
              <FloatingPanel width={panelWidth} maxHeight="100%" fillHeight>
                {activeRightComponent}
              </FloatingPanel>
            )}
          </Stack>
        )}
        <Stack
          direction="column"
          alignItems="flex-end"
          sx={{
            mt: dataPanelVisible ? "auto" : 2,
            flexShrink: 0,
            pointerEvents: "none",
          }}>
          <Stack direction="column" alignItems="flex-end" sx={{ mb: 1 }}>
            <Zoom tooltipZoomIn={t("zoom_in")} tooltipZoomOut={t("zoom_out")} />
            <Fullscren tooltipOpen={t("fullscreen")} tooltipExit={t("exit_fullscreen")} />
            <BasemapSelector
              styles={translatedBaseMaps}
              active={activeBasemap.value}
              editable
              basemapChange={async (basemap) => {
                await onProjectUpdate?.("basemap", basemap);
              }}
              onAdd={() => {
                setEditing(null);
                setDialogOpen(true);
              }}
              onEdit={(id) => {
                const target =
                  (project?.custom_basemaps as CustomBasemap[] | undefined)?.find(
                    (c) => c.id === id
                  ) ?? null;
                if (target && project?.basemap !== id) {
                  // Ephemeral preview only — reverted on close, never persisted.
                  basemapBeforeEdit.current = project?.basemap ?? DEFAULT_BASEMAP;
                  setActiveBasemap(id);
                }
                setEditing(target);
                setDialogOpen(true);
              }}
            />
          </Stack>
          {/* -10px cancels the right-overlay's 10px bottom inset (height: calc(100% - toolbarHeight - 20px) at top: toolbarHeight+10) so the strip sits flush to the map's bottom edge. */}
          <Box sx={{ mb: "-10px" }}>
            <AttributionControl
              extraAttribution={
                activeBasemap.source === "custom" ? activeBasemap.attribution : null
              }
            />
          </Box>
        </Stack>
      </Stack>
      {/* Right panel + measure results — rendered separately when data panel is open so controls can be to the left */}
      {dataPanelVisible && (
        <Box
          {...{ [DATA_PANEL_HEIGHT_CONSUMER_ATTR]: "" }}
          sx={{
            position: "absolute",
            top: toolbarHeight + 10,
            height: `calc(100% - ${toolbarHeight + 20}px - var(${DATA_PANEL_HEIGHT_VAR}, 0px))`,
            right: 10,
            zIndex: (theme) => theme.zIndex.drawer + 1,
            pointerEvents: "none",
          }}>
          <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start", height: "100%", overflow: "hidden" }}>
            <MeasureResultsPanel {...measureTool} />
            {showFeatureEditPanel && (
              <FloatingPanel width={320} maxHeight="100%" fillHeight>
                <FeatureEditPanel />
              </FloatingPanel>
            )}
            {activeRightComponent && (
              <FloatingPanel width={panelWidth} maxHeight="100%" fillHeight>
                {activeRightComponent}
              </FloatingPanel>
            )}
          </Stack>
        </Box>
      )}
      {/* Host for fixed-anchor feature popups. Sized to the visible map
          content area — top: below the app toolbar, bottom: above the
          data panel, left: past the always-mounted layer tree, right:
          past whichever right-side panels are open. PopupFixedHost
          positions its content to one of this Box's 4 corners, so the
          popup naturally respects the layout's chrome without any
          global offsets or portals. Same pattern as the top-left
          controls (Geocoder / ToolboxCtrl / MeasureButton). */}
      <Box
        {...{ [DATA_PANEL_HEIGHT_CONSUMER_ATTR]: "" }}
        sx={{
          position: "absolute",
          top: toolbarHeight + 10,
          left: panelWidth + GAP_SIZE + 10,
          right: (rightStackWidth ? rightStackWidth + GAP_SIZE : 0) + 10,
          bottom: `calc(10px + var(${DATA_PANEL_HEIGHT_VAR}, 0px))`,
          pointerEvents: "none",
          // Above layout controls (drawer + 1), so a popup at the top-left
          // corner correctly stacks on top of the Geocoder/Toolbox/Measure
          // button column.
          zIndex: (theme) => theme.zIndex.drawer + 2,
        }}>
        <MapFixedPopupSlot layers={projectLayers} />
      </Box>
      <CustomBasemapDialog
        open={dialogOpen}
        initial={editing}
        projectLayers={projectLayers}
        onClose={() => {
          setDialogOpen(false);
          if (basemapBeforeEdit.current !== null) {
            setActiveBasemap(basemapBeforeEdit.current);
            basemapBeforeEdit.current = null;
          }
        }}
        onSubmit={async (payload) => {
          if (editing) {
            await editCustomBasemap(editing.id, payload);
          } else {
            await addCustomBasemap(payload, /* selectAfterAdd */ true);
          }
        }}
        onDelete={
          editing
            ? async () => {
                await deleteCustomBasemap(editing.id, DEFAULT_BASEMAP);
              }
            : undefined
        }
      />
    </>
  );
};

export default DataProjectLayout;
