"use client";

import { Box } from "@mui/material";
import { styled, useTheme } from "@mui/material/styles";
import React, { useMemo } from "react";

// Ruler configuration
const RULER_SIZE = 20; // Height for horizontal, width for vertical ruler

// Convert mm to pixels
const mmToPx = (mm: number, dpi: number): number => {
  return (mm / 25.4) * dpi;
};

// Convert pixels to mm
const pxToMm = (px: number, dpi: number): number => {
  return (px / dpi) * 25.4;
};

interface RulerProps {
  orientation: "horizontal" | "vertical";
  lengthMm: number; // Paper length in millimeters
  zoom: number;
  dpi: number;
  scrollOffset: number; // Current scroll position
  viewportSize: number; // Viewport width (horizontal) or height (vertical)
  paperOffset: number; // Where the paper starts in the scrollable content (pixels)
}

const RulerContainer = styled(Box, {
  shouldForwardProp: (prop) => !["orientation"].includes(prop as string),
})<{ orientation: "horizontal" | "vertical" }>(({ theme, orientation }) => ({
  position: "absolute",
  backgroundColor: theme.palette.background.default,
  overflow: "hidden",
  userSelect: "none",
  zIndex: 10,
  ...(orientation === "horizontal"
    ? {
        top: 0,
        left: RULER_SIZE,
        right: 0,
        height: RULER_SIZE,
        borderBottom: `1px solid ${theme.palette.divider}`,
      }
    : {
        top: RULER_SIZE,
        left: 0,
        bottom: 0,
        width: RULER_SIZE,
        borderRight: `1px solid ${theme.palette.divider}`,
      }),
}));

const CornerSquare = styled(Box)(({ theme }) => ({
  position: "absolute",
  top: 0,
  left: 0,
  width: RULER_SIZE,
  height: RULER_SIZE,
  backgroundColor: theme.palette.background.default,
  borderRight: `1px solid ${theme.palette.divider}`,
  borderBottom: `1px solid ${theme.palette.divider}`,
  zIndex: 11,
}));

// Calculate adaptive tick intervals based on zoom level
const getTickIntervals = (zoom: number): { major: number; minor: number; showMinor: boolean } => {
  // At very low zoom, show labels every 100mm
  if (zoom < 0.3) {
    return { major: 100, minor: 50, showMinor: false };
  }
  // At low zoom, show labels every 50mm
  if (zoom < 0.5) {
    return { major: 50, minor: 10, showMinor: false };
  }
  // At medium-low zoom, show labels every 20mm
  if (zoom < 0.75) {
    return { major: 20, minor: 10, showMinor: true };
  }
  // At medium zoom, show labels every 10mm
  if (zoom < 1.5) {
    return { major: 10, minor: 5, showMinor: true };
  }
  // At high zoom, show labels every 10mm with all minor ticks
  return { major: 10, minor: 5, showMinor: true };
};

interface TickMark {
  mm: number; // Position in mm relative to paper (can be negative)
  viewportPx: number; // Position in viewport pixels
  height: number; // Height/width of tick
  label?: string; // Label for major ticks
}

