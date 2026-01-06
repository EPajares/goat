"use client";

import { Stack } from "@mui/material";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { ReportElement } from "@/lib/validations/reportLayout";

import type { SelectorItem } from "@/types/map/common";

import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";

/**
 * North arrow style options with their corresponding icon names
 */
const NORTH_ARROW_STYLES = [
  { value: "default", iconName: ICON_NAME.NORTH_ARROW, labelKey: "default" },
  { value: "circle", iconName: ICON_NAME.NORTH_ARROW_CIRCLE, labelKey: "circle" },
  { value: "compass", iconName: ICON_NAME.NORTH_ARROW_COMPASS, labelKey: "compass" },
  { value: "circle_extended", iconName: ICON_NAME.NORTH_ARROW_CIRCLE_EXT, labelKey: "circle_extended" },
  { value: "compass_filled", iconName: ICON_NAME.NORTH_ARROW_COMPASS_FILLED, labelKey: "compass_filled" },
  { value: "quadrant", iconName: ICON_NAME.NORTH_ARROW_QUADRANT, labelKey: "quadrant" },
] as const;

export type NorthArrowStyle = (typeof NORTH_ARROW_STYLES)[number]["value"];

/**
 * Get the icon name for a given north arrow style
 */
export const getNorthArrowIconName = (style?: NorthArrowStyle): ICON_NAME => {
  const found = NORTH_ARROW_STYLES.find((s) => s.value === style);
  return found?.iconName ?? ICON_NAME.NORTH_ARROW;
};

/**
 * North arrow element configuration interface
 */
interface NorthArrowElementConfig {
  /** Map element ID to bind rotation to */
  mapElementId?: string | null;
  /** North arrow style */
  style?: NorthArrowStyle;
}

interface NorthArrowElementConfigProps {
  element: ReportElement;
  mapElements?: ReportElement[];
  onChange: (updates: Partial<ReportElement>) => void;
}

/**
 * North Arrow Element Configuration Panel
 *
 * Uses consistent UI patterns with SectionHeader and SectionOptions.
 *
 * Structure:
 * - Data: Connected map (for rotation binding)
 * - Options: Style selection
 */
const NorthArrowElementConfig: React.FC<NorthArrowElementConfigProps> = ({
  element,
  mapElements = [],
  onChange,
}) => {
  const { t } = useTranslation("common");

  // Section collapsed states
  const [dataCollapsed, setDataCollapsed] = useState(false);
  const [optionsCollapsed, setOptionsCollapsed] = useState(false);

  // Extract current config
  const config = (element.config || {}) as NorthArrowElementConfig;
  const mapElementId = config.mapElementId ?? "";
  const style = config.style ?? "default";

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

  // Style selector items with icons
  const styleSelectorItems: SelectorItem[] = useMemo(
    () =>
      NORTH_ARROW_STYLES.map((s) => ({
        label: t(s.labelKey),
        value: s.value,
        icon: s.iconName,
      })),
    [t]
  );

  const selectedStyleItem = useMemo(
    () => styleSelectorItems.find((item) => item.value === style),
    [styleSelectorItems, style]
  );

  // Handle config updates
  const updateConfig = (updates: Partial<NorthArrowElementConfig>) => {
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
    updateConfig({ style: item.value as NorthArrowStyle });
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
              tooltip={t("north_arrow_map_connection_help")}
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
          </Stack>
        }
      />
    </Stack>
  );
};

export default NorthArrowElementConfig;
