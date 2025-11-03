import MapboxDraw from "@mapbox/mapbox-gl-draw";
import type { Theme } from "@mui/material";
import { Box, useMediaQuery, useTheme } from "@mui/material";
import { useCallback, useMemo } from "react";
import { Map, type MapLayerMouseEvent, type MapRef, type ViewState } from "react-map-gl/maplibre";
import type { ViewStateChangeEvent } from "react-map-gl/maplibre";
import { v4 } from "uuid";

import { PATTERN_IMAGES } from "@/lib/constants/pattern-images";
import { setCurrentZoom, setHighlightedFeature, setPopupInfo } from "@/lib/store/map/slice";
import { addOrUpdateMarkerImages, addPatternImages } from "@/lib/transformers/map-image";
import createPulsingDot from "@/lib/utils/map/pulsing-dot-image";
import type { LayerInteractionFieldListContent } from "@/lib/validations/layer";
import {
  type FeatureLayerPointProperties,
  type Layer,
  layerInteractionContentType,
  layerInteractionType,
} from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";
import type { ScenarioFeatures } from "@/lib/validations/scenario";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import GeocoderLayer from "@/components/map/GeocoderLayer";
import Layers from "@/components/map/Layers";
import ScenarioLayer from "@/components/map/ScenarioLayer";
import ToolboxLayers from "@/components/map/ToolboxLayers";
import UserLocationLayer from "@/components/map/UserLocationLayer";
import { MapPopoverInfo } from "@/components/map/controls/LayerInfo";
import MapPopoverEditor from "@/components/map/controls/PopoverEditor";
import DrawControl from "@/components/map/controls/draw/Draw";

interface MapProps {
  mapRef: React.RefObject<MapRef> | null;
  initialViewState?: Partial<ViewState> & {
    bounds?: [number, number, number, number];
    fitBoundsOptions?: {
      offset?: [number, number];
      minZoom?: number;
      maxZoom?: number;
      padding?: number | { top: number; bottom: number; left: number; right: number };
    };
  };
  maxExtent?: [number, number, number, number];
  mapStyle: string;
  layers: ProjectLayer[] | Layer[];
  scenarioFeatures?: ScenarioFeatures;
  onMove?: ((e: ViewStateChangeEvent) => void | undefined) | undefined;
  onMoveEnd?: ((e: ViewStateChangeEvent) => void | undefined) | undefined;
  onClick?: (e: MapLayerMouseEvent) => void;
  onLoad?: () => void;
  dragRotate?: boolean | undefined;
  touchZoomRotate?: boolean | undefined;
  children?: React.ReactNode;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  containerSx?: any;
  isEditor?: boolean;
}

