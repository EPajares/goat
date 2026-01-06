"use client";

import { Box, Typography } from "@mui/material";
import React, { useMemo } from "react";

import type { ReportElement } from "@/lib/validations/reportLayout";

import {
  type ScalebarElementConfig,
  type ScalebarUnit,
  getUnitAbbreviation,
} from "@/components/reports/elements/config/ScalebarElementConfig";

interface ScalebarElementRendererProps {
  element: ReportElement;
  mapElements?: ReportElement[];
  zoom?: number;
}

/**
 * Convert meters to the target unit
 */
const metersToUnit = (meters: number, unit: ScalebarUnit): number => {
  switch (unit) {
    case "kilometers":
      return meters / 1000;
    case "meters":
      return meters;
    case "feet":
      return meters * 3.28084;
    case "yards":
      return meters * 1.09361;
    case "miles":
      return meters / 1609.344;
    case "nautical_miles":
      return meters / 1852;
    case "centimeters":
      return meters * 100;
    case "millimeters":
      return meters * 1000;
    case "inches":
      return meters * 39.3701;
    case "map_units":
    default:
      return meters;
  }
};

/**
 * Get nice round numbers for scale bars
 */
const getNiceNumber = (value: number): number => {
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const normalized = value / magnitude;

  if (normalized <= 1) return magnitude;
  if (normalized <= 2) return 2 * magnitude;
  if (normalized <= 5) return 5 * magnitude;
  return 10 * magnitude;
};

/**
 * Calculate scale bar parameters based on map scale
 */
const calculateScaleBarParams = (
  mapScale: number,
  unit: ScalebarUnit,
  segmentsRight: number,
  _segmentsLeft: number
) => {
  // mapScale is meters per pixel at the map center
  // For a typical scalebar width of ~150px, we want readable values

  const targetWidthPx = 150;
  const totalMeters = mapScale * targetWidthPx;
  const totalUnits = metersToUnit(totalMeters, unit);

  // Get a nice round total value
  const niceTotal = getNiceNumber(totalUnits);

  // Calculate segment value
  const totalSegments = Math.max(1, segmentsRight);
  const segmentValue = niceTotal / totalSegments;

  return {
    totalValue: niceTotal,
    segmentValue,
    totalSegments,
  };
};

/**
 * Render Single Box style scalebar
 */
const SingleBoxScalebar: React.FC<{
  totalSegments: number;
  segmentsLeft: number;
  segmentValue: number;
  labelUnit: string;
  labelMultiplier: number;
  height: number;
}> = ({ totalSegments, segmentsLeft, segmentValue, labelUnit, labelMultiplier, height }) => {
  const allSegments = segmentsLeft + totalSegments;

  return (
    <Box sx={{ width: "100%", display: "flex", flexDirection: "column", gap: 0.5 }}>
      {/* Labels */}
      <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
        {Array.from({ length: allSegments + 1 }, (_, i) => {
          const value = (i - segmentsLeft) * segmentValue * labelMultiplier;
          const isLast = i === allSegments;
          return (
            <Typography
              key={i}
              variant="caption"
              sx={{ fontSize: "0.65rem", minWidth: isLast ? "auto" : 0, textAlign: "center" }}>
              {value}
              {isLast && labelUnit ? ` ${labelUnit}` : ""}
            </Typography>
          );
        })}
      </Box>
      {/* Bar */}
      <Box sx={{ display: "flex", height: `${height}px`, border: "1px solid #000" }}>
        {Array.from({ length: allSegments }, (_, i) => (
          <Box
            key={i}
            sx={{
              flex: 1,
              backgroundColor: i % 2 === 0 ? "#000" : "#fff",
            }}
          />
        ))}
      </Box>
    </Box>
  );
};

/**
 * Render Double Box style scalebar
 */
