"use client";

import type MapboxDraw from "@mapbox/mapbox-gl-draw";
import React, { type ReactNode, createContext, useContext, useState } from "react";

// ============================================================================
// Draw Context - shared MapboxDraw instance
// ============================================================================

interface DrawContextType {
  drawControl: MapboxDraw | null;
  setDrawControl: React.Dispatch<React.SetStateAction<MapboxDraw | null>>;
}

const DrawContext = createContext<DrawContextType | undefined>(undefined);

export const useDraw = () => {
  const context = useContext(DrawContext);
  if (!context) {
    throw new Error("useDraw must be used within a DrawProvider");
  }
  return context;
};

export const DrawProvider = ({ children }: { children: ReactNode }) => {
  const [drawControl, setDrawControl] = useState<MapboxDraw | null>(null);

  return <DrawContext.Provider value={{ drawControl, setDrawControl }}>{children}</DrawContext.Provider>;
};
