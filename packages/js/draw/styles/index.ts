/**
 * @p4b/draw - MapboxDraw styles
 */
import type { DrawStyle } from "../types";

/**
 * Default styles - red dashed lines with white-outlined vertices
 */
export const defaultDrawStyles: DrawStyle[] = [
  // Polygon fill
  {
    id: "gl-draw-polygon-fill-inactive",
    type: "fill",
    filter: ["all", ["==", "active", "false"], ["==", "$type", "Polygon"], ["!=", "mode", "static"]],
    paint: {
      "fill-color": "#ef4444",
      "fill-outline-color": "#ef4444",
      "fill-opacity": 0.1,
    },
  },
  {
    id: "gl-draw-polygon-fill-active",
    type: "fill",
    filter: ["all", ["==", "active", "true"], ["==", "$type", "Polygon"]],
    paint: {
      "fill-color": "#ef4444",
      "fill-outline-color": "#ef4444",
      "fill-opacity": 0.15,
    },
  },
  // Polygon stroke
  {
    id: "gl-draw-polygon-stroke-inactive",
    type: "line",
    filter: ["all", ["==", "active", "false"], ["==", "$type", "Polygon"], ["!=", "mode", "static"]],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": "#ef4444", "line-dasharray": [2, 2], "line-width": 2 },
  },
  {
    id: "gl-draw-polygon-stroke-active",
    type: "line",
    filter: ["all", ["==", "active", "true"], ["==", "$type", "Polygon"]],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": "#ef4444", "line-dasharray": [2, 2], "line-width": 3 },
  },
  // Line
  {
    id: "gl-draw-line-inactive",
    type: "line",
    filter: ["all", ["==", "active", "false"], ["==", "$type", "LineString"], ["!=", "mode", "static"]],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": "#ef4444", "line-dasharray": [2, 2], "line-width": 2 },
  },
  {
    id: "gl-draw-line-active",
    type: "line",
    filter: ["all", ["==", "$type", "LineString"], ["==", "active", "true"]],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": "#ef4444", "line-dasharray": [2, 2], "line-width": 3 },
  },
  // Vertex stroke (white background)
  {
    id: "gl-draw-polygon-and-line-vertex-stroke-inactive",
    type: "circle",
    filter: ["all", ["==", "meta", "vertex"], ["==", "$type", "Point"], ["!=", "mode", "static"]],
    paint: { "circle-radius": 8, "circle-color": "#fff" },
  },
  // Vertex fill (red inner)
  {
    id: "gl-draw-polygon-and-line-vertex-inactive",
    type: "circle",
    filter: ["all", ["==", "meta", "vertex"], ["==", "$type", "Point"], ["!=", "mode", "static"]],
    paint: { "circle-radius": 6, "circle-color": "#ef4444" },
  },
  // Midpoints (hidden)
  {
    id: "gl-draw-polygon-midpoint",
    type: "circle",
    filter: ["all", ["==", "$type", "Point"], ["==", "meta", "midpoint"]],
    paint: { "circle-radius": 0, "circle-color": "#ef4444", "circle-opacity": 0 },
  },
  // Point
  {
    id: "gl-draw-point-inactive",
    type: "circle",
    filter: ["all", ["==", "active", "false"], ["==", "$type", "Point"], ["==", "meta", "feature"]],
    paint: {
      "circle-radius": 5,
      "circle-color": "#fff",
      "circle-stroke-color": "#ef4444",
      "circle-stroke-width": 2,
    },
  },
  {
    id: "gl-draw-point-active",
    type: "circle",
    filter: ["all", ["==", "$type", "Point"], ["==", "meta", "feature"], ["==", "active", "true"]],
    paint: {
      "circle-radius": 7,
      "circle-color": "#fff",
      "circle-stroke-color": "#ef4444",
      "circle-stroke-width": 3,
    },
  },
];

/**
 * Create styles with a custom color
 */
export function createDrawStyles(color: string): DrawStyle[] {
  return defaultDrawStyles.map((style) => {
    const newStyle = { ...style, paint: { ...style.paint } };
    if (newStyle.paint) {
      for (const key of Object.keys(newStyle.paint)) {
        if (newStyle.paint[key] === "#ef4444") {
          newStyle.paint[key] = color;
        }
      }
    }
    return newStyle;
  });
}
