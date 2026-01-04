"use client";

import { useSystemSettings } from "@/lib/api/system/client";
import type { UnitSystem } from "@/lib/utils/measurementUnits";

export const usePreferredUnitSystem = (): { unit: UnitSystem } => {
  const { systemSettings } = useSystemSettings();
  const unit = (systemSettings?.unit ?? "metric") as UnitSystem;

  return { unit };
};
