"use client";

import { useTheme } from "@mui/material";
import { DotPulse, Ring } from "@uiball/loaders";

export type LoadingProps = {
  loadingType?: "ring" | "dotpulse";
  size?: number;
  color?: string;
  speed?: number;
};

export const defaultProps: LoadingProps = {
  loadingType: "dotpulse",
  size: 60,
  color: "black",
  speed: 1.3,
};

export function Loading(props: LoadingProps = defaultProps) {
  const theme = useTheme();
  const color = theme.palette.primary.main;
  props = { ...defaultProps, ...props, color };
  return props.loadingType === "ring" ? <Ring {...props} /> : <DotPulse {...props} />;
}
