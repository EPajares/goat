"use client";

import { Stack, TextField, useTheme } from "@mui/material";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { ReportElement } from "@/lib/validations/reportLayout";

import type { SelectorItem } from "@/types/map/common";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";

/**
 * Scalebar style options
 */
export const SCALEBAR_STYLES = [
  { value: "single_box", labelKey: "scalebar_single_box" },
  { value: "double_box", labelKey: "scalebar_double_box" },
  { value: "line_ticks_middle", labelKey: "scalebar_line_ticks_middle" },
  { value: "line_ticks_down", labelKey: "scalebar_line_ticks_down" },
  { value: "line_ticks_up", labelKey: "scalebar_line_ticks_up" },
  { value: "stepped_line", labelKey: "scalebar_stepped_line" },
  { value: "hollow", labelKey: "scalebar_hollow" },
  { value: "numeric", labelKey: "scalebar_numeric" },
] as const;

export type ScalebarStyle = (typeof SCALEBAR_STYLES)[number]["value"];

/**
 * Scalebar unit options with their abbreviations
 */
export const SCALEBAR_UNITS = [
  { value: "map_units", labelKey: "map_units", abbreviation: "" },
  { value: "kilometers", labelKey: "kilometers", abbreviation: "km" },
  { value: "meters", labelKey: "meters", abbreviation: "m" },
  { value: "feet", labelKey: "feet", abbreviation: "ft" },
  { value: "yards", labelKey: "yards", abbreviation: "yd" },
  { value: "miles", labelKey: "miles", abbreviation: "mi" },
  { value: "nautical_miles", labelKey: "nautical_miles", abbreviation: "nmi" },
  { value: "centimeters", labelKey: "centimeters", abbreviation: "cm" },
  { value: "millimeters", labelKey: "millimeters", abbreviation: "mm" },
  { value: "inches", labelKey: "inches", abbreviation: "in" },
] as const;

export type ScalebarUnit = (typeof SCALEBAR_UNITS)[number]["value"];

/**
 * Get the default abbreviation for a unit
 */
export const getUnitAbbreviation = (unit: ScalebarUnit): string => {
  const found = SCALEBAR_UNITS.find((u) => u.value === unit);
  return found?.abbreviation ?? "";
};

/**
 * Scalebar element configuration interface
 */
export interface ScalebarElementConfig {
  /** Map element ID to bind to */
  mapElementId?: string | null;
  /** Scalebar style */
  style?: ScalebarStyle;
  /** Unit for the scalebar */
  unit?: ScalebarUnit;
  /** Label unit multiplier */
  labelMultiplier?: number;
  /** Custom label for unit (overrides default abbreviation) */
  labelUnit?: string;
  /** Height in mm */
  height?: number;
  /** Number of segments on the left (subdivisions) */
  segmentsLeft?: number;
  /** Number of segments on the right (main divisions) */
  segmentsRight?: number;
}

interface ScalebarElementConfigProps {
  element: ReportElement;
  mapElements?: ReportElement[];
  onChange: (updates: Partial<ReportElement>) => void;
}

/**
 * Scalebar Element Configuration Panel
 *
 * Structure:
 * - Data: Connected map
 * - Options: Style, units, segments, height
 */
