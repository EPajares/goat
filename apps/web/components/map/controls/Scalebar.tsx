import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { styled } from "@mui/material/styles";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

type Unit = "imperial" | "metric";

type ScaleControlProps = {
  maxWidth?: number;
  unit?: Unit;
};

const Container = styled(Box)({
  position: "relative",
  width: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
});

const LabelsContainer = styled(Box)({
  color: "black",
  display: "flex",
  justifyContent: "space-between",
  width: "100%",
  position: "absolute",
  top: "-18px", // Position the labels above the scale bar
});

const Label = styled(Typography)({
  color: "inherit",
  position: "absolute",
  fontWeight: "bold",
  textShadow:
    "-1.5px 0 rgba(255, 255, 255, 0.75), 0 1.5px rgba(255, 255, 255, 0.75), 1.5px 0 rgba(255, 255, 255, 0.75), 0 -1.5px rgba(255, 255, 255, 0.75)", // Add white outline
});

const ScaleBar = styled(Box)({
  display: "flex",
  width: "100%",
  height: "4px",
  overflow: "hidden",
});

const BlackSection = styled(Box)({
  flex: 1,
  background: "black",
});

const WhiteSection = styled(Box)({
  flex: 1,
  background: "white",
});

const ScaleControl: React.FC<ScaleControlProps> = ({ maxWidth = 150 }) => {
  const { map } = useMap(); // Get the current map instance
  const containerRef = useRef<HTMLDivElement>(null);
  const [midLabel, setMidLabel] = useState<string>(""); // Midpoint label
  const [endLabel, setEndLabel] = useState<string>(""); // Endpoint label

  // List of valid scales
  const allowedScales = useMemo(
    () => [
      5, 10, 20, 30, 50, 100, 200, 300, 500, 1000, 2000, 3000, 5000, 10000, 20000, 30000, 50000, 100000,
      200000, 300000, 500000, 1000000, 2000000, 3000000, 5000000,
    ],
    []
  );

  const getNearestScale = useCallback(
    (num: number) => {
      // Find the closest valid scale from the allowedScales list
      return allowedScales.reduce((prev, curr) =>
        Math.abs(curr - num) < Math.abs(prev - num) ? curr : prev
      );
    },
    [allowedScales]
  );

  useEffect(() => {
    if (!map || !containerRef.current) return;

    const updateScale = () => {
      if (!containerRef.current) return;
      const optWidth = maxWidth;
      const y = map.getContainer().clientHeight / 2;
      const x = map.getContainer().clientWidth / 2;
      const left = map.unproject([x - optWidth / 2, y]);
      const right = map.unproject([x + optWidth / 2, y]);

      const maxMeters = left.distanceTo(right);
      const roundedScale = getNearestScale(maxMeters);

      const ratio = roundedScale / maxMeters;
      const displayWidth = optWidth * ratio;

      containerRef.current.style.width = `${displayWidth}px`;

      // Set labels with units
      setMidLabel(
        roundedScale >= 1000
          ? `${roundedScale / 2000}km` // Midpoint (half, in kilometers)
          : `${roundedScale / 2}m` // Midpoint (half, in meters)
      );
      setEndLabel(
        roundedScale >= 1000
          ? `${roundedScale / 1000}km` // Endpoint (in kilometers)
          : `${roundedScale}m` // Endpoint (in meters)
      );
    };

    map.on("moveend", updateScale);
    updateScale(); // Initial call

    return () => {
      map.off("moveend", updateScale);
    };
  }, [getNearestScale, map, maxWidth]);

  return (
    <Container ref={containerRef}>
      {/* Labels */}
      <LabelsContainer>
        <Label
          variant="caption"
          sx={{ left: "0%", transform: "translateX(-50%)" }} // Center align the left label
        >
          0
        </Label>
        <Label
          variant="caption"
          sx={{ left: "50%", transform: "translateX(-50%)" }} // Center align the middle label
        >
          {midLabel}
        </Label>
        <Label
          variant="caption"
          sx={{ right: "0%", transform: "translateX(50%)" }} // Center align the right label
        >
          {endLabel}
        </Label>
      </LabelsContainer>

      {/* Scale Bar */}
      <ScaleBar>
        <BlackSection />
        <WhiteSection />
      </ScaleBar>
    </Container>
  );
};

export default ScaleControl;
