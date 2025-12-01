// Reuse your existing component
import ImageIcon from "@mui/icons-material/Image";
import { Box } from "@mui/material";
import React from "react";

import { MaskedImageIcon } from "@/components/map/panels/style/other/MaskedImageIcon";

interface LayerIconProps {
  type: "point" | "line" | "polygon" | "raster" | string;
  color?: string;
  strokeColor?: string;
  filled?: boolean;
  iconUrl?: string; // For custom markers or raster thumbnails
}

export const LayerIcon = ({ type, color, strokeColor, filled = true, iconUrl }: LayerIconProps) => {
  if (type === "raster") {
    return <ImageIcon fontSize="small" sx={{ color: "#888" }} />;
  }

  // Custom Marker Image
  if (type === "point" && iconUrl) {
    return (
      <Box sx={{ width: 20, height: 20, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <MaskedImageIcon imageUrl={iconUrl} dimension="16px" applyMask={false} />
      </Box>
    );
  }

  // SVG Geometry Icons
  return (
    <svg height="20" width="20" style={{ display: "block" }}>
      {type === "point" && (
        <circle
          cx="10"
          cy="10"
          r="6"
          fill={filled ? color : "none"}
          stroke={strokeColor || color} // Default stroke to fill if missing
          strokeWidth={strokeColor || !filled ? 2 : 0}
          fillOpacity={filled ? 1 : 0}
        />
      )}
      {type === "line" && (
        // line with round caps centered
        <line x1="4" y1="14" x2="16" y2="6" stroke={color} strokeWidth="3" strokeLinecap="round" />
      )}
      {type === "polygon" && (
        <rect
          x="4"
          y="4"
          width="12"
          height="12"
          rx="2"
          fill={filled ? color : "none"}
          stroke={strokeColor || color}
          strokeWidth={2}
          fillOpacity={filled ? 1 : 0}
        />
      )}
    </svg>
  );
};
