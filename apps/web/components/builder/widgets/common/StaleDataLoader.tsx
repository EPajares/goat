import type { LinearProgressProps } from "@mui/material";
import { LinearProgress } from "@mui/material";
import { useEffect, useState } from "react";

interface StaleDataLoaderProps extends LinearProgressProps {
  isLoading: boolean;
  hasData: boolean;
  delay?: number;
}

export const StaleDataLoader = ({ isLoading, hasData, delay = 1000, ...props }: StaleDataLoaderProps) => {
  const [showLoader, setShowLoader] = useState(false);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (isLoading && hasData) {
      timeoutId = setTimeout(() => setShowLoader(true), delay);
    } else {
      setShowLoader(false);
    }

    return () => clearTimeout(timeoutId);
  }, [isLoading, hasData, delay]);

  return (
    <div
      style={{
        height: 2,
        zIndex: 1,
        visibility: showLoader ? "visible" : "hidden",
        transition: "opacity 0.2s ease",
        opacity: showLoader ? 1 : 0,
      }}>
      <LinearProgress
        {...props}
        sx={{
          height: "100%",
          backgroundColor: "transparent",
          "& .MuiLinearProgress-bar": {
            transition: "transform 0.5s linear",
          },
          ...props.sx,
        }}
      />
    </div>
  );
};
