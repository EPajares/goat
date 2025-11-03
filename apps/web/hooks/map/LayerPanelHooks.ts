import { useMemo, useState } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { useProject, useProjectLayers } from "@/lib/api/projects";
import { SYSTEM_LAYERS_IDS } from "@/lib/constants";
import type { LayerType } from "@/lib/validations/layer";
import {
  featureLayerLinePropertiesSchema,
  featureLayerPointPropertiesSchema,
  featureLayerPolygonPropertiesSchema,
} from "@/lib/validations/layer";
import { type ProjectLayer, projectLayerSchema } from "@/lib/validations/project";

import { ContentActions, MapLayerActions } from "@/types/common";

import { useAppSelector } from "@/hooks/store/ContextHooks";

import type { PopperMenuItem } from "@/components/common/PopperMenu";

export const useLayerSettingsMoreMenu = () => {
  const { t } = useTranslation("common");

  function getLayerMoreMenuOptions(
    layerType: ProjectLayer["type"],
    viewChart?: boolean,
    inCatalog?: ProjectLayer["in_catalog"],
    readOnly?: boolean
  ): PopperMenuItem[] {

    if (readOnly) {
      const readOnlyOptions: PopperMenuItem[] = [
        ...(layerType !== "table" ? [
          {
            id: MapLayerActions.ZOOM_TO,
            label: t("zoom_to"),
            icon: ICON_NAME.ZOOM_IN,
          },
        ] : []),
        ...(layerType !== "feature" || !inCatalog ? [
          {
            id: ContentActions.DOWNLOAD,
            label: t("download"),
            icon: ICON_NAME.DOWNLOAD,
          },
        ] : []),
        {
          id: ContentActions.INFO,
          label: t("data_source_info"),
          icon: ICON_NAME.CIRCLEINFO,
        },
      ];
      return readOnlyOptions;
    }

    if (layerType === "feature") {
      const featureOptions: PopperMenuItem[] = [
        {
          id: MapLayerActions.PROPERTIES,
          label: t("properties"),
          icon: ICON_NAME.CIRCLEINFO,
        },
        {
          id: MapLayerActions.ZOOM_TO,
          label: t("zoom_to"),
          icon: ICON_NAME.ZOOM_IN,
        },
        {
          id: ContentActions.TABLE,
          label: t("open_data_table"),
          icon: ICON_NAME.TABLE,
        },
        ...(viewChart
          ? [
            {
              id: MapLayerActions.CHART,
              label: t("view_chart"),
              icon: ICON_NAME.CHART,
            },
          ]
          : []),
        {
          id: MapLayerActions.DUPLICATE,
          label: t("duplicate"),
          icon: ICON_NAME.COPY,
        },
        {
          id: MapLayerActions.RENAME,
          label: t("rename"),
          icon: ICON_NAME.EDIT,
        },
        ...(inCatalog
          ? []
          : [
            {
              id: ContentActions.DOWNLOAD,
              label: t("download"),
              icon: ICON_NAME.DOWNLOAD,
            },
          ]),
        {
          id: ContentActions.DELETE,
          label: t("delete"),
          icon: ICON_NAME.TRASH,
          color: "error.main",
        },
      ];
      return featureOptions;
    }
    if (layerType === "table") {
      const tableOptions = [
        {
          id: MapLayerActions.PROPERTIES,
          label: t("properties"),
          icon: ICON_NAME.CIRCLEINFO,
        },
        {
          id: ContentActions.TABLE,
          label: t("open_data_table"),
          icon: ICON_NAME.TABLE,
        },
        ...(viewChart
          ? [
            {
              id: MapLayerActions.CHART,
              label: t("view_chart"),
              icon: ICON_NAME.CHART,
            },
          ]
          : []),
        {
          id: MapLayerActions.RENAME,
          label: t("rename"),
          icon: ICON_NAME.EDIT,
        },
        {
          id: ContentActions.DOWNLOAD,
          label: t("download"),
          icon: ICON_NAME.DOWNLOAD,
        },
        {
          id: ContentActions.DELETE,
          label: t("delete"),
          icon: ICON_NAME.TRASH,
          color: "error.main",
        },
      ];

      return tableOptions;
    }
    if (layerType === "raster") {
      const rasterOptions = [
        {
          id: MapLayerActions.PROPERTIES,
          label: t("properties"),
          icon: ICON_NAME.CIRCLEINFO,
        },
        {
          id: MapLayerActions.ZOOM_TO,
          label: t("zoom_to"),
          icon: ICON_NAME.ZOOM_IN,
        },
        {
          id: MapLayerActions.DUPLICATE,
          label: t("duplicate"),
          icon: ICON_NAME.COPY,
        },
        {
          id: MapLayerActions.RENAME,
          label: t("rename"),
          icon: ICON_NAME.EDIT,
        },
        {
          id: ContentActions.DELETE,
          label: t("delete"),
          icon: ICON_NAME.TRASH,
          color: "error.main",
        },
      ];

      return rasterOptions;
    }

    return [];
  }

  const [activeLayer, setActiveLayer] = useState<ProjectLayer>();
  const [moreMenuState, setMoreMenuState] = useState<PopperMenuItem>();

  const closeMoreMenu = () => {
    setActiveLayer(undefined);
    setMoreMenuState(undefined);
  };

  const openMoreMenu = (menuItem: PopperMenuItem, layerItem: ProjectLayer) => {
    setActiveLayer(layerItem);
    setMoreMenuState(menuItem);
  };

  return {
    getLayerMoreMenuOptions,
    activeLayer,
    moreMenuState,
    closeMoreMenu,
    openMoreMenu,
  };
};

