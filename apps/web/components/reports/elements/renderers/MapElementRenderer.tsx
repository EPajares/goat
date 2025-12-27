"use client";

import { Box, Chip, CircularProgress, useTheme } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Map, MapProvider, type MapRef, type ViewStateChangeEvent } from "react-map-gl/maplibre";

import { PATTERN_IMAGES } from "@/lib/constants/pattern-images";
import type { AtlasPage } from "@/lib/print/atlas-utils";
import { addOrUpdateMarkerImages, addPatternImages } from "@/lib/transformers/map-image";
import type { FeatureLayerPointProperties } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";
import type { ReportElement } from "@/lib/validations/reportLayout";

import Layers from "@/components/map/Layers";

// Default basemap URL (OpenStreetMap style)
const DEFAULT_BASEMAP_URL = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

// Default view state (centered on Europe)
const DEFAULT_VIEW_STATE = {
  latitude: 48.13,
  longitude: 11.57,
  zoom: 10,
  bearing: 0,
  pitch: 0,
};

interface MapElementRendererProps {
  element: ReportElement;
  basemapUrl?: string; // Live from project (synced)
  layers?: ProjectLayer[]; // Live from project (synced)
  zoom?: number; // Page zoom level for scaling
  atlasPage?: AtlasPage | null; // Current atlas page (if atlas enabled)
  viewOnly?: boolean;
  onElementUpdate?: (elementId: string, config: Record<string, unknown>) => void;
  onNavigationModeChange?: (isNavigating: boolean) => void;
  onMapLoaded?: () => void; // Called when the map has finished loading
}

/**
 * Map element renderer for reports.
 *
 * - basemapUrl & layers: SYNCED live from project props
 * - viewState: SNAPSHOT stored in element.config (not synced), OR computed from atlas page bounds
 *
 * Atlas Mode:
 * - When atlasPage is provided, the map automatically fits to the feature bounds
 * - The map element can have atlas control settings that override default behavior
 *
 * Double-click to enter navigation mode (pan/zoom the map).
 * Press Escape to exit navigation mode.
 * View state changes are saved to element.config.
 */
