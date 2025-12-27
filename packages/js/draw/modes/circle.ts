/**
 * @p4b/draw - Circle mode
 *
 * Draws circles by clicking center then edge point.
 * Stores as a radius line (2-point LineString) with circle metadata.
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import bearing from "@turf/bearing";
import { distance } from "@turf/distance";
import { point } from "@turf/helpers";

import { generateCirclePolygon } from "../helpers";
import { generateGreatCirclePath } from "./great-circle";

const Constants = MapboxDraw.constants;
const { doubleClickZoom } = MapboxDraw.lib;
const DrawLineString = MapboxDraw.modes.draw_line_string;

export const CIRCLE_PROPERTY = "isCircle";
export const RADIUS_LINE_PROPERTY = "isRadiusLine";

function createDisplayCircle(
  center: [number, number],
  radiusKm: number,
  active: boolean,
  parentId?: string,
  startBearing?: number
): GeoJSON.Feature<GeoJSON.Polygon> {
  const circlePolygon = generateCirclePolygon(center, radiusKm, startBearing);

  circlePolygon.properties = {
    meta: "static",
    parent: parentId,
    active: active ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
    isCircle: true,
    isDisplayOnly: true,
  };

  return circlePolygon;
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

const CircleMode: typeof DrawLineString = { ...DrawLineString };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
CircleMode.onSetup = function (this: any, _opts: any) {
  const lineFeature = this.newFeature({
    type: Constants.geojsonTypes.FEATURE,
    properties: {
      isRadiusLine: true,
      isCircle: true,
    },
    geometry: {
      type: Constants.geojsonTypes.LINE_STRING,
      coordinates: [],
    },
  });

  const state = {
    line: lineFeature,
    currentVertexPosition: 0,
    direction: "forward",
  };

  this.addFeature(lineFeature);
  this.clearSelectedFeatures();
  doubleClickZoom.disable(this);
  this.updateUIClasses({ mouse: Constants.cursors.ADD });
  this.activateUIButton();

  return state;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
CircleMode.onClick = CircleMode.onTap = function (this: any, state: any, e: any) {
  // End drawing after second point (edge)
  if (state.currentVertexPosition === 1) {
    state.line.updateCoordinate(state.currentVertexPosition, e.lngLat.lng, e.lngLat.lat);

    const coords = state.line.getCoordinates();
    const center = coords[0] as [number, number];
    const edge = coords[1] as [number, number];
    const radiusKm = distance(point(center), point(edge), { units: "kilometers" });

    const bearingValue = bearing(point(center), point(edge));
    const azimuth = bearingValue < 0 ? bearingValue + 360 : bearingValue;

    state.line.setProperty("isRadiusLine", true);
    state.line.setProperty("isCircle", true);
    state.line.setProperty("centerLng", center[0]);
    state.line.setProperty("centerLat", center[1]);
    state.line.setProperty("radiusInKm", radiusKm);
    state.line.setProperty("azimuthDegrees", azimuth);

    return this.changeMode(Constants.modes.SIMPLE_SELECT, {
      featureIds: [state.line.id],
    });
  }

  this.updateUIClasses({ mouse: Constants.cursors.ADD });
  state.line.updateCoordinate(state.currentVertexPosition, e.lngLat.lng, e.lngLat.lat);

  if (state.direction === "forward") {
    state.currentVertexPosition += 1;
    state.line.updateCoordinate(state.currentVertexPosition, e.lngLat.lng, e.lngLat.lat);
  } else {
    state.line.addCoordinate(0, e.lngLat.lng, e.lngLat.lat);
  }

  return null;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
CircleMode.onStop = function (this: any, state: any) {
  doubleClickZoom.enable(this);
  this.activateUIButton();

  if (this.getFeature(state.line.id) === undefined) return;

  const isLineValid = state.line.isValid();
  if (isLineValid) {
    const coords = state.line.getCoordinates();

    if (coords.length >= 2) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      this.map.fire(Constants.events.CREATE as any, {
        features: [state.line.toGeoJSON()],
      });
    } else {
      this.deleteFeature(state.line.id, { silent: true });
    }
  } else {
    this.deleteFeature(state.line.id, { silent: true });
  }
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
CircleMode.onKeyUp = function (this: any, state: any, e: any) {
  if (e.keyCode === 27) {
    this.deleteFeature(state.line.id, { silent: true });
    this.changeMode(Constants.modes.SIMPLE_SELECT);
  } else if (e.keyCode === 13) {
    const coords = state.line.getCoordinates();
    if (coords.length >= 2) {
      this.changeMode(Constants.modes.SIMPLE_SELECT, {
        featureIds: [state.line.id],
      });
    }
  }
};

CircleMode.toDisplayFeatures = function (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  this: any,
  state: { line: { id: string }; direction: string },
  geojson: GeoJSON.Feature<GeoJSON.LineString> & { properties: Record<string, unknown> },
  display: (feature: GeoJSON.Feature) => void
) {
  const isActiveLine = geojson.properties.id === state.line.id;
  geojson.properties.active = isActiveLine ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE;

  if (!isActiveLine) {
    // Handle circle features
    const isRadiusLine = geojson.properties?.isRadiusLine || geojson.properties?.user_isRadiusLine;
    const isCircle = geojson.properties?.isCircle || geojson.properties?.user_isCircle;
    if (
      (isRadiusLine || isCircle) &&
      geojson.geometry.type === "LineString" &&
      geojson.geometry.coordinates.length === 2
    ) {
      display(geojson);

      const center = geojson.geometry.coordinates[0] as [number, number];
      const edge = geojson.geometry.coordinates[1] as [number, number];
      const radiusKm = distance(point(center), point(edge), { units: "kilometers" });

      // Get stored azimuth or calculate it
      const storedAzimuth = geojson.properties?.azimuthDegrees || geojson.properties?.user_azimuthDegrees;
      let azimuth = storedAzimuth;

      if (azimuth === undefined) {
        const bearingValue = bearing(point(center), point(edge));
        azimuth = bearingValue < 0 ? bearingValue + 360 : bearingValue;
      }

      const circlePolygon = createDisplayCircle(
        center,
        radiusKm,
        false,
        geojson.properties?.id as string,
        azimuth
      );
      display(circlePolygon);
      return;
    }

    // Handle great circle features - render them with their curved path
    const isGreatCircle = geojson.properties?.isGreatCircle || geojson.properties?.user_isGreatCircle;
    if (isGreatCircle && geojson.geometry.type === "LineString" && geojson.geometry.coordinates.length >= 2) {
      const originalCoords = geojson.geometry.coordinates as [number, number][];
      const greatCircleCoords = generateGreatCirclePath(originalCoords);
      display({
        ...geojson,
        geometry: { ...geojson.geometry, coordinates: greatCircleCoords },
      } as GeoJSON.Feature);
      return;
    }

    return display(geojson);
  }

  if (geojson.geometry.coordinates.length < 1) return;

  const coords = geojson.geometry.coordinates as [number, number][];

  if (coords.length >= 1) {
    display(createVertex(state.line.id, coords[0], "0", false) as GeoJSON.Feature);
  }

  if (coords.length >= 2) {
    const center = coords[0];
    const edge = coords[1];
    const radiusKm = distance(point(center), point(edge), { units: "kilometers" });

    // Calculate bearing to align circle vertex with edge point
    const bearingValue = bearing(point(center), point(edge));
    const azimuth = bearingValue < 0 ? bearingValue + 360 : bearingValue;

    // Display edge vertex
    display(createVertex(state.line.id, edge, "1", true) as GeoJSON.Feature);

    geojson.properties.meta = Constants.meta.FEATURE;
    geojson.properties.isRadiusLine = true;
    geojson.properties.isCircle = true;
    display(geojson);

    if (radiusKm > 0) {
      // Create circle rotated so a vertex aligns with the edge point
      const circlePolygon = createDisplayCircle(center, radiusKm, true, state.line.id, azimuth);
      display(circlePolygon);
    }
  }
};

export default CircleMode;
