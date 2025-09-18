// src/components/MapViewer.js
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import React, { useEffect, useRef } from "react";

/* -----------------------
   Utility Functions
------------------------ */

function looksLikeWorld(ring) {
  if (!ring || ring.length < 4) return false;
  const xs = ring.map((p) => p[0]);
  const ys = ring.map((p) => p[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return minX <= -179.9 && maxX >= 179.9 && minY <= -89.9 && maxY >= 89.9;
}

function getCoords(geometry, { stripWorldMask = true } = {}) {
  if (!geometry) return [];
  switch (geometry.type) {
    case "Point":
      return [geometry.coordinates];
    case "LineString":
    case "MultiPoint":
      return geometry.coordinates;
    case "Polygon": {
      if (stripWorldMask && looksLikeWorld(geometry.coordinates[0])) {
        return geometry.coordinates.slice(1).flat();
      }
      return geometry.coordinates.flat();
    }
    case "MultiPolygon": {
      return geometry.coordinates.flatMap((poly) => {
        if (stripWorldMask && looksLikeWorld(poly[0])) {
          return poly.slice(1).flat();
        }
        return poly.flat();
      });
    }
    case "GeometryCollection":
      return geometry.geometries.flatMap((g) => getCoords(g, { stripWorldMask }));
    default:
      return [];
  }
}

function getBoundingBox(geojson) {
  if (!geojson?.features?.length) return null;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  geojson.features.forEach((feature) => {
    const coords = getCoords(feature.geometry, { stripWorldMask: true });
    coords.forEach(([x, y]) => {
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    });
  });
  if (minX === Infinity) return null;
  return [
    [minX, minY],
    [maxX, maxY],
  ];
}

/* -----------------------
   MapViewer Component
------------------------ */

const MapViewer = ({ geojsonUrls = [], styleOptions, legendItems = [] }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  // Initialize map
  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [0, 0],
      zoom: 2,
    });

    map.scrollZoom.disable();
    map.dragRotate.disable();
    map.touchZoomRotate.disable();
    map.dragPan.disable();
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;
  }, []);

  // Load GeoJSONs
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.on("load", () => {
      geojsonUrls.forEach((url, idx) => {
        const sourceId = `geojson-${idx}`;
        const layerId = `geojson-layer-${idx}`;

        if (!map.getSource(sourceId)) {
          map.addSource(sourceId, { type: "geojson", data: url });
        }
        if (!map.getLayer(layerId)) {
          map.addLayer({
            id: layerId,
            type: "fill",
            source: sourceId,
            paint: {
              "fill-color": styleOptions?.fillColor || "rgba(0, 123, 255, 0.4)",
              "fill-outline-color": styleOptions?.outlineColor || "#0055aa",
              "fill-opacity": typeof styleOptions?.fillOpacity === "number" ? styleOptions.fillOpacity : 0.5,
            },
          });
        }
      });

      Promise.all(
        geojsonUrls.map((url) =>
          fetch(url)
            .then((r) => r.json())
            .catch(() => null)
        )
      ).then((geojsons) => {
        const features = geojsons.filter(Boolean).flatMap((f) => f.features);
        if (features.length > 0) {
          const bbox = getBoundingBox({
            type: "FeatureCollection",
            features,
          });
          if (bbox) {
            map.fitBounds(bbox, { padding: 40, animate: false });
          }
        }
      });
    });
  }, [geojsonUrls, styleOptions]);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "500px",
        border: "1px solid #ccc",
      }}>
      <div ref={mapContainerRef} style={{ width: "100%", height: "100%" }} />

      {legendItems.length > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: "10px",
            left: "10px",
            background: "rgba(255, 255, 255, 0.9)",
            padding: "8px 12px",
            borderRadius: "6px",
            boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
            fontSize: "14px",
          }}>
          {legendItems.map((item, idx) => (
            <div key={idx} style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
              <div
                style={{
                  width: "16px",
                  height: "16px",
                  backgroundColor: item.color,
                  border: "1px solid #444",
                  marginRight: "6px",
                }}
              />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MapViewer;