const MapElementRenderer: React.FC<MapElementRendererProps> = ({
  element,
  basemapUrl,
  layers = [],
  zoom = 1,
  atlasPage,
  viewOnly = false,
  onElementUpdate,
  onNavigationModeChange,
  onMapLoaded,
}) => {
  const theme = useTheme();
  const mapRef = useRef<MapRef>(null);
  const [isNavigationMode, setIsNavigationMode] = useState(false);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Get snapshot view state from element config (NOT synced)
  // Use optional chaining directly to allow React to properly track changes
  const configViewState = element.config?.viewState;

  // Create a stable key for detecting config changes
  const configKey = JSON.stringify(configViewState);

  // Use live basemap URL from props, fallback to default
  const mapStyleUrl = basemapUrl || DEFAULT_BASEMAP_URL;

  // For the report map, ensure all layers are visible regardless of their visibility state in main map
  // Deep clone layers and set visibility to true for all
  const visibleLayers = useMemo(() => {
    return layers.map((layer) => ({
      ...layer,
      properties: {
        ...layer.properties,
        visibility: true,
      },
    }));
  }, [layers]);

  // Use controlled viewState to prevent map from changing when container resizes (page zoom)
  const [viewState, setViewState] = useState({
    latitude: configViewState?.latitude ?? DEFAULT_VIEW_STATE.latitude,
    longitude: configViewState?.longitude ?? DEFAULT_VIEW_STATE.longitude,
    zoom: configViewState?.zoom ?? DEFAULT_VIEW_STATE.zoom,
    bearing: configViewState?.bearing ?? DEFAULT_VIEW_STATE.bearing,
    pitch: configViewState?.pitch ?? DEFAULT_VIEW_STATE.pitch,
  });

  // Check if this map element is controlled by atlas
  const isAtlasControlled = element.config?.atlas?.enabled === true;

  // Update viewState when element config changes (e.g., from config panel or after reload)
  // This syncs bearing (rotation) and zoom set via the config panel
  // Only update from config if NOT in atlas mode (or atlas not controlling this map)
  useEffect(() => {
    if (atlasPage && isAtlasControlled) return; // Atlas mode handles viewState separately

    const configBearing = configViewState?.bearing ?? DEFAULT_VIEW_STATE.bearing;
    const configZoom = configViewState?.zoom ?? DEFAULT_VIEW_STATE.zoom;
    const configLat = configViewState?.latitude ?? DEFAULT_VIEW_STATE.latitude;
    const configLng = configViewState?.longitude ?? DEFAULT_VIEW_STATE.longitude;
    const configPitch = configViewState?.pitch ?? DEFAULT_VIEW_STATE.pitch;

    setViewState({
      latitude: configLat,
      longitude: configLng,
      zoom: configZoom,
      bearing: configBearing,
      pitch: configPitch,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configKey, atlasPage, isAtlasControlled]);

  // Atlas mode: fit map to atlas page bounds when atlas page changes
  // Only applies if this map element has atlas control enabled
  useEffect(() => {
    if (!atlasPage || !isAtlasControlled || !mapLoaded || !mapRef.current) return;

    const [west, south, east, north] = atlasPage.bounds;

    // Get bearing from config to preserve rotation during fitBounds
    const configBearing = configViewState?.bearing ?? DEFAULT_VIEW_STATE.bearing;

    // Fit the map to the atlas page bounds with some padding
    mapRef.current.fitBounds(
      [
        [west, south],
        [east, north],
      ],
      {
        padding: 20, // Add some padding around the feature
        duration: 0, // No animation for print preview
        maxZoom: 18, // Prevent excessive zoom for small features
        bearing: configBearing, // Preserve rotation from config
      }
    );
  }, [atlasPage, isAtlasControlled, mapLoaded, configViewState?.bearing]);

  // Handle double-click to enter navigation mode
  const handleDoubleClick = useCallback(
    (e: React.MouseEvent) => {
      if (viewOnly) return;
      e.stopPropagation();
      e.preventDefault();
      setIsNavigationMode(true);
    },
    [viewOnly]
  );

  // Handle escape key to exit navigation mode
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape" && isNavigationMode) {
        setIsNavigationMode(false);
        e.stopPropagation();
      }
    },
    [isNavigationMode]
  );

  // Save view state when map is moved
  const handleMoveEnd = useCallback(
    (e: ViewStateChangeEvent) => {
      if (!isNavigationMode || !onElementUpdate) return;

      const { latitude, longitude, zoom, bearing, pitch } = e.viewState;
      onElementUpdate(element.id, {
        ...element.config,
        viewState: { latitude, longitude, zoom, bearing, pitch },
      });
    },
    [element.id, element.config, isNavigationMode, onElementUpdate]
  );

  // Handle blur to exit navigation mode
  const handleBlur = useCallback(() => {
    if (isNavigationMode) {
      setIsNavigationMode(false);
    }
  }, [isNavigationMode]);

  // Notify parent when navigation mode changes
  useEffect(() => {
    onNavigationModeChange?.(isNavigationMode);
  }, [isNavigationMode, onNavigationModeChange]);

  // Handle map load - load marker and pattern images for layers
  const handleMapLoad = useCallback(() => {
    if (mapRef.current) {
      // Load marker images for point layers with custom markers
      visibleLayers.forEach((layer) => {
        if (layer.type === "feature" && layer.feature_layer_geometry_type === "point") {
          const pointFeatureProperties = layer.properties as FeatureLayerPointProperties;
          addOrUpdateMarkerImages(layer.id, pointFeatureProperties, mapRef.current);
        }
      });

      // Load pattern images
      addPatternImages(PATTERN_IMAGES ?? [], mapRef.current);
    }
    setMapLoaded(true);
  }, [visibleLayers]);

  // Track if we've already notified parent that map is ready
  const hasNotifiedReady = useRef(false);

  // Handle map idle - called when the map has finished rendering
  // This is more reliable for print than onLoad which fires when style is loaded
  const handleMapIdle = useCallback(() => {
    // Only notify once when the map first becomes idle after loading
    if (mapLoaded && !hasNotifiedReady.current) {
      hasNotifiedReady.current = true;
      onMapLoaded?.();
    }
  }, [mapLoaded, onMapLoaded]);

  // Calculate inverse scale to render map at native size
  // The parent container is already scaled by zoom, so we render the map
  // at 1/zoom size and scale it back up to fill the container
  const inverseZoom = 1 / zoom;

  return (
    <MapProvider>
      <Box
        tabIndex={0}
        onDoubleClick={handleDoubleClick}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        sx={{
          width: "100%",
          height: "100%",
          position: "relative",
          cursor: isNavigationMode ? "grab" : "default",
          outline: "none",
          pointerEvents: "auto",
          overflow: "hidden",
        }}>
        {/* Map container with inverse scaling to maintain consistent appearance */}
        <Box
          sx={{
            width: `${100 * inverseZoom}%`,
            height: `${100 * inverseZoom}%`,
            transform: `scale(${zoom})`,
            transformOrigin: "top left",
            position: "relative",
            "& .maplibregl-ctrl-attrib": {
              display: "none",
            },
            "& .maplibregl-ctrl-logo": {
              display: "none",
            },
          }}>
          {/* Loading overlay */}
          {!mapLoaded && (
            <Box
              sx={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#f5f5f5",
                zIndex: 5,
              }}>
              <CircularProgress size={24} />
            </Box>
          )}

          <Map
            ref={mapRef}
            style={{ width: "100%", height: "100%" }}
            {...viewState}
            onMove={(e) => setViewState(e.viewState)}
            mapStyle={mapStyleUrl}
            attributionControl={false}
            dragPan={isNavigationMode}
            scrollZoom={isNavigationMode}
            dragRotate={false}
            touchZoomRotate={isNavigationMode}
            doubleClickZoom={false}
            onMoveEnd={handleMoveEnd}
            onLoad={handleMapLoad}
            onIdle={handleMapIdle}
            interactive={isNavigationMode}>
            {visibleLayers.length > 0 && <Layers layers={visibleLayers} />}
          </Map>
        </Box>

        {/* Navigation mode indicator */}
        {!viewOnly && mapLoaded && (
          <Box
            sx={{
              position: "absolute",
              bottom: 8,
              left: 8,
              zIndex: 10,
            }}>
            {isNavigationMode ? (
              <Chip
                size="small"
                label="Press ESC to exit"
                sx={{
                  backgroundColor: theme.palette.primary.main,
                  color: "white",
                  fontSize: "0.7rem",
                  height: 20,
                }}
              />
            ) : (
              <Chip
                size="small"
                label="Double-click to navigate"
                sx={{
                  backgroundColor: "rgba(0,0,0,0.6)",
                  color: "white",
                  fontSize: "0.7rem",
                  height: 20,
                }}
              />
            )}
          </Box>
        )}
      </Box>
    </MapProvider>
  );
};

export default MapElementRenderer;
