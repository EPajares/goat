/**
 * @p4b/draw - Great circle mode
 *
 * Draws geodesic (great circle) arcs between points.
 * Handles antimeridian crossing.
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { circle } from "@turf/circle";
import { distance } from "@turf/distance";
import greatCircle from "@turf/great-circle";
import { point } from "@turf/helpers";

const Constants = MapboxDraw.constants;
const DrawLineString = MapboxDraw.modes.draw_line_string;

export const GREAT_CIRCLE_PROPERTY = "isGreatCircle";
const USER_GREAT_CIRCLE_PROPERTY = `user_${GREAT_CIRCLE_PROPERTY}`;

// Generate great circle arc with antimeridian handling
function generateGreatCircleArc(
  start: [number, number],
  end: [number, number],
  worldOffset: number,
  npoints = 50
): { coordinates: [number, number][]; newWorldOffset: number } {
  try {
    const dx = end[0] - start[0];
    const dy = end[1] - start[1];
    if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) {
      return {
        coordinates: [
          [start[0] + worldOffset * 360, start[1]],
          [end[0] + worldOffset * 360, end[1]],
        ],
        newWorldOffset: worldOffset,
      };
    }

    const gc = greatCircle(start, end, { npoints });

    if (gc.geometry.type === "LineString") {
      const coords = gc.geometry.coordinates.map((c) => [c[0] + worldOffset * 360, c[1]] as [number, number]);
      return { coordinates: coords, newWorldOffset: worldOffset };
    }

    if (gc.geometry.type === "MultiLineString") {
      const segments = gc.geometry.coordinates;
      if (segments.length >= 2) {
        const firstSegment = segments[0];
        const secondSegment = segments[1];
        const goingWest = firstSegment[0][0] > secondSegment[0][0];
        const nextWorldOffset = worldOffset + (goingWest ? 1 : -1);

        const coords: [number, number][] = [
          ...firstSegment.map((c) => [c[0] + worldOffset * 360, c[1]] as [number, number]),
          ...secondSegment.map((c) => [c[0] + nextWorldOffset * 360, c[1]] as [number, number]),
        ];

        return { coordinates: coords, newWorldOffset: nextWorldOffset };
      }
    }
  } catch {
    // Fallback
  }

  return {
    coordinates: [
      [start[0] + worldOffset * 360, start[1]],
      [end[0] + worldOffset * 360, end[1]],
    ],
    newWorldOffset: worldOffset,
  };
}

export function generateGreatCirclePath(coordinates: [number, number][]): [number, number][] {
  if (coordinates.length < 2) return coordinates;

  const result: [number, number][] = [];
  let worldOffset = 0;

  for (let i = 0; i < coordinates.length - 1; i++) {
    const { coordinates: arcCoords, newWorldOffset } = generateGreatCircleArc(
      coordinates[i],
      coordinates[i + 1],
      worldOffset,
      50
    );

    if (i === 0) {
      result.push(...arcCoords);
    } else {
      result.push(...arcCoords.slice(1));
    }

    worldOffset = newWorldOffset;
  }

  return result;
}

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

const GreatCircleMode: typeof DrawLineString = { ...DrawLineString };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
GreatCircleMode.onSetup = function (this: any, opts: any) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const state = (DrawLineString.onSetup as any).call(this, opts);
  if (state.line) {
    state.line.properties = state.line.properties || {};
    state.line.properties[GREAT_CIRCLE_PROPERTY] = true;
  }
  return state;
};

GreatCircleMode.toDisplayFeatures = function (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  this: any,
  state: { line: { id: string }; direction: string },
  geojson: GeoJSON.Feature<GeoJSON.LineString> & { properties: Record<string, unknown> },
  display: (feature: GeoJSON.Feature) => void
) {
  const isActiveLine = geojson.properties.id === state.line.id;
  geojson.properties.active = isActiveLine ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE;

  const isGreatCircle =
    geojson.properties &&
    (geojson.properties[GREAT_CIRCLE_PROPERTY] || geojson.properties[USER_GREAT_CIRCLE_PROPERTY]);

  const displayAsGreatCircle = (feat: GeoJSON.Feature) => {
    if (feat.geometry.type === "LineString" && feat.geometry.coordinates.length >= 2) {
      const originalCoords = feat.geometry.coordinates as [number, number][];
      const greatCircleCoords = generateGreatCirclePath(originalCoords);
      display({
        ...feat,
        geometry: { ...feat.geometry, coordinates: greatCircleCoords },
      } as GeoJSON.Feature);
    } else {
      display(feat);
    }
  };

  if (!isActiveLine) {
    // Handle circle
    const isRadiusLine = geojson.properties?.isRadiusLine || geojson.properties?.user_isRadiusLine;
    const isCircle = geojson.properties?.isCircle || geojson.properties?.user_isCircle;
    if (
      (isRadiusLine || isCircle) &&
      geojson.geometry.type === "LineString" &&
      geojson.geometry.coordinates.length === 2
    ) {
      display(geojson);
      const circlePolygon = regenerateCircleFromLine(geojson);
      if (circlePolygon) display(circlePolygon);
      return;
    }

    if (isGreatCircle && geojson.geometry.type === "LineString" && geojson.geometry.coordinates.length >= 2) {
      displayAsGreatCircle(geojson);
    } else {
      display(geojson);
    }
    return;
  }

  if (geojson.geometry.coordinates.length < 2) return;

  geojson.properties.meta = Constants.meta.FEATURE;

  const originalCoords = geojson.geometry.coordinates as [number, number][];

  for (let i = 0; i < originalCoords.length - 1; i++) {
    const isLastVertex = i === originalCoords.length - 2;
    display(createVertex(state.line.id, originalCoords[i], `${i}`, isLastVertex) as GeoJSON.Feature);
  }

  displayAsGreatCircle(geojson);
};

export default GreatCircleMode;