export const useLayerActions = (projectLayers: ProjectLayer[]) => {
  function toggleLayerVisibility(layer: ProjectLayer) {
    const layers = JSON.parse(JSON.stringify(projectLayers));
    const index = layers.findIndex((l) => l.id === layer.id);
    const layerToUpdate = layers[index];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let properties = layerToUpdate.properties as any;
    if (!properties) {
      properties = {};
    }

    properties.visibility = !properties.visibility;

    layerToUpdate.properties = properties;
    return { layers, layerToUpdate };
  }

  return {
    toggleLayerVisibility,
  }

};


export const useActiveLayer = (projectId: string) => {
  const { layers: projectLayers, mutate } = useProjectLayers(projectId);
  const activeLayerId = useAppSelector((state) => state.layers.activeLayerId);
  const activeLayer = useMemo(() => {
    const activeLayer = projectLayers?.find((layer) => layer.id === activeLayerId);
    if (!activeLayer) return undefined;
    const properties = activeLayer.properties;
    const parsedActiveLayer = projectLayerSchema.parse(activeLayer);
    if (parsedActiveLayer.feature_layer_geometry_type === "point") {
      parsedActiveLayer.properties = featureLayerPointPropertiesSchema.parse(properties);
    }
    if (parsedActiveLayer.feature_layer_geometry_type === "line") {
      parsedActiveLayer.properties = featureLayerLinePropertiesSchema.parse(properties);
    }

    if (parsedActiveLayer.feature_layer_geometry_type === "polygon") {
      parsedActiveLayer.properties = featureLayerPolygonPropertiesSchema.parse(properties);
    }

    return parsedActiveLayer;
  }, [activeLayerId, projectLayers]);
  return { activeLayer, mutate };
};

export const useFilterQueries = (projectId: string) => {
  const { layers: projectLayers, mutate } = useProjectLayers(projectId);
  const activeLayerId = useAppSelector((state) => state.layers.activeLayerId);
  const activeLayer = projectLayers?.find((layer) => layer.id === activeLayerId);

  return { activeLayer, mutate };
};

export const useFilteredProjectLayers = (
  projectId: string,
  excludeLayerTypes: LayerType[] = [],
  excludeLayerIds: string[] = [...SYSTEM_LAYERS_IDS]
) => {
  const { layers: projectLayers, mutate, isLoading, isError, isValidating } = useProjectLayers(projectId);
  const { project } = useProject(projectId);
  const sortedLayers = useMemo(() => {
    if (!projectLayers || !project) return [];
    if (!project.layer_order) return projectLayers;
    const filteredLayers = projectLayers.filter(
      (layer) => !excludeLayerTypes.includes(layer.type) && !excludeLayerIds.includes(layer.layer_id)
    );

    return filteredLayers.sort(
      (a, b) => project?.layer_order.indexOf(a.id) - project.layer_order.indexOf(b.id)
    );
  }, [projectLayers, project, excludeLayerTypes, excludeLayerIds]);
  return { layers: sortedLayers, mutate, isLoading, isError, isValidating };
};
