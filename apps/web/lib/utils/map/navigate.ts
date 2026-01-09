import bbox from "@turf/bbox";
import bboxPolygon from "@turf/bbox-polygon";
import type { BBox } from "@turf/helpers";
import type { MapRef } from "react-map-gl/maplibre";

import { getExtent } from "@/lib/api/processes";
import type { ProjectLayer } from "@/lib/validations/project";

import { wktToGeoJSON } from "@/lib/utils/map/wkt";

export function zoomToLayer(map: MapRef, wkt_extent: string) {
  const geojson = wktToGeoJSON(wkt_extent);
  const boundingBox = bbox(geojson);
  fitBounds(map, boundingBox as [number, number, number, number]);
}

export function fitBounds(
  map: MapRef,
  bounds: [number, number, number, number],
  padding = 40,
  maxZoom = 18,
  duration = 1000
) {
  map.fitBounds(bounds, {
    padding: padding,
    maxZoom: maxZoom,
    duration: duration,
  });
}

export function getMapExtentCQL(map: MapRef) {
  const bounds = map.getBounds();
  if (!bounds) return;
  const bbox = bounds.toArray().flat();
  if (!bbox) return;
  const polygon = bboxPolygon(bbox as BBox);
  const geometry = polygon.geometry;
  const cqlFilter = `{"op":"s_intersects","args":[{"property":"geom"}, ${JSON.stringify(geometry)}]}`;
  return cqlFilter;
}

export function zoomToFeatureCollection(
  map: MapRef,
  featureCollection: GeoJSON.FeatureCollection,
  options: Partial<{
    padding: number;
    maxZoom: number;
    duration: number;
  }> = {}
) {
  if (!featureCollection || !featureCollection.features.length) return;
  const { padding = 40, maxZoom = 18, duration = 1000 } = options; // Destructure with defaults

  const _bbox = bbox(featureCollection);
  fitBounds(map, _bbox as [number, number, number, number], padding, maxZoom, duration);
}

/**
 * Smart zoom to a project layer.
 * - For feature layers with CQL filters: fetches filtered extent from API
 * - For raster layers or layers without filters: uses stored extent
 * - Falls back to stored extent on API error
 */
export async function zoomToProjectLayer(
  map: MapRef,
  layer: ProjectLayer
): Promise<void> {
  // Check if layer has a CQL filter applied
  const hasCqlFilter = layer.query?.cql && Object.keys(layer.query.cql).length > 0;

  if (hasCqlFilter && layer.layer_id) {
    try {
      console.log("zoomToProjectLayer: Fetching filtered extent for", layer.layer_id);
      // Fetch filtered extent from API
      const cqlFilter = JSON.stringify(layer.query?.cql);
      const result = await getExtent(layer.layer_id, cqlFilter);
      console.log("zoomToProjectLayer: Got result", result);

      if (result.bbox) {
        // API returned valid bbox [minx, miny, maxx, maxy]
        fitBounds(map, result.bbox);
        return;
      }
      console.log("zoomToProjectLayer: Empty bbox result, falling back");
      // If bbox is null (empty result), fall through to stored extent
    } catch (error) {
      // On error, fall back to stored extent
      console.warn("Failed to fetch filtered extent, using stored extent:", error);
    }
  } else {
    console.log("zoomToProjectLayer: No CQL filter, using stored extent");
  }

  // Default: use stored extent (works for rasters, layers without filters, or on error)
  if (layer.extent) {
    zoomToLayer(map, layer.extent);
  }
}
