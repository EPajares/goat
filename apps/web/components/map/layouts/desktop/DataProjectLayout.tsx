import { Box, Stack, type SxProps, type Theme, useTheme } from "@mui/material";
import { alpha } from "@mui/material";
import React, { useEffect, useMemo } from "react";
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
import { MAPBOX_TOKEN, SYSTEM_LAYERS_IDS } from "@/lib/constants";
import { setSelectedLayers } from "@/lib/store/layer/slice";
import { setActiveRightPanel, setGeocoderResult } from "@/lib/store/map/slice";
import { FeatureName } from "@/lib/validations/organization";
import type { Project, ProjectLayerTreeUpdate } from "@/lib/validations/project";

import { MapSidebarItemID } from "@/types/map/common";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useBasemap } from "@/hooks/map/MapHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import AttributionControl from "@/components/map/controls/Attribution";
import { BasemapSelector } from "@/components/map/controls/BasemapSelector";
import { Fullscren } from "@/components/map/controls/Fullscreen";
import Geocoder from "@/components/map/controls/Geocoder";
import Scalebar from "@/components/map/controls/Scalebar";
import { Scenario as ScenarioCtrl } from "@/components/map/controls/Scenario";
import { Toolbox as ToolboxCtrl } from "@/components/map/controls/Toolbox";
import { Zoom } from "@/components/map/controls/Zoom";
import LayerSettingsPanel from "@/components/map/panels/layer/LayerSettingsPanel";
import { ProjectLayerTree } from "@/components/map/panels/layer/ProjectLayerTree";
import Scenario from "@/components/map/panels/scenario/Scenario";
import Toolbox from "@/components/map/panels/toolbox/Toolbox";

const toolbarHeight = 52;
const panelWidth = 300;
const GAP_SIZE = 16;

interface FloatingPanelProps {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
}

const FloatingPanel = ({ children, sx }: FloatingPanelProps) => {
  const theme = useTheme();
  return (
    <Stack
      direction="column"
      sx={[
        {
          direction: "ltr",
          width: `${panelWidth}px`,
          minHeight: "400px",
          height: "auto",
          borderRadius: "1rem",
          backgroundColor: alpha(theme.palette.background.paper, 0.9),
          boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px 10px`,
          backdropFilter: "blur(10px)",
          pointerEvents: "all",
          overflow: "hidden",
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}>
      {children}
    </Stack>
  );
};

interface DataProjectLayoutProps {
  project: Project;
  isPublic?: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (key: string, value: any, refresh?: boolean) => void;
}

const DataProjectLayout = ({ project, onProjectUpdate }: DataProjectLayoutProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const projectId = project.id;

  // Fetch project data with SWR
  const { layers: allProjectLayers, mutate: mutateProjectLayers } = useProjectLayers(projectId);
  const { layerGroups: projectLayerGroups, mutate: mutateProjectLayerGroups } =
    useProjectLayerGroups(projectId);

  // Filter out system layers
  const projectLayers = useMemo(() => {
    return allProjectLayers?.filter((layer) => !SYSTEM_LAYERS_IDS.includes(layer.layer_id)) || [];
  }, [allProjectLayers]);

  const { translatedBaseMaps, activeBasemap } = useBasemap(project);
  const activeRight = useAppSelector((state) => state.map.activeRightPanel);
  const { isAppFeatureEnabled } = useAuthZ();

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
      {
        id: MapSidebarItemID.SCENARIO,
        icon: ICON_NAME.SCENARIO,
        name: t("scenario"),
        component: <Scenario projectId={projectId} />,
        disabled: !isAppFeatureEnabled(FeatureName.SCENARIO),
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
    return rightSidebar.topItems?.find((item) => item.id === activeRight && !item.disabled)?.component;
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

  const handleScenarioToggle = async (open: boolean) => {
    if (open) {
      dispatch(setActiveRightPanel(MapSidebarItemID.SCENARIO));
      dispatch(setSelectedLayers([])); // Clear tree
    } else {
      dispatch(setActiveRightPanel(undefined));
    }
  };

  // Keep Panel state consistent
  useEffect(() => {
    if (activeRight === MapSidebarItemID.PROPERTIES && selectedLayerIds.length === 0) {
      dispatch(setActiveRightPanel(undefined));
    }
  }, [activeRight, selectedLayerIds, dispatch]);

  return (
    <>
      <Box
        sx={{
          position: "absolute",
          top: toolbarHeight + 10,
          height: `calc(100% - ${toolbarHeight + 20}px)`,
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
          }}>
          <FloatingPanel>
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
              viewMode="edit"
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
          <Geocoder
            accessToken={MAPBOX_TOKEN}
            placeholder={t("enter_an_address")}
            tooltip={t("search")}
            onSelect={(result) => {
              dispatch(setGeocoderResult(result));
            }}
          />
          <ToolboxCtrl onToggle={handleToolboxToggle} open={activeRight === MapSidebarItemID.TOOLBOX} />
          <ScenarioCtrl onToggle={handleScenarioToggle} open={activeRight === MapSidebarItemID.SCENARIO} />
        </Box>
      </Box>

      {/* RIGHT OVERLAY */}
      <Stack
        direction="column"
        sx={{
          position: "absolute",
          top: toolbarHeight + 10,
          height: `calc(100% - ${toolbarHeight + 10}px)`,
          right: 10,
          zIndex: (theme) => theme.zIndex.drawer + 1,
          pointerEvents: "none",
          alignItems: "flex-end",
        }}>
        {activeRightComponent && <FloatingPanel sx={{ mb: 2 }}>{activeRightComponent}</FloatingPanel>}

        <Stack
          direction="column"
          alignItems="flex-end"
          sx={{
            marginTop: "auto",
            pointerEvents: "all",
            width: "max-content",
            maxWidth: "none",
            whiteSpace: "nowrap",
          }}>
          <Stack direction="column" alignItems="flex-end" sx={{ mb: 1 }}>
            <Zoom tooltipZoomIn={t("zoom_in")} tooltipZoomOut={t("zoom_out")} />
            <Fullscren tooltipOpen={t("fullscreen")} tooltipExit={t("exit_fullscreen")} />
            <BasemapSelector
              styles={translatedBaseMaps}
              active={activeBasemap.value}
              basemapChange={async (basemap) => {
                await onProjectUpdate?.("basemap", basemap);
              }}
            />
          </Stack>
          <AttributionControl />
        </Stack>
      </Stack>
    </>
  );
};

export default DataProjectLayout;
