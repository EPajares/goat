"use client";

import { Stack, TextField, Typography } from "@mui/material";
import React, { useState } from "react";
// import React, { useMemo, useState } from "react"; // Uncomment when Atlas is ready
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { ReportElement } from "@/lib/validations/reportLayout";

// import type { SelectorItem } from "@/types/map/common"; // Uncomment when Atlas is ready
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";

// import Selector from "@/components/map/panels/common/Selector"; // Uncomment when Atlas is ready

interface MapElementConfigProps {
  element: ReportElement;
  onChange: (updates: Partial<ReportElement>) => void;
}

// type AtlasMode = "best_fit" | "fixed_scale"; // Uncomment when Atlas is ready

/**
 * Configuration panel for map elements in reports.
 * Uses consistent UI patterns with SectionHeader and SectionOptions.
 *
 * Structure:
 * - Main Properties: Scale, rotation (general viewport settings)
 * - Controlled by Atlas: Mode selection for atlas-driven maps (hidden for now)
 *
 * Future sections to consider:
 * - Appearance (border, background, opacity) - can be shared across element types
 */
const MapElementConfig: React.FC<MapElementConfigProps> = ({ element, onChange }) => {
  const { t } = useTranslation("common");

  // Section collapsed states
  const [mainPropertiesCollapsed, setMainPropertiesCollapsed] = useState(false);
  // const [atlasCollapsed, setAtlasCollapsed] = useState(false); // Uncomment when Atlas is ready

  // Get current settings from element config
  const viewState = element.config?.viewState || {};
  const currentZoom = viewState.zoom ?? 10;
  const currentRotation = viewState.bearing ?? 0;

  // Atlas control settings - Uncomment when Atlas is ready
  // const atlasEnabled = element.config?.atlas?.enabled ?? false;
  // const atlasMode: AtlasMode = element.config?.atlas?.mode ?? "best_fit";
  // const marginPercent = element.config?.atlas?.margin_percent ?? 10;

  // Mode selector items - Uncomment when Atlas is ready
  // const modeItems: SelectorItem[] = useMemo(
  //   () => [
  //     { label: t("margin_around_feature"), value: "best_fit" },
  //     { label: t("fixed_scale"), value: "fixed_scale" },
  //   ],
  //   [t]
  // );

  // const selectedModeItem = useMemo(
  //   () => modeItems.find((item) => item.value === atlasMode),
  //   [modeItems, atlasMode]
  // );

  // Main Properties handlers
  const handleZoomChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(event.target.value);
    if (!isNaN(value) && value >= 0 && value <= 22) {
      onChange({
        config: {
          ...element.config,
          viewState: {
            ...element.config?.viewState,
            zoom: value,
          },
        },
      });
    }
  };

  const handleRotationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(event.target.value);
    if (!isNaN(value)) {
      // Normalize to -180 to 180
      const normalized = ((value % 360) + 360) % 360;
      const bearing = normalized > 180 ? normalized - 360 : normalized;
      onChange({
        config: {
          ...element.config,
          viewState: {
            ...element.config?.viewState,
            bearing,
          },
        },
      });
    }
  };

  // Atlas handlers - Uncomment when Atlas is ready
  // const handleAtlasEnabledChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  //   const enabled = event.target.checked;
  //   onChange({
  //     config: {
  //       ...element.config,
  //       atlas: {
  //         ...element.config?.atlas,
  //         enabled,
  //       },
  //     },
  //   });
  // };

  // const handleModeChange = (item: SelectorItem | SelectorItem[] | undefined) => {
  //   if (!item || Array.isArray(item)) return;
  //   const mode = item.value as AtlasMode;
  //   onChange({
  //     config: {
  //       ...element.config,
  //       atlas: {
  //         ...element.config?.atlas,
  //         mode,
  //       },
  //     },
  //   });
  // };

  // const handleMarginChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  //   const value = parseInt(event.target.value, 10);
  //   if (!isNaN(value) && value >= 0 && value <= 100) {
  //     onChange({
  //       config: {
  //         ...element.config,
  //         atlas: {
  //           ...element.config?.atlas,
  //           margin_percent: value,
  //         },
  //       },
  //     });
  //   }
  // };

  return (
    <Stack spacing={2}>
      {/* Main Properties Section */}
      <SectionHeader
        label={t("main_properties")}
        icon={ICON_NAME.MAP}
        active={true}
        alwaysActive
        collapsed={mainPropertiesCollapsed}
        setCollapsed={setMainPropertiesCollapsed}
        disableAdvanceOptions
      />
      <SectionOptions
        active={true}
        collapsed={mainPropertiesCollapsed}
        baseOptions={
          <Stack spacing={3}>
            {/* Zoom */}
            <TextField
              label={t("zoom")}
              type="number"
              size="small"
              value={currentZoom}
              onChange={handleZoomChange}
              inputProps={{ min: 0, max: 22, step: 0.5 }}
            />

            {/* Rotation */}
            <TextField
              label={t("map_rotation")}
              type="number"
              size="small"
              value={currentRotation}
              onChange={handleRotationChange}
              InputProps={{
                endAdornment: (
                  <Typography variant="body2" color="text.secondary">
                    °
                  </Typography>
                ),
              }}
            />
          </Stack>
        }
      />

      {/* Atlas Section - Hidden for now, feature not yet complete */}
      {/* TODO: Uncomment when Atlas feature is ready
      <SectionHeader
        label={t("controlled_by_atlas")}
        icon={ICON_NAME.LAYERS}
        active={atlasEnabled}
        onToggleChange={handleAtlasEnabledChange}
        collapsed={atlasCollapsed}
        setCollapsed={setAtlasCollapsed}
        disableAdvanceOptions
      />
      <SectionOptions
        active={atlasEnabled}
        collapsed={atlasCollapsed}
        baseOptions={
          <Stack spacing={3}>
            <Selector
              selectedItems={selectedModeItem}
              setSelectedItems={handleModeChange}
              items={modeItems}
              label={t("mode")}
            />

            {atlasMode === "best_fit" && (
              <TextField
                label={t("margin_percent")}
                type="number"
                size="small"
                value={marginPercent}
                onChange={handleMarginChange}
                inputProps={{ min: 0, max: 100 }}
                InputProps={{
                  endAdornment: <Typography variant="body2" color="text.secondary">%</Typography>,
                }}
              />
            )}

            {atlasMode === "fixed_scale" && (
              <Typography variant="caption" color="text.secondary">
                {t("fixed_scale_uses_main_properties")}
              </Typography>
            )}
          </Stack>
        }
      />
      */}
    </Stack>
  );
};

export default MapElementConfig;
