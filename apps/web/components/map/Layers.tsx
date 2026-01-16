import { setColorFunction } from "@geomatico/maplibre-cog-protocol";
import React, { useMemo } from "react";
import type { LayerProps, MapGeoJSONFeature } from "react-map-gl/maplibre";
import { Layer as MapLayer, Source } from "react-map-gl/maplibre";

import { GEOAPI_BASE_URL, SYSTEM_LAYERS_IDS } from "@/lib/constants";
import { excludes as excludeOp } from "@/lib/transformers/filter";
import {
  getHightlightStyleSpec,
  getSymbolStyleSpec,
  transformToMapboxLayerStyleSpec,
} from "@/lib/transformers/layer";
import { generateCOGColorFunction } from "@/lib/utils/map/cog-styling";
import { getLayerKey } from "@/lib/utils/map/layer";
import type { FeatureLayerProperties, Layer, RasterLayerProperties } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";
import { type ScenarioFeatures, scenarioEditTypeEnum } from "@/lib/validations/scenario";

import { useAppSelector } from "@/hooks/store/ContextHooks";

interface LayersProps {
  layers?: ProjectLayer[] | Layer[];
  selectedScenarioLayer?: ProjectLayer | null;
  highlightFeature?: MapGeoJSONFeature | null;
  scenarioFeatures?: ScenarioFeatures | null;
}