const MapViewer: React.FC<MapProps> = ({
  mapRef,
  initialViewState,
  mapStyle,
  layers,
  scenarioFeatures,
  onMove,
  onMoveEnd,
  onClick,
  onLoad,
  dragRotate = false,
  touchZoomRotate = false,
  maxExtent,
  children,
  containerSx,
  isEditor,
}) => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const isGetInfoActive = useAppSelector((state) => state.map.isMapGetInfoActive);
  const mapCursor = useAppSelector((state) => state.map.mapCursor);
  const highlightedFeature = useAppSelector((state) => state.map.highlightedFeature);
  const popupInfo = useAppSelector((state) => state.map.popupInfo);
  const popupEditor = useAppSelector((state) => state.map.popupEditor);

  const _selectedScenarioEditLayer = useAppSelector((state) => state.map.selectedScenarioLayer);
  const selectedScenarioEditLayer = useMemo(() => {
    return layers?.find((layer) => layer.id === _selectedScenarioEditLayer?.value);
  }, [_selectedScenarioEditLayer, layers]);

  const interactiveLayerIds = useMemo(() => layers?.map((layer) => layer.id.toString()), [layers]);

  const handlePopoverClose = () => {
    dispatch(setPopupInfo(undefined));
    dispatch(setHighlightedFeature(undefined));
  };

  const handleMapClick = (e: MapLayerMouseEvent) => {
    const { features } = e;
    const hiddenProperties = ["layer_id", "id", "h3_3", "h3_6"];

    if (features && features.length > 0 && isGetInfoActive) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let interactiveFeature = null as any;
      let interactiveLayer: Layer | ProjectLayer | undefined = undefined;

      // Find the first feature that has a click interaction by iterating through them
      for (const feature of features) {
        const layer = layers?.find(
          (l) =>
            l.id.toString() === feature.layer.id &&
            ![layerInteractionType.Enum.none, layerInteractionType.Enum.hover].includes(
              l.properties.interaction?.type
            )
        );

        if (layer) {
          interactiveFeature = feature;
          interactiveLayer = layer;
          break; // Found the topmost interactive feature, so we stop.
        }
      }

      if (interactiveFeature && interactiveLayer) {
        dispatch(setHighlightedFeature(interactiveFeature));

        const layerName = interactiveLayer.name;
        let lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat];
        if (interactiveFeature.geometry.type === "Point" && interactiveFeature.geometry.coordinates) {
          lngLat = [interactiveFeature.geometry.coordinates[0], interactiveFeature.geometry.coordinates[1]];
        }

        const interactionFieldLists = interactiveLayer.properties?.interaction?.content?.filter(
          (content) => content.type === layerInteractionContentType.Enum.field_list
        ) as LayerInteractionFieldListContent[] | undefined;

        const propertyLabels = interactionFieldLists?.reduce(
          (acc, content) => {
            content.attributes.forEach((attr) => {
              if (attr.label) {
                acc[attr.label] = interactiveFeature.properties[attr.name] || "";
              }
            });
            return acc;
          },
          {} as Record<string, string>
        );

        const properties =
          propertyLabels && Object.keys(propertyLabels).length > 0
            ? propertyLabels
            : interactiveFeature.properties;

        const jsonProperties = {};
        const primitiveProperties = {};
        if (properties) {
          for (const key in properties) {
            if (!hiddenProperties.includes(key)) {
              const value = properties[key];
              try {
                // Type assertion to satisfy JSON.parse
                const parsedValue = JSON.parse(value as string);
                if (typeof parsedValue === "object" && parsedValue !== null) {
                  jsonProperties[key] = parsedValue;
                } else {
                  throw new Error("Parsed value is not an object");
                }
              } catch (error) {
                primitiveProperties[key] = value;
              }
            }
          }
        }
        dispatch(
          setPopupInfo({
            lngLat,
            properties: primitiveProperties,
            jsonProperties: jsonProperties,
            title: layerName ?? "",
            onClose: handlePopoverClose,
          })
        );
      } else {
        // No interactive features were found in the click stack.
        dispatch(setHighlightedFeature(undefined));
        dispatch(setPopupInfo(undefined));
      }
    } else {
      // No features clicked or get info tool is not active.
      dispatch(setHighlightedFeature(undefined));
      dispatch(setPopupInfo(undefined));
    }

    if (onClick) {
      onClick(e);
    }
  };

  const handleMapOverImmediate = (e: MapLayerMouseEvent) => {
    // Extract features immediately
    const features = e.features;
    if (mapRef?.current) {
      // This is a hack to change the cursor to a pointer when hovering over a feature
      // It's not recommended to change the state of a component through internal methods
      // However, this is the only way to do it with the current version of react-map-gl
      // See https://github.com/visgl/react-map-gl/issues/579#issuecomment-1275163348
      const map = mapRef.current.getMap();
      if (mapCursor) {
        map.getCanvas().style.cursor = mapCursor;
      } else {
        map.getCanvas().style.cursor = features?.length ? "pointer" : "";
      }
    }
  };

  const handleMapLoad = useCallback(() => {
    if (mapRef?.current) {
      // get all icon layers and add icons to map using addOrUpdateMarkerImages method

      layers?.forEach((layer) => {
        if (layer.type === "feature" && layer.feature_layer_geometry_type === "point") {
          const pointFeatureProperties = layer.properties as FeatureLayerPointProperties;
          addOrUpdateMarkerImages(layer.id, pointFeatureProperties, mapRef.current);
        }
      });

      // load pattern images
      addPatternImages(PATTERN_IMAGES ?? [], mapRef.current);

      // load geolocation images
      const geolocationPulsingDot = createPulsingDot(mapRef.current);
      mapRef.current.addImage("geolocation-pulsing-dot", geolocationPulsingDot, { pixelRatio: 2 });

      // set current zoom
      const map = mapRef.current.getMap();
      const zoom = map.getZoom();
      dispatch(setCurrentZoom(zoom));
    }
    onLoad && onLoad();
  }, [layers, mapRef, onLoad, dispatch]);

  const _onMove = useCallback(
    (e: ViewStateChangeEvent) => {
      if (onMove) {
        onMove(e);
      }
      if (mapRef?.current) {
        const map = mapRef.current.getMap();
        const zoom = map.getZoom();
        dispatch(setCurrentZoom(zoom));
      }
    },
    [dispatch, onMove, mapRef]
  );

  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down("md"));

  return (
    <>
      <Box
        sx={{
          width: "100%",
          ".maplibregl-ctrl .maplibregl-ctrl-logo": {
            display: "none",
          },
          height: `100%`,
          ".maplibregl-popup-content": {
            padding: 0,
            borderRadius: "6px",
            background: theme.palette.background.paper,
          },
          ".maplibregl-popup-anchor-top .maplibregl-popup-tip, .maplibregl-popup-anchor-top-left .maplibregl-popup-tip, .maplibregl-popup-anchor-top-right .maplibregl-popup-tip":
            {
              borderBottomColor: theme.palette.background.paper,
            },
          ".maplibregl-popup-anchor-bottom .maplibregl-popup-tip, .maplibregl-popup-anchor-bottom-right .maplibregl-popup-tip, .maplibregl-popup-anchor-bottom-left .maplibregl-popup-tip":
            {
              borderTopColor: theme.palette.background.paper,
            },
          ".maplibregl-popup-anchor-left .maplibregl-popup-tip": {
            borderRightColor: theme.palette.background.paper,
          },
          ".maplibregl-popup-anchor-right .maplibregl-popup-tip": {
            borderLeftColor: theme.palette.background.paper,
          },
          ...containerSx,
        }}>
        <Map
          id="map"
          ref={mapRef}
          style={{ width: "100%", height: "100%" }}
          initialViewState={initialViewState}
          mapStyle={mapStyle}
          interactiveLayerIds={interactiveLayerIds}
          dragRotate={dragRotate}
          touchZoomRotate={touchZoomRotate}
          attributionControl={false}
          onMoveEnd={onMoveEnd}
          onClick={handleMapClick}
          onMouseMove={handleMapOverImmediate}
          onMove={_onMove}
          maxBounds={maxExtent}
          onLoad={handleMapLoad}>
          {isEditor && (
            <DrawControl
              position="top-right"
              displayControlsDefault={false}
              defaultMode={MapboxDraw.constants.modes.SIMPLE_SELECT}
            />
          )}
          <Layers
            layers={layers}
            highlightFeature={highlightedFeature}
            scenarioFeatures={scenarioFeatures}
            selectedScenarioLayer={selectedScenarioEditLayer as ProjectLayer}
          />
          <ScenarioLayer scenarioLayerData={scenarioFeatures} projectLayers={layers as ProjectLayer[]} />
          <GeocoderLayer />
          <UserLocationLayer />
          <ToolboxLayers />
          {!isMobile && popupInfo && <MapPopoverInfo key={highlightedFeature?.id ?? v4()} {...popupInfo} />}
          {!isMobile && popupEditor && isEditor && (
            <MapPopoverEditor
              key={popupEditor.feature?.id || popupEditor.feature?.properties?.id || v4()}
              {...popupEditor}
            />
          )}
        </Map>
        {children}
      </Box>
    </>
  );
};

export default MapViewer;