const ScalebarElementConfig: React.FC<ScalebarElementConfigProps> = ({
  element,
  mapElements = [],
  onChange,
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();

  // Section collapsed states
  const [dataCollapsed, setDataCollapsed] = useState(false);
  const [optionsCollapsed, setOptionsCollapsed] = useState(false);

  // Extract current config
  const config = (element.config || {}) as ScalebarElementConfig;
  const mapElementId = config.mapElementId ?? "";
  const style = config.style ?? "single_box";
  const unit = config.unit ?? "kilometers";
  const labelMultiplier = config.labelMultiplier ?? 1;
  const labelUnit = config.labelUnit ?? getUnitAbbreviation(unit);
  const height = config.height ?? 8;
  const segmentsLeft = config.segmentsLeft ?? 0;
  const segmentsRight = config.segmentsRight ?? 2;

  // Filter to only map elements and create selector items
  const mapSelectorItems: SelectorItem[] = useMemo(() => {
    const maps = mapElements.filter((el) => el.type === "map");
    return [
      { label: t("none"), value: "" },
      ...maps.map((mapEl, index) => ({
        label: `${t("map")} ${index + 1}`,
        value: mapEl.id,
      })),
    ];
  }, [mapElements, t]);

  const selectedMapItem = useMemo(
    () => mapSelectorItems.find((item) => item.value === mapElementId),
    [mapSelectorItems, mapElementId]
  );

  // Style selector items
  const styleSelectorItems: SelectorItem[] = useMemo(
    () =>
      SCALEBAR_STYLES.map((s) => ({
        label: t(s.labelKey),
        value: s.value,
      })),
    [t]
  );

  const selectedStyleItem = useMemo(
    () => styleSelectorItems.find((item) => item.value === style),
    [styleSelectorItems, style]
  );

  // Unit selector items
  const unitSelectorItems: SelectorItem[] = useMemo(
    () =>
      SCALEBAR_UNITS.map((u) => ({
        label: t(u.labelKey),
        value: u.value,
      })),
    [t]
  );

  const selectedUnitItem = useMemo(
    () => unitSelectorItems.find((item) => item.value === unit),
    [unitSelectorItems, unit]
  );

  // Height selector items (4-20mm)
  const heightSelectorItems: SelectorItem[] = useMemo(
    () =>
      [4, 5, 6, 8, 10, 12, 14, 16, 18, 20].map((h) => ({
        label: `${h} mm`,
        value: h,
      })),
    []
  );

  const selectedHeightItem = useMemo(
    () => heightSelectorItems.find((item) => item.value === height),
    [heightSelectorItems, height]
  );

  // Segment selector items (0-10)
  const segmentSelectorItems: SelectorItem[] = useMemo(
    () =>
      Array.from({ length: 11 }, (_, i) => ({
        label: `${i}`,
        value: i,
      })),
    []
  );

  const selectedSegmentsLeftItem = useMemo(
    () => segmentSelectorItems.find((item) => item.value === segmentsLeft),
    [segmentSelectorItems, segmentsLeft]
  );

  const selectedSegmentsRightItem = useMemo(
    () => segmentSelectorItems.find((item) => item.value === segmentsRight),
    [segmentSelectorItems, segmentsRight]
  );

  // Handle config updates
  const updateConfig = (updates: Partial<ScalebarElementConfig>) => {
    onChange({
      config: {
        ...config,
        ...updates,
      },
    });
  };

  // Handle map selection
  const handleMapChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({ mapElementId: item.value ? String(item.value) : null });
  };

  // Handle style selection
  const handleStyleChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({ style: item.value as ScalebarStyle });
  };

  // Handle unit selection
  const handleUnitChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    const newUnit = item.value as ScalebarUnit;
    // Update both unit and labelUnit (to default abbreviation)
    updateConfig({
      unit: newUnit,
      labelUnit: getUnitAbbreviation(newUnit),
    });
  };

  // Handle label multiplier change
  const handleLabelMultiplierChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value > 0) {
      updateConfig({ labelMultiplier: value });
    }
  };

  // Handle label unit change
  const handleLabelUnitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    updateConfig({ labelUnit: e.target.value });
  };

  // Handle height selection
  const handleHeightChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({ height: item.value as number });
  };

  // Handle segments left change
  const handleSegmentsLeftChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({ segmentsLeft: item.value as number });
  };

  // Handle segments right change
  const handleSegmentsRightChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({ segmentsRight: item.value as number });
  };

  return (
    <Stack spacing={2}>
      {/* Data Section */}
      <SectionHeader
        label={t("data")}
        icon={ICON_NAME.LAYERS}
        active={true}
        alwaysActive
        collapsed={dataCollapsed}
        setCollapsed={setDataCollapsed}
        disableAdvanceOptions
      />
      <SectionOptions
        active={true}
        collapsed={dataCollapsed}
        baseOptions={
          <Stack spacing={3}>
            {/* Connected Map */}
            <Selector
              selectedItems={selectedMapItem}
              setSelectedItems={handleMapChange}
              items={mapSelectorItems}
              label={t("connected_map")}
              tooltip={t("scalebar_map_connection_help")}
            />
          </Stack>
        }
      />

      {/* Options Section */}
      <SectionHeader
        label={t("options")}
        icon={ICON_NAME.SLIDERS}
        active={true}
        alwaysActive
        collapsed={optionsCollapsed}
        setCollapsed={setOptionsCollapsed}
        disableAdvanceOptions
      />
      <SectionOptions
        active={true}
        collapsed={optionsCollapsed}
        baseOptions={
          <Stack spacing={3}>
            {/* Style */}
            <Selector
              selectedItems={selectedStyleItem}
              setSelectedItems={handleStyleChange}
              items={styleSelectorItems}
              label={t("style")}
            />

            {/* Units - only for non-numeric styles */}
            {style !== "numeric" && (
              <Selector
                selectedItems={selectedUnitItem}
                setSelectedItems={handleUnitChange}
                items={unitSelectorItems}
                label={t("scalebar_units")}
              />
            )}

            {/* Label Unit Multiplier - only for non-numeric styles */}
            {style !== "numeric" && (
              <Stack spacing={0.5}>
                <FormLabelHelper
                  label={t("scalebar_label_multiplier")}
                  color={theme.palette.text.secondary}
                  tooltip={t("scalebar_label_multiplier_help")}
                />
                <TextField
                  type="number"
                  size="small"
                  value={labelMultiplier}
                  onChange={handleLabelMultiplierChange}
                  inputProps={{ min: 0.001, step: 0.1 }}
                />
              </Stack>
            )}

            {/* Label for Unit - only for non-numeric styles */}
            {style !== "numeric" && (
              <Stack spacing={0.5}>
                <FormLabelHelper
                  label={t("scalebar_label_unit")}
                  color={theme.palette.text.secondary}
                  tooltip={t("scalebar_label_unit_help")}
                />
                <TextField
                  size="small"
                  value={labelUnit}
                  onChange={handleLabelUnitChange}
                  placeholder={getUnitAbbreviation(unit)}
                />
              </Stack>
            )}

            {/* Height - only for non-numeric styles */}
            {style !== "numeric" && (
              <Selector
                selectedItems={selectedHeightItem}
                setSelectedItems={handleHeightChange}
                items={heightSelectorItems}
                label={t("height")}
              />
            )}

            {/* Segments - Left - only for non-numeric styles */}
            {style !== "numeric" && (
              <Selector
                selectedItems={selectedSegmentsLeftItem}
                setSelectedItems={handleSegmentsLeftChange}
                items={segmentSelectorItems}
                label={t("scalebar_segments_left")}
                tooltip={t("scalebar_segments_left_help")}
              />
            )}

            {/* Segments - Right - only for non-numeric styles */}
            {style !== "numeric" && (
              <Selector
                selectedItems={selectedSegmentsRightItem}
                setSelectedItems={handleSegmentsRightChange}
                items={segmentSelectorItems}
                label={t("scalebar_segments_right")}
                tooltip={t("scalebar_segments_right_help")}
              />
            )}
          </Stack>
        }
      />
    </Stack>
  );
};

export default ScalebarElementConfig;