const Layers = (props: LayersProps) => {
  const temporaryFilters = useAppSelector((state) => state.map.temporaryFilters);
  const mapMode = useAppSelector((state) => state.map.mapMode);
  const scenarioFeaturesToExclude = useMemo(() => {
    const featuresToExclude: { [key: string]: string[] } = {};
    props.scenarioFeatures?.features.forEach((feature) => {
      // Exclude deleted and modified features
      if (
        feature.properties?.edit_type === scenarioEditTypeEnum.Enum.d ||
        feature.properties?.edit_type === scenarioEditTypeEnum.Enum.m
      ) {
        const projectLayerId = feature.properties.layer_project_id;
        if (!projectLayerId || !feature.properties?.feature_id) return;

        if (!featuresToExclude[projectLayerId]) featuresToExclude[projectLayerId] = [];

        if (feature.properties?.feature_id)
          featuresToExclude[projectLayerId].push(feature.properties?.feature_id);
      }
    });

    return featuresToExclude;
  }, [props.scenarioFeatures]);

  const getLayerQueryFilter = (layer: ProjectLayer | Layer) => {
    const cqlFilter = layer["query"]?.cql;
    if (!layer["layer_id"] || (!Object.keys(scenarioFeaturesToExclude).length && mapMode === "data"))
      return cqlFilter;

    const extendedFilter = JSON.parse(JSON.stringify(cqlFilter || {}));
    if (scenarioFeaturesToExclude[layer.id]?.length && mapMode === "data") {
      const scenarioFeaturesExcludeFilter = excludeOp("id", scenarioFeaturesToExclude[layer.id]);
      const parsedScenarioFeaturesExcludeFilter = JSON.parse(scenarioFeaturesExcludeFilter);
      // Append the filter to the existing filters
      if (extendedFilter["op"] === "and" && extendedFilter["args"]) {
        extendedFilter["args"].push(parsedScenarioFeaturesExcludeFilter);
      } else {
        // Create a new filter
        extendedFilter["op"] = "and";
        extendedFilter["args"] = [parsedScenarioFeaturesExcludeFilter];
      }
    }

    if (mapMode !== "data" && temporaryFilters.length > 0) {
      const nonCrossFilters = temporaryFilters
        .filter((filter) => filter.layer_id === layer.id)
        .map((filter) => filter.filter);
      const spatialCrossFilters = temporaryFilters
        .filter((filter) => filter.layer_id !== layer.id && filter.spatial_cross_filter)
        .map((filter) => filter.spatial_cross_filter);
      // 3- Merge all filters
      const allFilters = [...nonCrossFilters, ...spatialCrossFilters];
      if (allFilters.length === 0) return extendedFilter;
      const extendedWithTemporaryFilters = {
        op: "and",
        args: allFilters,
      };
      if (extendedFilter["args"]) {
        extendedWithTemporaryFilters["args"].push(extendedFilter);
      }
      return extendedWithTemporaryFilters;
    }
    return extendedFilter;
  };

  const getFeatureTileUrl = (layer: ProjectLayer | Layer) => {
    let query = "";
    const extendedQuery = getLayerQueryFilter(layer);
    if (extendedQuery && Object.keys(extendedQuery).length > 0) {
      query = `?filter=${encodeURIComponent(JSON.stringify(extendedQuery))}`;
    }
    const layerId = layer["layer_id"] || layer["id"];
    return `${GEOAPI_BASE_URL}/collections/${layerId}/tiles/WebMercatorQuad/{z}/{x}/{y}${query}`;
  };
  const { useDataLayers, systemLayers } = useMemo(() => {
    const dataLayers = [] as ProjectLayer[] | Layer[];
    const sysLayers = [] as ProjectLayer[] | Layer[];

    props.layers?.forEach((layer) => {
      const layerId = layer["layer_id"] ?? layer.id;
      if (SYSTEM_LAYERS_IDS.indexOf(layerId) === -1) {
        dataLayers.push(layer);
      } else {
        sysLayers.push(layer);
      }
    });
    return { useDataLayers: dataLayers, systemLayers: sysLayers };
  }, [props.layers]);

  return (
    <>
      {useDataLayers?.length
        ? useDataLayers.map((layer: ProjectLayer | Layer, index: number) =>
            (() => {
              if (layer.type === "feature") {
                return (
                  <Source key={layer.id} type="vector" tiles={[getFeatureTileUrl(layer)]} maxzoom={14}>
                    {!layer.properties?.["custom_marker"] && (
                      <MapLayer
                        key={getLayerKey(layer)}
                        minzoom={layer.properties.min_zoom || 0}
                        maxzoom={layer.properties.max_zoom || 24}
                        id={layer.id.toString()}
                        {...(transformToMapboxLayerStyleSpec(layer) as LayerProps)}
                        beforeId={
                          index === 0 || !useDataLayers ? undefined : useDataLayers[index - 1].id.toString()
                        }
                        source-layer="default"
                      />
                    )}
                    {layer.feature_layer_geometry_type === "polygon" && (
                      <MapLayer
                        key={`stroke-${layer.id.toString()}`}
                        id={`stroke-${layer.id.toString()}`}
                        minzoom={layer.properties.min_zoom || 0}
                        maxzoom={layer.properties.max_zoom || 24}
                        beforeId={
                          index === 0 || !useDataLayers ? undefined : useDataLayers[index - 1].id.toString()
                        }
                        {...(transformToMapboxLayerStyleSpec({
                          ...layer,
                          feature_layer_geometry_type: "line",
                          properties: {
                            ...layer.properties,
                            opacity: 1, // todo: add stroke_opacity to the layer properties
                            visibility:
                              layer.properties?.visibility &&
                              (layer.properties as FeatureLayerProperties)?.stroked,
                          },
                        }) as LayerProps)}
                        source-layer="default"
                      />
                    )}

                    {/* Labels for all layers that aren't a custom marker*/}
                    {((layer.properties as FeatureLayerProperties)?.text_label ||
                      layer.properties?.["custom_marker"]) && (
                      <MapLayer
                        key={
                          layer.properties?.["custom_marker"] ? getLayerKey(layer) : `text-label-${layer.id}`
                        }
                        id={
                          layer.properties?.["custom_marker"] ? layer.id.toString() : `text-label-${layer.id}`
                        }
                        source-layer="default"
                        minzoom={layer.properties.min_zoom || 0}
                        maxzoom={layer.properties.max_zoom || 24}
                        {...(getSymbolStyleSpec(
                          (layer.properties as FeatureLayerProperties)?.text_label,
                          layer
                        ) as LayerProps)}
                        beforeId={
                          index === 0 || !useDataLayers ? undefined : useDataLayers[index - 1].id.toString()
                        }
                      />
                    )}

                    {/* HighlightLayer */}
                    {props.highlightFeature &&
                      props.highlightFeature.properties?.id &&
                      props.highlightFeature.layer.id === layer.id.toString() && (
                        <MapLayer
                          id={`highlight-${layer.id}`}
                          source-layer="default"
                          {...(getHightlightStyleSpec(props.highlightFeature) as LayerProps)}
                        />
                      )}
                  </Source>
                );
              } else if (layer.type === "raster" && layer.url) {
                const rasterProperties = layer.properties as RasterLayerProperties;

                // Register color function for COG layers with custom styling
                // Only needed for color_range, categories, hillshade (not image - use native MapLibre properties)
                if (layer.data_type === "cog" && rasterProperties?.style?.style_type !== "image") {
                  const colorFunction = generateCOGColorFunction(rasterProperties.style);
                  if (colorFunction) {
                    setColorFunction(layer.url, colorFunction);
                  }
                }

                return (
                  <Source
                    key={layer.id}
                    type="raster"
                    {...(layer.data_type === "cog" ? { url: `cog://${layer.url}` } : { tiles: [layer.url] })}
                    tileSize={layer.other_properties?.tile_size || 256}>
                    <MapLayer
                      key={getLayerKey(layer)}
                      id={layer.id.toString()}
                      minzoom={layer.properties?.min_zoom || 0}
                      maxzoom={layer.properties?.max_zoom || 24}
                      type="raster"
                      source-layer="default"
                      beforeId={
                        index === 0 || !useDataLayers ? undefined : useDataLayers[index - 1].id.toString()
                      }
                      layout={{
                        visibility: layer.properties?.visibility ? "visible" : "none",
                      }}
                      paint={{
                        "raster-opacity": rasterProperties?.opacity || 1.0,
                        ...(rasterProperties?.style?.style_type === "image" && {
                          "raster-brightness-min": rasterProperties.style.brightness_min ?? 0,
                          "raster-brightness-max": rasterProperties.style.brightness_max ?? 1,
                          "raster-contrast": rasterProperties.style.contrast ?? 0,
                          "raster-saturation": rasterProperties.style.saturation ?? 0,
                        }),
                      }}
                    />
                  </Source>
                );
              } else {
                return null;
              }
            })()
          )
        : null}
      {systemLayers?.length
        ? systemLayers.map((layer: ProjectLayer | Layer) =>
            props.selectedScenarioLayer?.id === layer.id ? (
              <Source
                key={layer.id}
                type="vector"
                tiles={[getFeatureTileUrl(layer)]}
                minzoom={14}
                maxzoom={22}>
                <MapLayer
                  key={getLayerKey(layer)}
                  id={layer.id.toString()}
                  {...(transformToMapboxLayerStyleSpec(layer) as LayerProps)}
                  source-layer="default"
                  minzoom={14}
                  maxzoom={22}
                />
              </Source>
            ) : null
          )
        : null}
    </>
  );
};

export default Layers;
