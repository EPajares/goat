import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { updateProjectLayer } from "@/lib/api/projects";
import { updateProjectLayer as updateLocalProjectLayer } from "@/lib/store/layer/slice";
import type { ProjectLayer } from "@/lib/validations/project";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch } from "@/hooks/store/ContextHooks";

/**
 * Custom hook for handling layer style changes in both desktop and mobile layouts
 * Provides a unified way to update layer styles with proper viewOnly mode handling
 */
export const useLayerStyleChange = (projectLayers: ProjectLayer[], viewOnly?: boolean) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { projectId } = useParams() as { projectId: string };
  const { mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);

  const handleStyleChange = async (layerId: string, styleChanges: { opacity: number }) => {
    try {
      if (viewOnly) {
        // For view-only mode, update local Redux state
        const existingLayer = projectLayers.find((l) => l.id.toString() === layerId);
        if (existingLayer) {
          dispatch(
            updateLocalProjectLayer({
              id: existingLayer.id,
              changes: {
                properties: {
                  ...existingLayer.properties,
                  opacity: styleChanges.opacity,
                },
              },
            })
          );
        }
      } else {
        // For edit mode, do optimistic update first, then sync with server
        const layers = JSON.parse(JSON.stringify(projectLayers));
        const index = layers.findIndex((l: ProjectLayer) => l.id.toString() === layerId);
        const layerToUpdate = layers[index];

        if (layerToUpdate) {
          // Update layer properties with new opacity
          if (!layerToUpdate.properties) {
            layerToUpdate.properties = {};
          }
          layerToUpdate.properties.opacity = styleChanges.opacity;

          // Optimistic update
          await mutateProjectLayers(layers, false);

          // Sync with server
          await updateProjectLayer(projectId, layerToUpdate.id, layerToUpdate);
        }
      }
    } catch (error) {
      console.error("LayerStyleHooks - Error updating layer style:", error);
      toast.error(t("error_updating_layer_style", { defaultValue: "Failed to update layer style" }));

      // Revert optimistic updates on error
      if (!viewOnly) {
        mutateProjectLayers();
      }
    }
  };

  return { handleStyleChange };
};
