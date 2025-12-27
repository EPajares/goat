/**
 * @p4b/draw - Patched simple select mode
 *
 * Extends the default simple_select mode to:
 * - Render great circle features as geodesic arcs
 * - Render circle features from radius lines
 * - Redirect clicks on circle polygons to select the parent radius line
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";

import { regenerateCircleFromLine } from "../helpers";
import { GREAT_CIRCLE_PROPERTY, generateGreatCirclePath } from "./great-circle";

const SimpleSelect = MapboxDraw.modes.simple_select;
const Constants = MapboxDraw.constants;

const USER_GREAT_CIRCLE_PROPERTY = `user_${GREAT_CIRCLE_PROPERTY}`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function patchSimpleSelect(OriginalSimpleSelect: any) {
  const SimpleSelectPatched = { ...OriginalSimpleSelect };

  SimpleSelectPatched.toDisplayFeatures = function (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    geojson: any,
    display: (feature: GeoJSON.Feature) => void
  ) {
    const displayGeodesic = (feat: GeoJSON.Feature) => {
      const isMeta = feat.properties?.meta === "vertex" || feat.properties?.meta === "midpoint";
      if (isMeta) {
        display(feat);
        return;
      }

      // Handle circle
      const isRadiusLine = feat.properties?.isRadiusLine || feat.properties?.user_isRadiusLine;
      const isCircle = feat.properties?.isCircle || feat.properties?.user_isCircle;

      if ((isRadiusLine || isCircle) && feat.geometry.type === "LineString") {
        const coords = (feat.geometry as GeoJSON.LineString).coordinates;
        if (coords.length === 2) {
          display(feat);
          const featureId = feat.properties?.id || feat.id;
          const circlePolygon = regenerateCircleFromLine(feat, {
            meta: "feature",
            parent: featureId,
            parentRadiusLine: featureId,
            id: `${featureId}-circle-display`,
            active: feat.properties?.active,
            isCircle: true,
            isDisplayOnly: true,
          });
          if (circlePolygon) display(circlePolygon);
          return;
        }
      }

      // Don't render stored circle polygons directly
      if (
        feat.geometry.type === "Polygon" &&
        (feat.properties?.isCircle ||
          feat.properties?.user_isCircle ||
          feat.properties?.isDisplayOnly ||
          feat.properties?.user_isDisplayOnly)
      ) {
        return;
      }

      // Handle great circle
      const isGreatCircle =
        feat.properties &&
        (feat.properties[GREAT_CIRCLE_PROPERTY] || feat.properties[USER_GREAT_CIRCLE_PROPERTY]);

      const parentId = feat.properties?.parent;
      let parentIsGreatCircle = false;
      if (parentId && this._ctx?.store) {
        const parentFeature = this._ctx.store.get(parentId);
        if (parentFeature) {
          parentIsGreatCircle = parentFeature.properties?.[GREAT_CIRCLE_PROPERTY] === true;
        }
      }

      // Hide midpoints for great circle features
      if (parentIsGreatCircle && feat.properties?.meta === "midpoint") {
        return;
      }

      if (
        isGreatCircle &&
        feat.geometry.type === "LineString" &&
        (feat.geometry as GeoJSON.LineString).coordinates.length >= 2
      ) {
        const originalCoords = (feat.geometry as GeoJSON.LineString).coordinates as [number, number][];
        const greatCircleCoords = generateGreatCirclePath(originalCoords);
        display({
          ...feat,
          geometry: { ...feat.geometry, coordinates: greatCircleCoords },
        } as GeoJSON.Feature);
      } else {
        display(feat);
      }
    };

    OriginalSimpleSelect.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };

  // Redirect clicks on circle polygons to select parent radius line
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  SimpleSelectPatched.onClick = function (this: any, state: any, e: any) {
    const featureTarget = e.featureTarget;
    if (featureTarget) {
      const props = featureTarget.properties || {};

      if (props.isDisplayOnly || props.parentRadiusLine) {
        const parentId = props.parentRadiusLine || props.parent;
        if (parentId && this._ctx?.store) {
          const actualParentId = String(parentId).replace("-circle-display", "");
          const parentFeature = this._ctx.store.get(actualParentId);

          if (parentFeature) {
            this.setSelected([actualParentId]);
            return this.changeMode(Constants.modes.DIRECT_SELECT, {
              featureId: actualParentId,
            });
          }
        }
      }
    }

    return OriginalSimpleSelect.onClick.call(this, state, e);
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  SimpleSelectPatched.onTap = function (this: any, state: any, e: any) {
    const featureTarget = e.featureTarget;
    if (featureTarget) {
      const props = featureTarget.properties || {};

      if (props.isDisplayOnly || props.parentRadiusLine) {
        const parentId = props.parentRadiusLine || props.parent;
        if (parentId && this._ctx?.store) {
          const actualParentId = String(parentId).replace("-circle-display", "");
          const parentFeature = this._ctx.store.get(actualParentId);

          if (parentFeature) {
            this.setSelected([actualParentId]);
            return this.changeMode(Constants.modes.DIRECT_SELECT, {
              featureId: actualParentId,
            });
          }
        }
      }
    }

    return OriginalSimpleSelect.onTap.call(this, state, e);
  };

  return SimpleSelectPatched;
}

export default patchSimpleSelect(SimpleSelect);
