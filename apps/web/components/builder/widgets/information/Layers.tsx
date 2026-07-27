import { Box, InputAdornment, TextField } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
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
import TabsLayerLayout from "@/components/builder/widgets/information/TabsLayerLayout";

interface LayerInformationProps {
  widgetId: string;
  config: LayerInformationSchema;
  projectLayers: ProjectLayer[];
  projectLayerGroups: ProjectLayerGroup[];
  viewOnly?: boolean;
}

export const LayerInformationWidget = ({
  widgetId,
  config: configProp,
  projectLayers: _publishedProjectLayers,
  projectLayerGroups: _publishedProjectLayerGroups,
  viewOnly,
}: LayerInformationProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { projectId } = useParams() as { projectId: string };
  const { mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);
  const [searchText, setSearchText] = useState("");

  // In edit mode, read the latest config from Redux for instant updates — but ONLY for THIS widget
  const selectedBuilderItem = useAppSelector((state) =>
    !viewOnly ? state.map.selectedBuilderItem : undefined
  );
  const config =
    selectedBuilderItem?.type === "widget" &&
    selectedBuilderItem.id === widgetId &&
    selectedBuilderItem.config?.type === "layers"
      ? (selectedBuilderItem.config as LayerInformationSchema)
      : configProp;

  const reduxProjectLayers = useAppSelector((state) => state.layers.projectLayers);
  const reduxProjectLayerGroups = useAppSelector((state) => state.layers.projectLayerGroups);

  const { layers: editProjectLayers } = useProjectLayers(viewOnly ? undefined : projectId);
  const { layerGroups: editProjectLayerGroups, mutate: mutateProjectLayerGroups } = useProjectLayerGroups(
    viewOnly ? undefined : projectId
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const opts = config.options as Record<string, any> | undefined;
  const excludedLayers: number[] = opts?.excluded_layers ?? [];
  const legendHiddenLayers: number[] = opts?.legend_hidden_layers ?? [];
  const legendSimpleLayers: number[] = opts?.legend_simple_layers ?? [];
  const downloadableLayers: number[] = opts?.downloadable_layers ?? [];
  const outOfZoomBehavior = opts?.out_of_zoom_behavior ?? "hide";

  // Subscribe to currentZoom when we need it for zoom-based behavior (hide or dim)
  const currentZoom = useAppSelector((state) =>
    outOfZoomBehavior !== undefined ? state.map.currentZoom : undefined
  );

  const filteredLayers = useMemo(() => {
    const layersToUse = viewOnly ? reduxProjectLayers : editProjectLayers || [];
    return layersToUse.filter((layer) => {
      if (layer.layer_id && SYSTEM_LAYERS_IDS.includes(layer.layer_id)) return false;
      // Excluded by checkbox in config
      if (excludedLayers.includes(layer.id)) return false;
      // Hidden from legend by "Show in legend" toggle
      if (legendHiddenLayers.includes(layer.id)) return false;
      // Hide layers outside zoom range (only when behavior is "hide")
      if (outOfZoomBehavior === "hide" && currentZoom !== undefined) {
        const minZoom = layer.properties?.min_zoom;
        const maxZoom = layer.properties?.max_zoom;
        if (minZoom !== undefined && maxZoom !== undefined) {
          if (currentZoom < minZoom || currentZoom > maxZoom) return false;
        }
      }
      if (searchText) {
        return layer.name?.toLowerCase().includes(searchText.toLowerCase());
      }
      return true;
    });
  }, [viewOnly, reduxProjectLayers, editProjectLayers, currentZoom, searchText, excludedLayers, legendHiddenLayers, outOfZoomBehavior]);

  // Filter out groups that have no visible layers
  const allGroups = viewOnly ? reduxProjectLayerGroups : editProjectLayerGroups || [];
  const filteredGroups = useMemo(() => {
    const visibleLayerGroupIds = new Set(
      filteredLayers.map((l) => l.layer_project_group_id).filter(Boolean)
    );
    return allGroups.filter((g) => visibleLayerGroupIds.has(g.id));
  }, [allGroups, filteredLayers]);

  const handleTreeUpdate = useCallback(async (updatePayload: ProjectLayerTreeUpdate) => {
    try {
      if (viewOnly) {
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
        // The dashboard widget only edits visibility / legend / expanded state.
        // Pin `order` and `parent_id` to whatever is currently persisted so
        // toggling visibility here cannot reorder or reparent layers on the map.
        const sanitizedItems = updatePayload.items.map((item) => {
          if (item.type === "layer") {
            const existing = editProjectLayers?.find((l) => l.id === item.id);
            return {
              ...item,
              order: existing?.order ?? item.order,
              parent_id: existing?.layer_project_group_id ?? null,
            };
          }
          const existing = editProjectLayerGroups?.find((g) => g.id === item.id);
          return {
            ...item,
            order: existing?.order ?? item.order,
            parent_id: existing?.parent_id ?? null,
          };
        });
        const sanitizedPayload: ProjectLayerTreeUpdate = { items: sanitizedItems };

        if (editProjectLayers) {
          const updatedLayers = editProjectLayers.map((layer) => {
            const updateItem = sanitizedItems.find(
              (item) => item.id === layer.id && item.type === "layer"
            );
            if (updateItem) {
              return {
                ...layer,
                properties: updateItem.properties
                  ? { ...layer.properties, ...updateItem.properties }
                  : layer.properties,
              };
            }
            return layer;
          });
          mutateProjectLayers(updatedLayers, false);
        }

        if (editProjectLayerGroups) {
          const updatedGroups = editProjectLayerGroups.map((group) => {
            const updateItem = sanitizedItems.find(
              (item) => item.id === group.id && item.type === "group"
            );
            if (updateItem) {
              return {
                ...group,
                properties: updateItem.properties
                  ? { ...group.properties, ...updateItem.properties }
                  : group.properties,
              };
            }
            return group;
          });
          mutateProjectLayerGroups(updatedGroups, false);
        }

        await updateProjectLayerTree(projectId, sanitizedPayload);
      }
    } catch (error) {
      console.error("LayerInformationWidget - Error updating tree:", error);
      toast.error("Failed to update tree");
      if (!viewOnly) {
        mutateProjectLayers();
        mutateProjectLayerGroups();
      }
    }
  }, [viewOnly, reduxProjectLayers, reduxProjectLayerGroups, editProjectLayers, editProjectLayerGroups, dispatch, projectId, mutateProjectLayers, mutateProjectLayerGroups]);

  const options = config.options;
  const layoutStyle = options?.layout_style || "tree";

  return (
    <Box>
      {/* Search bar */}
      {options?.show_search && (
        <Box sx={{ px: 1, pb: 1 }}>
          <TextField
            size="small"
            fullWidth
            placeholder={t("search_layers")}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ fontSize: 18, color: "text.disabled" }} />
                </InputAdornment>
              ),
            }}
            sx={{
              "& .MuiOutlinedInput-root": { height: 32 },
              "& .MuiOutlinedInput-input": { fontSize: 13 },
            }}
          />
        </Box>
      )}

      {layoutStyle === "tabs" ? (
        <TabsLayerLayout
          projectId={projectId}
          projectLayers={filteredLayers}
          projectLayerGroups={filteredGroups}
          config={config}
          onTreeUpdate={handleTreeUpdate}
          viewOnly={viewOnly}
          downloadableLayers={downloadableLayers}
          simpleLegendLayerIds={legendSimpleLayers}
          hideLegendHeading={!!opts?.hide_legend_heading}
          groupIcons={opts as Record<string, { url: string; source?: string }> | undefined}
          dimOutOfZoom={outOfZoomBehavior === "dim"}
        />
      ) : (
        <ProjectLayerTree
          projectId={projectId}
          projectLayers={filteredLayers}
          projectLayerGroups={filteredGroups}
          viewMode="view"
          isLoading={false}
          onTreeUpdate={handleTreeUpdate}
          toggleStyle={options?.toggle_style}
          togglePosition={options?.toggle_position}
          moreOptionsStyle={options?.more_options_style}
          allowedActions={{
            style: options?.show_style_action ?? true,
            viewData: options?.show_view_data_action ?? true,
            properties: options?.show_properties_action ?? true,
            zoomTo: options?.show_zoom_to_action ?? true,
          }}
          downloadableLayers={downloadableLayers}
          simpleLegendLayerIds={legendSimpleLayers}
          hideLegendHeading={!!opts?.hide_legend_heading}
          groupIcons={opts as Record<string, { url: string; source?: string }> | undefined}
          dimOutOfZoom={outOfZoomBehavior === "dim"}
          groupInfo={config.setup?.group_info}
        />
      )}
    </Box>
  );
};