const Ruler: React.FC<RulerProps> = ({
  orientation,
  lengthMm,
  zoom,
  dpi,
  scrollOffset,
  viewportSize,
  paperOffset,
}) => {
  const theme = useTheme();

  // Calculate where paper starts in viewport coordinates
  const paperStartInViewport = paperOffset - scrollOffset;

  // Pixels per mm at current zoom
  const pxPerMm = mmToPx(1, dpi) * zoom;

  // Get adaptive intervals based on zoom
  const { major: majorInterval, minor: minorInterval, showMinor } = getTickIntervals(zoom);

  // Generate tick marks covering the entire visible viewport
  // QGIS-style: negative values before paper, 0 at paper start, positive on paper
  const ticks = useMemo(() => {
    const result: TickMark[] = [];

    // Calculate the mm range visible in the viewport
    // When scrollOffset=0, the left edge of viewport shows content at x=0
    // Paper starts at paperOffset pixels in the content
    const viewportStartMm = pxToMm(-paperStartInViewport, dpi) / zoom;
    const viewportEndMm = pxToMm(viewportSize - paperStartInViewport, dpi) / zoom;

    // Extend range a bit for smooth scrolling
    const startMm = Math.floor(viewportStartMm / majorInterval) * majorInterval - majorInterval;
    const endMm = Math.ceil(viewportEndMm / majorInterval) * majorInterval + majorInterval;

    // Generate ticks from start to end
    for (let mm = startMm; mm <= endMm; mm++) {
      // Skip if this tick would be way outside viewport
      const viewportPx = paperStartInViewport + mm * pxPerMm;
      if (viewportPx < -50 || viewportPx > viewportSize + 50) {
        continue;
      }

      const isMajor = mm % majorInterval === 0;
      const isMinor = mm % minorInterval === 0;

      if (isMajor) {
        // Major tick with label
        result.push({
          mm,
          viewportPx,
          height: RULER_SIZE * 0.6,
          label: String(mm),
        });
      } else if (isMinor && showMinor) {
        // Minor tick without label
        result.push({
          mm,
          viewportPx,
          height: RULER_SIZE * 0.35,
        });
      }
    }

    return result;
  }, [paperStartInViewport, viewportSize, zoom, dpi, pxPerMm, majorInterval, minorInterval, showMinor]);

  return (
    <RulerContainer orientation={orientation}>
      <svg
        width={orientation === "horizontal" ? viewportSize : RULER_SIZE}
        height={orientation === "horizontal" ? RULER_SIZE : viewportSize}
        style={{ display: "block" }}>
        {/* Paper range highlight - subtle background for paper area */}
        {orientation === "horizontal" ? (
          <rect
            x={Math.max(0, paperStartInViewport)}
            y={0}
            width={Math.min(
              viewportSize - Math.max(0, paperStartInViewport),
              lengthMm * pxPerMm - Math.max(0, -paperStartInViewport)
            )}
            height={RULER_SIZE}
            fill={theme.palette.action.hover}
            opacity={0.3}
          />
        ) : (
          <rect
            x={0}
            y={Math.max(0, paperStartInViewport)}
            width={RULER_SIZE}
            height={Math.min(
              viewportSize - Math.max(0, paperStartInViewport),
              lengthMm * pxPerMm - Math.max(0, -paperStartInViewport)
            )}
            fill={theme.palette.action.hover}
            opacity={0.3}
          />
        )}

        {ticks.map((tick, index) => {
          if (orientation === "horizontal") {
            return (
              <g key={index}>
                <line
                  x1={tick.viewportPx}
                  y1={RULER_SIZE}
                  x2={tick.viewportPx}
                  y2={RULER_SIZE - tick.height}
                  stroke={theme.palette.text.secondary}
                  strokeWidth={tick.label !== undefined ? 1 : 0.5}
                />
                {tick.label && (
                  <text
                    x={tick.viewportPx + 2}
                    y={10}
                    fontSize={9}
                    fill={theme.palette.text.secondary}
                    dominantBaseline="middle">
                    {tick.label}
                  </text>
                )}
              </g>
            );
          } else {
            return (
              <g key={index}>
                <line
                  x1={RULER_SIZE}
                  y1={tick.viewportPx}
                  x2={RULER_SIZE - tick.height}
                  y2={tick.viewportPx}
                  stroke={theme.palette.text.secondary}
                  strokeWidth={tick.label !== undefined ? 1 : 0.5}
                />
                {tick.label && (
                  <text
                    x={2}
                    y={tick.viewportPx + 2}
                    fontSize={8}
                    fill={theme.palette.text.secondary}
                    dominantBaseline="hanging"
                    textAnchor="start">
                    {tick.label}
                  </text>
                )}
              </g>
            );
          }
        })}

        {/* Paper edge markers (0 position) */}
        {paperStartInViewport >= 0 &&
          paperStartInViewport <= viewportSize &&
          (orientation === "horizontal" ? (
            <line
              x1={paperStartInViewport}
              y1={0}
              x2={paperStartInViewport}
              y2={RULER_SIZE}
              stroke={theme.palette.primary.main}
              strokeWidth={1.5}
            />
          ) : (
            <line
              x1={0}
              y1={paperStartInViewport}
              x2={RULER_SIZE}
              y2={paperStartInViewport}
              stroke={theme.palette.primary.main}
              strokeWidth={1.5}
            />
          ))}

        {/* Paper end marker */}
        {(() => {
          const paperEndInViewport = paperStartInViewport + lengthMm * pxPerMm;
          if (paperEndInViewport >= 0 && paperEndInViewport <= viewportSize) {
            return orientation === "horizontal" ? (
              <line
                x1={paperEndInViewport}
                y1={0}
                x2={paperEndInViewport}
                y2={RULER_SIZE}
                stroke={theme.palette.primary.main}
                strokeWidth={1.5}
              />
            ) : (
              <line
                x1={0}
                y1={paperEndInViewport}
                x2={RULER_SIZE}
                y2={paperEndInViewport}
                stroke={theme.palette.primary.main}
                strokeWidth={1.5}
              />
            );
          }
          return null;
        })()}
      </svg>
    </RulerContainer>
  );
};

// Fixed ruler wrapper - rulers stay fixed to canvas viewport
interface FixedRulerWrapperProps {
  widthMm: number;
  heightMm: number;
  zoom: number;
  dpi: number;
  show: boolean;
  scrollLeft: number;
  scrollTop: number;
  viewportWidth: number;
  viewportHeight: number;
  paperOffsetX: number; // Where the paper starts horizontally in the scrollable content
  paperOffsetY: number; // Where the paper starts vertically in the scrollable content
}

export const FixedRulerWrapper: React.FC<FixedRulerWrapperProps> = ({
  widthMm,
  heightMm,
  zoom,
  dpi,
  show,
  scrollLeft,
  scrollTop,
  viewportWidth,
  viewportHeight,
  paperOffsetX,
  paperOffsetY,
}) => {
  if (!show) return null;

  return (
    <Box
      sx={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: "none",
        zIndex: 10,
      }}>
      <CornerSquare />
      <Ruler
        orientation="horizontal"
        lengthMm={widthMm}
        zoom={zoom}
        dpi={dpi}
        scrollOffset={scrollLeft}
        viewportSize={viewportWidth}
        paperOffset={paperOffsetX}
      />
      <Ruler
        orientation="vertical"
        lengthMm={heightMm}
        zoom={zoom}
        dpi={dpi}
        scrollOffset={scrollTop}
        viewportSize={viewportHeight}
        paperOffset={paperOffsetY}
      />
    </Box>
  );
};

// Legacy wrapper for backwards compatibility (not used anymore)
interface RulerWrapperProps {
  widthMm: number;
  heightMm: number;
  zoom: number;
  dpi: number;
  show: boolean;
}

export const RulerWrapper: React.FC<RulerWrapperProps> = ({ show }) => {
  // Deprecated - use FixedRulerWrapper instead
  if (!show) return null;
  return null;
};

export { RULER_SIZE };
export default Ruler;
