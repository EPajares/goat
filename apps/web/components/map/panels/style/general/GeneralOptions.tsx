import { Box, Typography, useTheme } from "@mui/material";
import { useEffect, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

import { useTranslation } from "@/i18n/client";

import type { FeatureLayerProperties } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import SliderInput from "@/components/map/panels/common/SliderInput";

const GeneralOptions = ({
  layer,
  onStyleChange,
}: {
  layer: ProjectLayer;
  onStyleChange?: (newStyle: FeatureLayerProperties) => void;
}) => {
  const { map } = useMap();
  const [currentZoom, setCurrentZoom] = useState<number>(map?.getZoom() || 0);

  useEffect(() => {
    if (!map) return;

    const updateZoom = () => {
      const zoom = map.getZoom();
      setCurrentZoom(zoom);
    };

    map.on("move", updateZoom);
    updateZoom();

    return () => {
      map.off("move", updateZoom);
    };
  }, [map]);

  const { t } = useTranslation("common");
  const theme = useTheme();

  const [zoomLevels, setZoomLevels] = useState([
    layer.properties.min_zoom || 0,
    layer.properties.max_zoom || 22,
  ]);

  // Calculates percentage for label/arrow positioning inside padded box
  const getLeftPercent = (value: number, min: number, max: number) => ((value - min) / (max - min)) * 100;

  return (
    <>
      <Typography variant="body2" fontWeight="bold" color={theme.palette.text.secondary} sx={{ mb: 3 }}>
        {t("zoom_visibility")}
      </Typography>

      <Box sx={{ position: "relative", width: "100%", px: 4 }}>
        {/* Triangle + Label (in padded layer above slider) */}
        <Box sx={{ position: "absolute", top: 0, left: 0, right: 0, padding: "0 16px 0 16px" }}>
          <Box
            sx={{
              position: "relative",
              width: "100%",
            }}>
            <Box
              sx={{
                position: "absolute",
                top: "-12px",
                left: `${getLeftPercent(currentZoom, 0, 22)}%`,
                transform: "translateX(-50%)",
                pointerEvents: "none",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}>
              {/* Zoom value */}
              <Typography variant="caption" fontWeight="bold" sx={{ fontSize: 12, lineHeight: 1, mb: "2px" }}>
                {currentZoom.toFixed(1)}
              </Typography>

              {/* Downward-pointing triangle */}
              <Box
                sx={{
                  width: 0,
                  height: 0,
                  borderLeft: "6px solid transparent",
                  borderRight: "6px solid transparent",
                  borderTop: `6px solid ${theme.palette.primary.main}`,
                }}
              />
            </Box>
          </Box>
        </Box>

        {/* Full-width SliderInput without padding */}
        <SliderInput
          value={zoomLevels}
          isRange={true}
          min={0}
          max={22}
          step={1}
          onChange={(value) => {
            setZoomLevels(value as number[]);
          }}
          onChangeCommitted={(value) => {
            const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
            newStyle.min_zoom = (value as number[])[0];
            newStyle.max_zoom = (value as number[])[1];
            onStyleChange && onStyleChange(newStyle);
          }}
        />
      </Box>
    </>
  );
};

export default GeneralOptions;
