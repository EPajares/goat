import { Button, Stack, Typography } from "@mui/material";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { type StatisticOperation, statisticOperationEnum } from "@/lib/validations/common";

import type { SelectorItem } from "@/types/map/common";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useLayerDatasetId, useStatisticValues } from "@/hooks/map/ToolsHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import Selector from "@/components/map/panels/common/Selector";
const FormulaBuilder = dynamic(() => import("@/components/modals/FormulaBuilder"), { ssr: false });

export type StatisticConfig = {
  method?: StatisticOperation | undefined;
  value?: string | undefined;
  groupBy?: string | undefined;
};

export const StatisticSelector = ({
  layerProjectId,
  value,
  onChange,
  hasGroupBy = false,
}: {
  layerProjectId: number;
  value?: StatisticConfig;
  onChange?: (value: StatisticConfig) => void;
  hasGroupBy?: boolean;
}) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams();

  const [formulaBuilderOpen, setFormulaBuilderOpen] = useState(false);

  const { statisticMethods } = useStatisticValues(true);
  const layerDatasetId = useLayerDatasetId(layerProjectId, projectId as string);
  const selectedStatisticMethod = useMemo(() => {
    return statisticMethods.find((method) => method.value === value?.method);
  }, [statisticMethods, value?.method]);

  const { layerFields } = useLayerFields(layerDatasetId || "");

  const isStatisticFieldVisible = useMemo(() => {
    return (
      selectedStatisticMethod?.value !== statisticOperationEnum.Enum.count &&
      selectedStatisticMethod?.value !== statisticOperationEnum.Enum.expression
    );
  }, [selectedStatisticMethod]);

  const statisticLayerFields = useMemo(() => {
    if (!layerFields) return [];
    if (isStatisticFieldVisible) {
      return layerFields.filter((field) => field.type === "number");
    }
    return layerFields;
  }, [layerFields, isStatisticFieldVisible]);

  const groupByFields = useMemo(() => {
    if (!layerFields) return [];
    return layerFields.filter((field) => field.name !== value?.value);
  }, [layerFields, value?.value]);

  const selectedField = useMemo(() => {
    return statisticLayerFields.find((field) => field.name === value?.value);
  }, [statisticLayerFields, value?.value]);

  const selectedGroupByField = useMemo(() => {
    return groupByFields.find((field) => field.name === value?.groupBy);
  }, [groupByFields, value?.groupBy]);

  return (
    <>
      {layerProjectId && (
        <Selector
          selectedItems={selectedStatisticMethod}
          setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
            if (onChange) {
              const newConfig: StatisticConfig = {
                method: (item as SelectorItem)?.value as StatisticOperation | undefined,
                value: undefined,
              };
              // Only include groupBy if hasGroupBy is true
              if (hasGroupBy) {
                newConfig.groupBy = undefined;
              }
              onChange(newConfig);
            }
          }}
          items={statisticMethods}
          label={t("select_statistic_method")}
          placeholder={t("select_statistic_method_placeholder")}
          tooltip={t("select_statistic_method_tooltip")}
        />
      )}

      {selectedStatisticMethod && layerDatasetId && isStatisticFieldVisible && (
        <LayerFieldSelector
          fields={statisticLayerFields}
          selectedField={selectedField}
          setSelectedField={(field) => {
            if (onChange) {
              const newConfig: StatisticConfig = {
                method: selectedStatisticMethod?.value as StatisticOperation | undefined,
                value: field?.name,
              };
              if (hasGroupBy) {
                newConfig.groupBy = undefined; // Reset groupBy when changing the field
              }
              onChange(newConfig);
            }
          }}
          label={t("select_field_to_calculate_statistics")}
          tooltip={t("select_field_to_calculate_statistics_tooltip")}
        />
      )}
      {hasGroupBy && selectedStatisticMethod?.value !== statisticOperationEnum.Enum.expression && (
        <LayerFieldSelector
          fields={groupByFields}
          selectedField={selectedGroupByField}
          setSelectedField={(field) => {
            if (onChange) {
              onChange({
                method: selectedStatisticMethod?.value as StatisticOperation | undefined,
                value: value?.value,
                groupBy: field?.name,
              });
            }
          }}
          label={t("field_group")}
        />
      )}
      {selectedStatisticMethod?.value === statisticOperationEnum.Enum.expression && (
        <>
          <FormLabelHelper label={t("expression")} tooltip={t("expression_tooltip")} color="text.secondary" />
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              variant="outlined"
              fullWidth
              onClick={() => setFormulaBuilderOpen(true)}
              startIcon={<Icon iconName={ICON_NAME.CODE} fontSize="small" />}
              sx={{
                justifyContent: "flex-start",
                textTransform: "none",
                fontFamily: value?.value ? "monospace" : "inherit",
                color: value?.value ? "text.primary" : "text.secondary",
              }}>
              <Typography
                variant="body2"
                noWrap
                sx={{
                  maxWidth: "100%",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}>
                {value?.value || t("click_to_build_expression")}
              </Typography>
            </Button>
          </Stack>
          <FormulaBuilder
            open={formulaBuilderOpen}
            onClose={() => setFormulaBuilderOpen(false)}
            onApply={(expression: string, groupByColumn?: string) => {
              if (onChange) {
                onChange({
                  method: statisticOperationEnum.Enum.expression,
                  value: expression,
                  groupBy: groupByColumn,
                });
              }
            }}
            initialExpression={value?.value || ""}
            initialGroupByColumn={value?.groupBy || ""}
            fields={layerFields || []}
            collectionId={layerDatasetId || undefined}
            showGroupBy={hasGroupBy}
          />
        </>
      )}
    </>
  );
};
