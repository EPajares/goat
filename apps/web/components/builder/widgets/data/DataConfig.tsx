// import { Checkbox, FormControlLabel, Stack, Typography } from "@mui/material";
import { useMemo } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { FilterDataSchema, FilterLayoutTypes, WidgetDataConfig } from "@/lib/validations/widget";
import { filterLayoutTypes } from "@/lib/validations/widget";

import type { SelectorItem } from "@/types/map/common";

import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
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

  const layoutOptions = useMemo(
    () => [{ value: filterLayoutTypes.Values.select, label: t("dropdown") }],
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
        active={!!config?.setup?.column_name}
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
            {/* <Stack>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    color="primary"
                    checked={!!config.setup?.multiple}
                    onChange={(e) => {
                      const isChecked = e.target.checked;
                      onChange({
                        ...config,
                        setup: {
                          ...config.setup,
                          multiple: isChecked,
                        },
                      });
                    }}
                  />
                }
                label={<Typography variant="body2">{t("multiple_selection")}</Typography>}
              />
            </Stack> */}
          </>
        }
      />
    </>
  );
};
