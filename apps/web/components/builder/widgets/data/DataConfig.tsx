import { Checkbox, FormControlLabel, Stack, Typography } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { FilterDataSchema, FilterLayoutTypes, WidgetDataConfig } from "@/lib/validations/widget";
import { filterLayoutTypes } from "@/lib/validations/widget";

import type { SelectorItem } from "@/types/map/common";

import { useLayerDatasetId } from "@/hooks/map/ToolsHooks";

import WidgetColorPicker from "@/components/builder/widgets/common/WidgetColorPicker";
import CategoryOrderConfig from "@/components/builder/widgets/data/CategoryOrderConfig";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import SliderInput from "@/components/map/panels/common/SliderInput";
import TextFieldInput from "@/components/map/panels/common/TextFieldInput";

export type FilterDataConfigurationProps = {
  config: WidgetDataConfig;
  onChange: (config: WidgetDataConfig) => void;
};

export const WidgetFilterLayout = ({
  config,
  onChange,
}: {
  config: FilterDataSchema;
  onChange: (config: FilterDataSchema) => void;
}) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams();

  // Get the dataset ID from the selected layer
  const selectedLayerDatasetId = useLayerDatasetId(
    config.setup?.layer_project_id as number | undefined,
    projectId as string
  );

  const layoutOptions = useMemo(
    () => [
      { value: filterLayoutTypes.Values.select, label: t("dropdown") },
      { value: filterLayoutTypes.Values.chips, label: t("chips") },
      { value: filterLayoutTypes.Values.checkbox, label: t("checkbox") },
      { value: filterLayoutTypes.Values.range, label: t("range") },
    ],
    [t]
  );

  const selectedLayout = useMemo(() => {
    return layoutOptions.find((option) => option.value === config.setup?.layout);
  }, [config.setup?.layout, layoutOptions]);

  return (
    <>
      <SectionHeader
        active={!!config?.setup?.column_name}
        alwaysActive
        label={t("setup")}
        icon={ICON_NAME.SETTINGS}
        disableAdvanceOptions
      />
      <SectionOptions
        active={true}
        baseOptions={
          <>
            <Selector
              selectedItems={selectedLayout}
              setSelectedItems={(item: SelectorItem) => {
                onChange({
                  ...config,
                  setup: {
                    ...config.setup,
                    layout: item?.value as FilterLayoutTypes,
                  },
                });
              }}
              items={layoutOptions}
              label={t("layout")}
            />
            {/* Select (Dropdown) specific settings */}
            {selectedLayout?.value === filterLayoutTypes.Values.select && (
              <TextFieldInput
                type="text"
                label={t("placeholder")}
                placeholder={t("enter_placeholder_text")}
                clearable={false}
                value={config.setup.placeholder || ""}
                onChange={(value: string) => {
                  onChange({
                    ...config,
                    setup: {
                      ...config.setup,
                      placeholder: value,
                    },
                  });
                }}
              />
            )}
            {/* Chips specific settings */}
            {selectedLayout?.value === filterLayoutTypes.Values.chips && (
              <>
                <Stack>
                  <Typography variant="body2" gutterBottom>
                    {t("min_visible_options")}
                  </Typography>
                  <SliderInput
                    value={config.setup.min_visible_options ?? 5}
                    isRange={false}
                    min={1}
                    max={20}
                    step={1}
                    onChange={(value) => {
                      onChange({
                        ...config,
                        setup: {
                          ...config.setup,
                          min_visible_options: value as number,
                        },
                      });
                    }}
                  />
                </Stack>
                <Stack>
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        color="primary"
                        checked={!!config.setup?.multiple}
                        onChange={(e) => {
                          onChange({
                            ...config,
                            setup: {
                              ...config.setup,
                              multiple: e.target.checked,
                            },
                          });
                        }}
                      />
                    }
                    label={<Typography variant="body2">{t("allow_multiple_selection")}</Typography>}
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        color="primary"
                        checked={config.setup?.wrap !== false}
                        onChange={(e) => {
                          onChange({
                            ...config,
                            setup: {
                              ...config.setup,
                              wrap: e.target.checked,
                            },
                          });
                        }}
                      />
                    }
                    label={<Typography variant="body2">{t("wrap_chips")}</Typography>}
                  />
                </Stack>
                <CategoryOrderConfig
                  layerId={selectedLayerDatasetId}
                  fieldName={config.setup?.column_name}
                  customOrder={config.setup?.custom_order}
                  onOrderChange={(order) => {
                    onChange({
                      ...config,
                      setup: {
                        ...config.setup,
                        custom_order: order,
                      },
                    });
                  }}
                />
              </>
            )}
            {/* Checkbox specific settings */}
            {selectedLayout?.value === filterLayoutTypes.Values.checkbox && (
              <>
                <Stack>
                  <Typography variant="body2" gutterBottom>
                    {t("min_visible_options")}
                  </Typography>
                  <SliderInput
                    value={config.setup.min_visible_options ?? 5}
                    isRange={false}
                    min={1}
                    max={20}
                    step={1}
                    onChange={(value) => {
                      onChange({
                        ...config,
                        setup: {
                          ...config.setup,
                          min_visible_options: value as number,
                        },
                      });
                    }}
                  />
                </Stack>
                <Stack>
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        color="primary"
                        checked={!!config.setup?.multiple}
                        onChange={(e) => {
                          onChange({
                            ...config,
                            setup: {
                              ...config.setup,
                              multiple: e.target.checked,
                            },
                          });
                        }}
                      />
                    }
                    label={<Typography variant="body2">{t("allow_multiple_selection")}</Typography>}
                  />
                </Stack>
                <CategoryOrderConfig
                  layerId={selectedLayerDatasetId}
                  fieldName={config.setup?.column_name}
                  customOrder={config.setup?.custom_order}
                  onOrderChange={(order) => {
                    onChange({
                      ...config,
                      setup: {
                        ...config.setup,
                        custom_order: order,
                      },
                    });
                  }}
                />
              </>
            )}
            {/* Range specific settings */}
            {selectedLayout?.value === filterLayoutTypes.Values.range && (
              <>
                <Stack>
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        color="primary"
                        checked={config.setup?.show_histogram !== false}
                        onChange={(e) => {
                          onChange({
                            ...config,
                            setup: {
                              ...config.setup,
                              show_histogram: e.target.checked,
                            },
                          });
                        }}
                      />
                    }
                    label={<Typography variant="body2">{t("show_histogram")}</Typography>}
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        color="primary"
                        checked={config.setup?.show_slider !== false}
                        onChange={(e) => {
                          onChange({
                            ...config,
                            setup: {
                              ...config.setup,
                              show_slider: e.target.checked,
                            },
                          });
                        }}
                      />
                    }
                    label={<Typography variant="body2">{t("show_slider")}</Typography>}
                  />
                </Stack>
                <Stack>
                  <Typography variant="body2" gutterBottom>
                    {t("steps")}
                  </Typography>
                  <SliderInput
                    value={config.setup.steps ?? 50}
                    isRange={false}
                    min={10}
                    max={100}
                    step={10}
                    onChange={(value) => {
                      onChange({
                        ...config,
                        setup: {
                          ...config.setup,
                          steps: value as number,
                        },
                      });
                    }}
                  />
                </Stack>
              </>
            )}
          </>
        }
      />

      {/* Style section - show for layouts that support color customization */}
      {(selectedLayout?.value === filterLayoutTypes.Values.chips ||
        selectedLayout?.value === filterLayoutTypes.Values.checkbox ||
        selectedLayout?.value === filterLayoutTypes.Values.range) && (
        <>
          <SectionHeader
            active={true}
            alwaysActive
            label={t("style")}
            icon={ICON_NAME.STYLE}
            disableAdvanceOptions
          />
          <SectionOptions
            active={true}
            baseOptions={
              <WidgetColorPicker
                color={config.setup?.color || "#0e58ff"}
                onChange={(color) => {
                  onChange({
                    ...config,
                    setup: {
                      ...config.setup,
                      color,
                    },
                  });
                }}
                label={t("color")}
              />
            }
          />
        </>
      )}
    </>
  );
};
