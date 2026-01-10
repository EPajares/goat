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
 * Legend element configuration interface (matches LegendElementRenderer)
 */
interface LegendElementConfig {
  /** Title configuration */
  title?: {
    text?: string;
  };
  /** Map element ID to bind to (null = show all layers) */
  mapElementId?: string | null;
  /** Layout options */
  layout?: {
    columns?: number;
    showBackground?: boolean;
  };
}

interface LegendElementConfigProps {
  element: ReportElement;
  mapElements?: ReportElement[];
  onChange: (updates: Partial<ReportElement>) => void;
}

/**
 * Legend Element Configuration Panel
 *
 * Uses consistent UI patterns with SectionHeader and SectionOptions.
 *
 * Structure:
 * - Info: Title text
 * - Configuration: Columns, map connection
 */
const LegendElementConfig: React.FC<LegendElementConfigProps> = ({ element, mapElements = [], onChange }) => {
  const { t } = useTranslation("common");
  const theme = useTheme();

  // Section collapsed states
  const [infoCollapsed, setInfoCollapsed] = useState(false);
  const [dataCollapsed, setDataCollapsed] = useState(false);
  const [optionsCollapsed, setOptionsCollapsed] = useState(false);

  // Extract current config
  const config = (element.config || {}) as LegendElementConfig;
  const titleText = config.title?.text ?? t("legend");
  const layoutConfig = config.layout ?? { columns: 1, showBackground: true };
  const mapElementId = config.mapElementId ?? "";

  // Create map selector items
  const mapSelectorItems: SelectorItem[] = useMemo(() => {
    const maps = mapElements.filter((el) => el.type === "map");
    return [
      { label: t("all_layers"), value: "" },
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

  // Create columns selector items
  const columnsSelectorItems: SelectorItem[] = useMemo(
    () =>
      [1, 2, 3, 4, 5].map((num) => ({
        label: `${num} ${num === 1 ? t("column") : t("columns")}`,
        value: num,
      })),
    [t]
  );

  const selectedColumnsItem = useMemo(
    () => columnsSelectorItems.find((item) => item.value === (layoutConfig.columns || 1)),
    [columnsSelectorItems, layoutConfig.columns]
  );

  // Handle config updates
  const updateConfig = (updates: Partial<LegendElementConfig>) => {
    onChange({
      config: {
        ...config,
        ...updates,
      },
    });
  };

  // Handle title change
  const handleTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    updateConfig({
      title: { text: event.target.value },
    });
  };

  // Handle map selection
  const handleMapChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({ mapElementId: item.value ? String(item.value) : null });
  };

  // Handle columns selection
  const handleColumnsChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    updateConfig({
      layout: { ...layoutConfig, columns: item.value as number },
    });
  };

  return (
    <Stack spacing={2}>
      {/* Info Section */}
      <SectionHeader
        label={t("info")}
        icon={ICON_NAME.CIRCLEINFO}
        active={true}
        alwaysActive
        collapsed={infoCollapsed}
        setCollapsed={setInfoCollapsed}
        disableAdvanceOptions
      />
      <SectionOptions
        active={true}
        collapsed={infoCollapsed}
        baseOptions={
          <Stack spacing={3}>
            <Stack>
              <FormLabelHelper label={t("title_text")} color={theme.palette.text.secondary} />
              <TextField
                size="small"
                value={titleText}
                onChange={handleTitleChange}
                placeholder={t("legend")}
                fullWidth
              />
            </Stack>
          </Stack>
        }
      />

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
              tooltip={t("legend_map_connection_help")}
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
            {/* Columns */}
            <Selector
              selectedItems={selectedColumnsItem}
              setSelectedItems={handleColumnsChange}
              items={columnsSelectorItems}
              label={t("columns")}
            />
          </Stack>
        }
      />
    </Stack>
  );
};

export default LegendElementConfig;
