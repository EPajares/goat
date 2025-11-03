import type { MapRef } from "react-map-gl/maplibre";

import type { PatternImage } from "@/lib/constants/pattern-images";
import type { FeatureLayerPointProperties } from "@/lib/validations/layer";

// Image prefix for marker images is needed to avoid
// name conflicts with other images from mapbox basemaps
export const PATTERN_IMAGE_PREFIX = "goat-pattern-";

/**
 * Load image from url and adds or updates the map with the image
 * @param map MapRef
 * @param url string
 * @param marker_name string
 * @param width number
 * @param height number
 * @param sdf boolean
 * @returns void
 */
export const loadImage = (
  map: MapRef,
  url: string,
  marker_name: string,
  sdf?: boolean,
  targetWidth = 200,   // default
  targetHeight = 200   // default
) => {
  const addOrUpdateImage = (
    image:
      | HTMLImageElement
      | { width: number; height: number; data: Uint8Array | Uint8ClampedArray }
      | ImageData
      | ImageBitmap
  ) => {
    if (map?.hasImage(marker_name)) {
      map.removeImage(marker_name);
    }
    map.addImage(marker_name, image, { sdf: sdf ?? true });
  };

  const rasterizeToCanvas = (
    img: HTMLImageElement,
    targetW: number,
    targetH: number
  ) => {
    const pixelRatio = window.devicePixelRatio || 1;
    const canvas = document.createElement("canvas");
    canvas.width = targetW * pixelRatio;
    canvas.height = targetH * pixelRatio;

    const context = canvas.getContext("2d");
    if (context) {
      context.scale(pixelRatio, pixelRatio);
      context.imageSmoothingEnabled = true;
      context.drawImage(img, 0, 0, targetW, targetH);

      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      addOrUpdateImage({
        width: canvas.width,
        height: canvas.height,
        data: new Uint8Array(imageData.data.buffer),
      });
    }
  };

  // Create an Image object for all formats the browser supports
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.src = url;
  img.onload = () => {
    rasterizeToCanvas(img, targetWidth, targetHeight);
  };
  img.onerror = (err) => console.error(`Failed to load image: ${url}`, err);
};

/**
 * Add or update marker images on the map
 * @param properties FeatureLayerPointProperties
 * @param map MapRef
 * @returns void
 */
export function addOrUpdateMarkerImages(
  id: number,
  properties: FeatureLayerPointProperties,
  map: MapRef | null
) {
  if (map && properties.custom_marker) {
    const markers = [properties.marker];
    properties.marker_mapping?.forEach((markerMap) => {
      if (markerMap && markerMap[1]) markers.push(markerMap[1]);
    });
    markers.forEach((marker) => {
      if (marker && marker.url && marker.name) {
        const name = `${id}-${marker.name}`;
        const sdf = marker.source === "library" ? true : false;
        loadImage(map, marker.url, name, sdf);
      }
    });
  }
}

/**
 * Add pattern images on the map
 * @param patterns PatternImage[]
 * @param map MapRef
 */
export function addPatternImages(patterns: PatternImage[], map: MapRef | null) {
  if (map && patterns) {
    patterns.forEach((pattern) => {
      const name = `${PATTERN_IMAGE_PREFIX}${pattern.name}`;
      loadImage(map, pattern.url, name, false, pattern.width, pattern.height);
    });
  }
}
