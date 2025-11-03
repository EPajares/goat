import bbox from "@turf/bbox";
import bboxPolygon from "@turf/bbox-polygon";
import type { BBox } from "@turf/helpers";
import type { MapRef } from "react-map-gl/maplibre";

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
