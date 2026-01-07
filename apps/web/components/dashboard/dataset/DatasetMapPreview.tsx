import { Box, Paper } from "@mui/material";
import bbox from "@turf/bbox";
import "maplibre-gl/dist/maplibre-gl.css";
import React, { useMemo, useRef, useState } from "react";
import type { MapRef } from "react-map-gl/maplibre";
import { MapProvider } from "react-map-gl/maplibre";

import { MAPTILER_KEY } from "@/lib/constants";
import { DrawProvider } from "@/lib/providers/DrawProvider";
import { globalExtent, wktToGeoJSON } from "@/lib/utils/map/wkt";
import type { Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import MapViewer from "@/components/map/MapViewer";
import { Legend } from "@/components/map/controls/Legend";
import { Recenter } from "@/components/map/controls/Recenter";

interface DatasetMapPreviewProps {
  dataset: Layer;
}

const DatasetMapPreview: React.FC<DatasetMapPreviewProps> = ({ dataset }) => {
  const mapRef = useRef<MapRef | null>(null);
  const geojson = wktToGeoJSON(dataset.extent || globalExtent);
  const boundingBox = bbox(geojson);
  const [initialViewState, setInitialViewState] = useState({});

  const [currentViewState, setCurrentViewState] = useState({});
  const hasMoved = useMemo(() => {
    return (
      Object.keys(currentViewState).length &&
      Object.keys(initialViewState).length &&
      JSON.stringify(currentViewState) !== JSON.stringify(initialViewState)
    );
  }, [currentViewState, initialViewState]);

  // Ensure the layer has visibility enabled for preview
  const layerWithVisibility = useMemo(() => {
    return {
      ...dataset,
      properties: {
        ...dataset.properties,
        visibility: true,
      },
    };
  }, [dataset]);

  return (
    <>
      <DrawProvider>
        <MapProvider>
          <MapViewer
            mapRef={mapRef}
            layers={[layerWithVisibility]}
            initialViewState={{
              bounds: boundingBox as [number, number, number, number],
              fitBoundsOptions: { padding: 10 },
            }}
            onMove={(e) => {
              setCurrentViewState({
                longitude: e.viewState.longitude.toFixed(4),
                latitude: e.viewState.latitude.toFixed(4),
              });
            }}
            onLoad={() => {
              const center = mapRef.current?.getMap().getCenter();
              if (center) {
                setInitialViewState({
                  longitude: center.lng.toFixed(4),
                  latitude: center.lat.toFixed(4),
                });
              }
            }}
            mapStyle={`https://api.maptiler.com/maps/dataviz-light/style.json?key=${MAPTILER_KEY}`}
            dragRotate={false}
            touchZoomRotate={false}
            containerSx={{
              position: "relative",
              display: "flex",
              height: `calc(100vh - 380px)`,
              overflow: "hidden",
            }}>
            {!!hasMoved && (
              <Box
                sx={{
                  position: "absolute",
                  left: 15,
                  top: 5,
                }}>
                <Recenter initialExtent={dataset.extent} />
              </Box>
            )}

            <Box>
              <Paper
                sx={{
                  position: "absolute",
                  top: 10,
                  right: 10,
                  px: 4,
                  maxHeight: "300px",
                  minWidth: "220px",
                  overflow: "auto",
                }}>
                <Legend
                  layers={[layerWithVisibility] as unknown as ProjectLayer[]}
                  hideZoomLevel
                  hideLayerName
                />
              </Paper>
            </Box>
          </MapViewer>
        </MapProvider>
      </DrawProvider>
    </>
  );
};

export default DatasetMapPreview;
