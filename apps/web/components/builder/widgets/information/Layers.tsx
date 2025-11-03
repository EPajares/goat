import { Box } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo } from "react";

import { updateProjectLayer } from "@/lib/api/projects";
import { SYSTEM_LAYERS_IDS } from "@/lib/constants";
import { updateProjectLayer as updateLocalProjectLayer } from "@/lib/store/layer/slice";
import type { ProjectLayer } from "@/lib/validations/project";
import type { LayerInformationSchema } from "@/lib/validations/widget";

import { useFilteredProjectLayers, useLayerActions } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { Legend } from "@/components/map/controls/Legend";

interface LayerInformationProps {
  config: LayerInformationSchema;
  projectLayers: ProjectLayer[];
  viewOnly?: boolean;
}

export const LayerInformationWidget = ({
  projectLayers: publishedProjectLayers,
  viewOnly,
}: LayerInformationProps) => {
  const dispatch = useAppDispatch();
  const { projectId } = useParams() as { projectId: string };
  const { mutate: mutateProjectLayers, layers: projectLayers } = useFilteredProjectLayers(projectId);
  const { toggleLayerVisibility } = useLayerActions(projectLayers);
  const currentZoom = useAppSelector((state) => state.map.currentZoom);
  const displayLayers = useMemo(() => {
    const _layers = viewOnly ? publishedProjectLayers : projectLayers;
    // If the layer has a min_zoom and max_zoom  is within the current zoom level show the layer. If min_zoom / max_zoom is not set show the layer
    // min_zoom and max_zoom are set in the layer properties
    return _layers.filter((layer) => {
      if (layer.layer_id && SYSTEM_LAYERS_IDS.includes(layer.layer_id)) return false; // TODO: remove this later. the reason is viewOnly is always true until dashboard builder is finished
      const minZoom = layer.properties?.min_zoom;
      const maxZoom = layer.properties?.max_zoom;
      if (minZoom && maxZoom && currentZoom) {
        return currentZoom >= minZoom && currentZoom <= maxZoom;
      }
      return true;
    });
  }, [projectLayers, publishedProjectLayers, viewOnly, currentZoom]);

  return (
    <Box>
      <Legend
        layers={displayLayers}
        enableActions
        hideZoomLevel
        onVisibilityChange={async (layer) => {
          if (viewOnly) {
            dispatch(
              updateLocalProjectLayer({
                id: layer.id,
                changes: {
                  properties: {
                    ...layer.properties,
                    visibility: !layer.properties.visibility,
                  },
                },
              })
            );
          } else {
            const { layers: _layers, layerToUpdate: _layerToUpdate } = toggleLayerVisibility(layer);
            await mutateProjectLayers(_layers, false);
            await updateProjectLayer(projectId, layer.id, _layerToUpdate);
          }
        }}
      />
    </Box>
  );
};
