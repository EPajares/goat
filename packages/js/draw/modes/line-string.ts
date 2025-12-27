/**
 * @p4b/draw - Enhanced line string mode
 *
 * Extends the default draw_line_string mode to show ALL vertices while drawing,
 * not just the last one. Also handles display of circle and great-circle features.
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { circle } from "@turf/circle";
import { distance } from "@turf/distance";
import { point } from "@turf/helpers";

import { GREAT_CIRCLE_PROPERTY, generateGreatCirclePath } from "./great-circle";

const Constants = MapboxDraw.constants;
const DrawLineString = MapboxDraw.modes.draw_line_string;

const USER_GREAT_CIRCLE_PROPERTY = `user_${GREAT_CIRCLE_PROPERTY}`;

function createVertex(parentId: string, coordinates: [number, number], path: string, selected: boolean) {
  return {
    type: Constants.geojsonTypes.FEATURE,
    properties: {
      meta: Constants.meta.VERTEX,
      parent: parentId,
      coord_path: path,
      active: selected ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
    },
    geometry: {
      type: Constants.geojsonTypes.POINT,
      coordinates,
    },
  };
}

function regenerateCircleFromLine(lineFeature: GeoJSON.Feature): GeoJSON.Feature | null {
  if (lineFeature.geometry.type !== "LineString") return null;
  const coords = (lineFeature.geometry as GeoJSON.LineString).coordinates;
  if (coords.length < 2) return null;

  const center = point(coords[0] as [number, number]);
  const edge = point(coords[1] as [number, number]);
  const radius = distance(center, edge, { units: "kilometers" });
  const featureId = lineFeature.properties?.id || lineFeature.id;

  return circle(center, radius, {
    steps: 64,
    units: "kilometers",
    properties: {
      meta: "feature",
      parent: featureId,
      parentRadiusLine: featureId,
      id: `${featureId}-circle-display`,
      active: lineFeature.properties?.active,
      isCircle: true,
      isDisplayOnly: true,
    },
  });
}

const LineStringMode: typeof DrawLineString = { ...DrawLineString };

LineStringMode.toDisplayFeatures = function (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  this: any,
  state: { line: { id: string }; direction: string },
  geojson: GeoJSON.Feature<GeoJSON.LineString> & { properties: Record<string, unknown> },
  display: (feature: GeoJSON.Feature) => void
) {
  const isActiveLine = geojson.properties.id === state.line.id;
  geojson.properties.active = isActiveLine ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE;

  // Handle circle radius line
  const isRadiusLine = geojson.properties?.isRadiusLine || geojson.properties?.user_isRadiusLine;
  const isCircle = geojson.properties?.isCircle || geojson.properties?.user_isCircle;
  if (
    !isActiveLine &&
    (isRadiusLine || isCircle) &&
    geojson.geometry.type === "LineString" &&
    geojson.geometry.coordinates.length === 2
  ) {
    display(geojson);
    const circlePolygon = regenerateCircleFromLine(geojson);
    if (circlePolygon) display(circlePolygon);
    return;
  }

  // Handle great circle
  const isGreatCircle =
    geojson.properties &&
    (geojson.properties[GREAT_CIRCLE_PROPERTY] || geojson.properties[USER_GREAT_CIRCLE_PROPERTY]);

  if (!isActiveLine) {
    if (isGreatCircle && geojson.geometry.coordinates.length >= 2) {
      const originalCoords = geojson.geometry.coordinates as [number, number][];
      const greatCircleCoords = generateGreatCirclePath(originalCoords);
      return display({
        ...geojson,
        geometry: { ...geojson.geometry, coordinates: greatCircleCoords },
      } as GeoJSON.Feature);
    }
    return display(geojson);
  }

  if (geojson.geometry.coordinates.length < 2) return;

  geojson.properties.meta = Constants.meta.FEATURE;

  // Display ALL vertices
  const coords = geojson.geometry.coordinates;
  for (let i = 0; i < coords.length - 1; i++) {
    const isLastVertex = i === coords.length - 2;
    display(
      createVertex(state.line.id, coords[i] as [number, number], `${i}`, isLastVertex) as GeoJSON.Feature
    );
  }

  display(geojson);
};

export default LineStringMode;