const DoubleBoxScalebar: React.FC<{
  totalSegments: number;
  segmentsLeft: number;
  segmentValue: number;
  labelUnit: string;
  labelMultiplier: number;
  height: number;
}> = ({ totalSegments, segmentsLeft, segmentValue, labelUnit, labelMultiplier, height }) => {
  const allSegments = segmentsLeft + totalSegments;
  const halfHeight = height / 2;

  return (
    <Box sx={{ width: "100%", display: "flex", flexDirection: "column", gap: 0.5 }}>
      {/* Labels */}
      <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
        {Array.from({ length: allSegments + 1 }, (_, i) => {
          const value = (i - segmentsLeft) * segmentValue * labelMultiplier;
          const isLast = i === allSegments;
          return (
            <Typography
              key={i}
              variant="caption"
              sx={{ fontSize: "0.65rem", minWidth: isLast ? "auto" : 0, textAlign: "center" }}>
              {value}
              {isLast && labelUnit ? ` ${labelUnit}` : ""}
            </Typography>
          );
        })}
      </Box>
      {/* Double Bar */}
      <Box sx={{ display: "flex", flexDirection: "column", border: "1px solid #000" }}>
        {/* Top row */}
        <Box sx={{ display: "flex", height: `${halfHeight}px` }}>
          {Array.from({ length: allSegments }, (_, i) => (
            <Box
              key={i}
              sx={{
                flex: 1,
                backgroundColor: i % 2 === 0 ? "#000" : "#fff",
              }}
            />
          ))}
        </Box>
        {/* Bottom row (inverted) */}
        <Box sx={{ display: "flex", height: `${halfHeight}px` }}>
          {Array.from({ length: allSegments }, (_, i) => (
            <Box
              key={i}
              sx={{
                flex: 1,
                backgroundColor: i % 2 === 0 ? "#fff" : "#000",
              }}
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
};

/**
 * Render Line Ticks style scalebar
 */
const LineTicksScalebar: React.FC<{
  totalSegments: number;
  segmentsLeft: number;
  segmentValue: number;
  labelUnit: string;
  labelMultiplier: number;
  height: number;
  tickPosition: "middle" | "down" | "up";
}> = ({ totalSegments, segmentsLeft, segmentValue, labelUnit, labelMultiplier, height, tickPosition }) => {
  const allSegments = segmentsLeft + totalSegments;

  return (
    <Box sx={{ width: "100%", display: "flex", flexDirection: "column", gap: 0.5 }}>
      {/* Labels */}
      <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
        {Array.from({ length: allSegments + 1 }, (_, i) => {
          const value = (i - segmentsLeft) * segmentValue * labelMultiplier;
          const isLast = i === allSegments;
          return (
            <Typography
              key={i}
              variant="caption"
              sx={{ fontSize: "0.65rem", minWidth: isLast ? "auto" : 0, textAlign: "center" }}>
              {value}
              {isLast && labelUnit ? ` ${labelUnit}` : ""}
            </Typography>
          );
        })}
      </Box>
      {/* Line with ticks */}
      <Box sx={{ position: "relative", height: `${height}px`, width: "100%" }}>
        {/* Horizontal line */}
        <Box
          sx={{
            position: "absolute",
            left: 0,
            right: 0,
            top: tickPosition === "up" ? `${height - 1}px` : tickPosition === "down" ? 0 : "50%",
            height: "1px",
            backgroundColor: "#000",
          }}
        />
        {/* Ticks */}
        {Array.from({ length: allSegments + 1 }, (_, i) => (
          <Box
            key={i}
            sx={{
              position: "absolute",
              left: `${(i / allSegments) * 100}%`,
              top: tickPosition === "up" ? 0 : tickPosition === "down" ? 0 : 0,
              bottom: tickPosition === "up" ? 0 : tickPosition === "down" ? 0 : 0,
              width: "1px",
              height: "100%",
              backgroundColor: "#000",
              transform: "translateX(-50%)",
            }}
          />
        ))}
      </Box>
    </Box>
  );
};

/**
 * Render Stepped Line style scalebar
 */
const SteppedLineScalebar: React.FC<{
  totalSegments: number;
  segmentsLeft: number;
  segmentValue: number;
  labelUnit: string;
  labelMultiplier: number;
  height: number;
}> = ({ totalSegments, segmentsLeft, segmentValue, labelUnit, labelMultiplier, height }) => {
  const allSegments = segmentsLeft + totalSegments;

  return (
    <Box sx={{ width: "100%", display: "flex", flexDirection: "column", gap: 0.5 }}>
      {/* Labels */}
      <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
        {Array.from({ length: allSegments + 1 }, (_, i) => {
          const value = (i - segmentsLeft) * segmentValue * labelMultiplier;
          const isLast = i === allSegments;
          return (
            <Typography
              key={i}
              variant="caption"
              sx={{ fontSize: "0.65rem", minWidth: isLast ? "auto" : 0, textAlign: "center" }}>
              {value}
              {isLast && labelUnit ? ` ${labelUnit}` : ""}
            </Typography>
          );
        })}
      </Box>
      {/* Stepped line */}
      <Box sx={{ position: "relative", height: `${height}px`, width: "100%" }}>
        {Array.from({ length: allSegments }, (_, i) => {
          const segmentWidth = 100 / allSegments;
          const isEven = i % 2 === 0;
          return (
            <React.Fragment key={i}>
              {/* Horizontal segment */}
              <Box
                sx={{
                  position: "absolute",
                  left: `${i * segmentWidth}%`,
                  width: `${segmentWidth}%`,
                  top: isEven ? 0 : `${height - 1}px`,
                  height: "1px",
                  backgroundColor: "#000",
                }}
              />
              {/* Vertical connector */}
              {i > 0 && (
                <Box
                  sx={{
                    position: "absolute",
                    left: `${i * segmentWidth}%`,
                    top: 0,
                    width: "1px",
                    height: `${height}px`,
                    backgroundColor: "#000",
                    transform: "translateX(-50%)",
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
        {/* End ticks */}
        <Box
          sx={{
            position: "absolute",
            left: 0,
            top: 0,
            width: "1px",
            height: `${height}px`,
            backgroundColor: "#000",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            right: 0,
            top: 0,
            width: "1px",
            height: `${height}px`,
            backgroundColor: "#000",
          }}
        />
      </Box>
    </Box>
  );
};

/**
 * Render Hollow style scalebar
 */
const HollowScalebar: React.FC<{
  totalSegments: number;
  segmentsLeft: number;
  segmentValue: number;
  labelUnit: string;
  labelMultiplier: number;
  height: number;
}> = ({ totalSegments, segmentsLeft, segmentValue, labelUnit, labelMultiplier, height }) => {
  const allSegments = segmentsLeft + totalSegments;

  return (
    <Box sx={{ width: "100%", display: "flex", flexDirection: "column", gap: 0.5 }}>
      {/* Labels */}
      <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
        {Array.from({ length: allSegments + 1 }, (_, i) => {
          const value = (i - segmentsLeft) * segmentValue * labelMultiplier;
          const isLast = i === allSegments;
          return (
            <Typography
              key={i}
              variant="caption"
              sx={{ fontSize: "0.65rem", minWidth: isLast ? "auto" : 0, textAlign: "center" }}>
              {value}
              {isLast && labelUnit ? ` ${labelUnit}` : ""}
            </Typography>
          );
        })}
      </Box>
      {/* Hollow bar */}
      <Box
        sx={{
          display: "flex",
          height: `${height}px`,
          border: "1px solid #000",
          backgroundColor: "#fff",
        }}>
        {Array.from({ length: allSegments }, (_, i) => (
          <Box
            key={i}
            sx={{
              flex: 1,
              borderRight: i < allSegments - 1 ? "1px solid #000" : "none",
            }}
          />
        ))}
      </Box>
    </Box>
  );
};

/**
 * Render Numeric style scalebar (just text showing scale ratio)
 */
const NumericScalebar: React.FC<{
  mapScale: number;
}> = ({ mapScale }) => {
  // Calculate scale ratio (1:X)
  // mapScale is meters per pixel, we need to convert to a ratio
  // Assuming screen DPI of 96, 1 inch = 25.4mm = ~2.54cm
  const inchesPerPixel = 1 / 96;
  const metersPerInch = mapScale * 96;
  // Convert to same units (meters to meters for 1:X ratio)
  const scaleRatio = Math.round(metersPerInch / (inchesPerPixel * 0.0254));

  // Format nicely
  const formatScale = (ratio: number): string => {
    if (ratio >= 1000000) {
      return `1:${(ratio / 1000000).toFixed(1)}M`;
    }
    if (ratio >= 1000) {
      return `1:${(ratio / 1000).toFixed(0)}K`;
    }
    return `1:${ratio}`;
  };

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}>
      <Typography variant="body2" sx={{ fontWeight: 500 }}>
        {formatScale(scaleRatio)}
      </Typography>
    </Box>
  );
};

/**
 * Scalebar Element Renderer for print reports
 *
 * Renders a scalebar that reflects the connected map's scale.
 * Supports multiple styles: Single Box, Double Box, Line Ticks, Stepped Line, Hollow, Numeric
 */
const ScalebarElementRenderer: React.FC<ScalebarElementRendererProps> = ({
  element,
  mapElements = [],
  zoom = 1,
}) => {
  // Extract config
  const config = (element.config || {}) as ScalebarElementConfig;
  const mapElementId = config.mapElementId;
  const style = config.style ?? "single_box";
  const unit = config.unit ?? "kilometers";
  const labelMultiplier = config.labelMultiplier ?? 1;
  const labelUnit = config.labelUnit ?? getUnitAbbreviation(unit);
  const height = config.height ?? 8;
  const segmentsLeft = config.segmentsLeft ?? 0;
  const segmentsRight = config.segmentsRight ?? 2;

  // Get connected map's scale
  const mapScale = useMemo(() => {
    if (!mapElementId || !mapElements.length) {
      // Default scale (roughly city level)
      return 100; // meters per pixel
    }

    const connectedMap = mapElements.find((el) => el.id === mapElementId);
    if (!connectedMap?.config?.viewState) {
      return 100;
    }

    const viewState = connectedMap.config.viewState;
    const zoomLevel = viewState.zoom ?? 10;
    const latitude = viewState.latitude ?? 48;

    // Calculate meters per pixel at this zoom level and latitude
    // Formula: 156543.03392 * cos(lat) / (2 ^ zoom)
    const metersPerPixel = (156543.03392 * Math.cos((latitude * Math.PI) / 180)) / Math.pow(2, zoomLevel);

    return metersPerPixel;
  }, [mapElementId, mapElements]);

  // Calculate scale bar values
  const scaleParams = useMemo(
    () => calculateScaleBarParams(mapScale, unit, segmentsRight, segmentsLeft),
    [mapScale, unit, segmentsRight, segmentsLeft]
  );

  const renderScalebar = () => {
    const commonProps = {
      totalSegments: scaleParams.totalSegments,
      segmentsLeft,
      segmentValue: scaleParams.segmentValue,
      labelUnit,
      labelMultiplier,
      height,
    };

    switch (style) {
      case "single_box":
        return <SingleBoxScalebar {...commonProps} />;
      case "double_box":
        return <DoubleBoxScalebar {...commonProps} />;
      case "line_ticks_middle":
        return <LineTicksScalebar {...commonProps} tickPosition="middle" />;
      case "line_ticks_down":
        return <LineTicksScalebar {...commonProps} tickPosition="down" />;
      case "line_ticks_up":
        return <LineTicksScalebar {...commonProps} tickPosition="up" />;
      case "stepped_line":
        return <SteppedLineScalebar {...commonProps} />;
      case "hollow":
        return <HollowScalebar {...commonProps} />;
      case "numeric":
        return <NumericScalebar mapScale={mapScale} />;
      default:
        return <SingleBoxScalebar {...commonProps} />;
    }
  };

  return (
    <Box
      sx={{
        width: `${100 / zoom}%`,
        height: `${100 / zoom}%`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 1,
        boxSizing: "border-box",
        transform: `scale(${zoom})`,
        transformOrigin: "top left",
      }}>
      <Box sx={{ width: "100%", maxWidth: "200px" }}>{renderScalebar()}</Box>
    </Box>
  );
};

export default ScalebarElementRenderer;
