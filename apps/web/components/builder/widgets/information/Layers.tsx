import { Box } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { toast } from "react-toastify";

import { updateProjectLayerTree, useProjectLayerGroups, useProjectLayers } from "@/lib/api/projects";
import { SYSTEM_LAYERS_IDS } from "@/lib/constants";
import { updateProjectLayer as updateLocalProjectLayer } from "@/lib/store/layer/slice";
import { updateProjectLayerGroup as updateLocalProjectLayerGroup } from "@/lib/store/layer/slice";
import type { ProjectLayer, ProjectLayerGroup, ProjectLayerTreeUpdate } from "@/lib/validations/project";
import type { LayerInformationSchema } from "@/lib/validations/widget";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { ProjectLayerTree } from "@/components/map/panels/layer/ProjectLayerTree";

interface LayerInformationProps {
  config: LayerInformationSchema;
  projectLayers: ProjectLayer[];
  projectLayerGroups: ProjectLayerGroup[];
  viewOnly?: boolean;
}

export const LayerInformationWidget = ({
  projectLayers: _publishedProjectLayers,
  projectLayerGroups: _publishedProjectLayerGroups,
  viewOnly,
}: LayerInformationProps) => {
  const dispatch = useAppDispatch();
  const { projectId } = useParams() as { projectId: string };
  const { mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);
  const currentZoom = useAppSelector((state) => state.map.currentZoom);

  // Get Redux state for viewOnly mode
  const reduxProjectLayers = useAppSelector((state) => state.layers.projectLayers);
  const reduxProjectLayerGroups = useAppSelector((state) => state.layers.projectLayerGroups);

  // Use useProjectLayers and useProjectLayerGroups for edit mode (when not viewOnly)
  const { layers: editProjectLayers } = useProjectLayers(viewOnly ? undefined : projectId);
  const { layerGroups: editProjectLayerGroups, mutate: mutateProjectLayerGroups } = useProjectLayerGroups(
    viewOnly ? undefined : projectId
  );

  // Determine which data to use based on viewOnly mode
  const groupsToUse = viewOnly ? reduxProjectLayerGroups : editProjectLayerGroups || [];

  // Filter layers based on zoom level
  const filteredLayers = useMemo(() => {
    const layersToUse = viewOnly ? reduxProjectLayers : editProjectLayers || [];
    return layersToUse.filter((layer) => {
      if (layer.layer_id && SYSTEM_LAYERS_IDS.includes(layer.layer_id)) return false;
      const minZoom = layer.properties?.min_zoom;
      const maxZoom = layer.properties?.max_zoom;
      if (minZoom && maxZoom && currentZoom) {
        return currentZoom >= minZoom && currentZoom <= maxZoom;
      }
      return true;
    });
  }, [viewOnly, reduxProjectLayers, editProjectLayers, currentZoom]);

  // Unified tree update handler for view mode
  const handleTreeUpdate = async (updatePayload: ProjectLayerTreeUpdate) => {
    try {
      if (viewOnly) {
        // For view-only mode, update local Redux state with proper property merging
        updatePayload.items.forEach((item) => {
          if (item.type === "layer" && item.properties) {
            const existingLayer = reduxProjectLayers.find((l) => l.id === item.id);
            if (existingLayer) {
              dispatch(
                updateLocalProjectLayer({
                  id: item.id,
                  changes: {
                    properties: {
                      ...existingLayer.properties,
                      ...item.properties,
                      // Ensure legend properties are properly merged
                      legend: item.properties.legend
                        ? { ...existingLayer.properties?.legend, ...item.properties.legend }
                        : existingLayer.properties?.legend,
                    },
                  },
                })
              );
            }
          } else if (item.type === "group" && item.properties) {
            const existingGroup = reduxProjectLayerGroups.find((g) => g.id === item.id);
            if (existingGroup) {
              dispatch(
                updateLocalProjectLayerGroup({
                  id: item.id,
                  changes: {
                    properties: {
                      ...existingGroup.properties,
                      ...item.properties,
                    },
                  },
                })
              );
            }
          }
        });
      } else {
        // For edit mode, do optimistic updates first, then sync with server
        if (editProjectLayers) {
          const updatedLayers = editProjectLayers.map((layer) => {
            const updateItem = updatePayload.items.find(
              (item) => item.id === layer.id && item.type === "layer"
            );
            if (updateItem) {
              return {
                ...layer,
                order: updateItem.order,
                layer_project_group_id: updateItem.parent_id || null,
                // Deep merge properties to preserve existing properties while updating new ones
                properties: updateItem.properties
                  ? {
                      ...layer.properties,
                      ...updateItem.properties,
                      // Ensure legend properties are properly merged
                      legend: updateItem.properties.legend
                        ? { ...layer.properties?.legend, ...updateItem.properties.legend }
                        : layer.properties?.legend,
                    }
                  : layer.properties,
              };
            }
            return layer;
          });
          mutateProjectLayers(updatedLayers, false);
        }

        if (editProjectLayerGroups) {
          const updatedGroups = editProjectLayerGroups.map((group) => {
            const updateItem = updatePayload.items.find(
              (item) => item.id === group.id && item.type === "group"
            );
            if (updateItem) {
              return {
                ...group,
                order: updateItem.order,
                parent_id: updateItem.parent_id || null,
                // Deep merge properties to preserve existing properties while updating new ones
                properties: updateItem.properties
                  ? { ...group.properties, ...updateItem.properties }
                  : group.properties,
              };
            }
            return group;
          });
          mutateProjectLayerGroups(updatedGroups, false);
        }

        // Then sync with server using the batch update endpoint (same as DataProjectLayout)
        await updateProjectLayerTree(projectId, updatePayload);
      }
    } catch (error) {
      console.error("LayerInformationWidget - Error updating tree:", error);
      toast.error("Failed to update tree");
      // Revert optimistic updates on error
      if (!viewOnly) {
        mutateProjectLayers();
        mutateProjectLayerGroups();
      }
    }
  };

  return (
    <Box>
      <ProjectLayerTree
        projectId={projectId}
        projectLayers={filteredLayers}
        projectLayerGroups={groupsToUse}
        viewMode="view"
        isLoading={false}
        onTreeUpdate={handleTreeUpdate}
      />
    </Box>
  );
};
