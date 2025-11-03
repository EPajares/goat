import chroma from "chroma-js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Cell, Label, Pie, PieChart, ResponsiveContainer } from "recharts";

import { useTranslation } from "@/i18n/client";

import { useProjectLayerAggregationStats } from "@/lib/api/projects";
import { formatNumber } from "@/lib/utils/format-number";
import type { AggregationStatsQueryParams } from "@/lib/validations/project";
import { aggregationStatsQueryParams } from "@/lib/validations/project";
import type { PieChartSchema } from "@/lib/validations/widget";
import { pieChartConfigSchema } from "@/lib/validations/widget";

import { useChartWidget } from "@/hooks/map/DashboardBuilderHooks";

import { StaleDataLoader } from "@/components/builder/widgets/common/StaleDataLoader";
import { WidgetStatusContainer } from "@/components/builder/widgets/common/WidgetStatusContainer";

const FALLBACK_COLORS = ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"];
const OPACITY_MODIFIER = "33";

export const PieChartWidget = ({ config: rawConfig }: { config: PieChartSchema }) => {
  const { t, i18n } = useTranslation("common");
  const { config, queryParams, projectId } = useChartWidget(
    rawConfig,
    pieChartConfigSchema,
    aggregationStatsQueryParams
  );

  const { aggregationStats, isLoading, isError } = useProjectLayerAggregationStats(
    projectId,
    config?.setup?.layer_project_id,
    queryParams as AggregationStatsQueryParams
  );

  const data = useMemo(() => aggregationStats?.items || [], [aggregationStats]);
  const displayData = useMemo(() => {
    return data.length > 0 ? data : [{ grouped_value: t("no_data"), operation_value: 1 }];
  }, [data, t]);

  const [activeIndex, setActiveIndex] = useState(0);
  const [isHovering, setIsHovering] = useState(false);

  const totalOperationValue = useMemo(
    () => displayData.reduce((sum, item) => sum + item.operation_value, 0),
    [displayData]
  );

  const selectedValues = useMemo(() => [] as string[], []); // TODO: Connect to filters

  const calculateDefaultActiveIndex = useCallback(() => {
    if (data.length === 0) return 0;

    const candidates = data.filter((item) =>
      selectedValues.length > 0 ? selectedValues.includes(item.grouped_value) : true
    );

    const validData = candidates.length > 0 ? candidates : data;
    const maxValue = Math.max(...validData.map((item) => item.operation_value));
    return data.findIndex((item) => item.operation_value === maxValue);
  }, [data, selectedValues]);

  const baseColors = useMemo(() => {
    if (displayData.length === 0) return [];

    const palette = data.length > 0 ? config?.options?.color_range?.colors || FALLBACK_COLORS : ["#e0e0e0"];

    return displayData.length === 1
      ? [palette[0]]
      : chroma.scale(palette).mode("lch").colors(displayData.length);
  }, [displayData.length, data.length, config?.options?.color_range?.colors]);

  const computedColors = useMemo(() => {
    return displayData.map((item, index) => {
      const baseColor = baseColors[index % baseColors.length];
      const isSelected = selectedValues.includes(item.grouped_value);

      if (data.length === 0) return baseColor; // Keep full color for "No data" state

      return isHovering || selectedValues.length > 0
        ? isSelected
          ? baseColor
          : `${baseColor}${OPACITY_MODIFIER}`
        : baseColor;
    });
  }, [displayData, baseColors, selectedValues, data.length, isHovering]);

  useEffect(() => {
    const newIndex = calculateDefaultActiveIndex();
    setActiveIndex(Math.max(newIndex, 0));
  }, [calculateDefaultActiveIndex]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handlePieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const handleChartHover = (isEnter: boolean) => {
    setIsHovering(isEnter);
    if (!isEnter) {
      const newIndex = calculateDefaultActiveIndex();
      setActiveIndex(Math.max(newIndex, 0));
    }
  };

  const isChartConfigured = useMemo(() => {
    return config?.setup?.layer_project_id && queryParams;
  }, [config, queryParams]);

  return (
    <>
      <WidgetStatusContainer
        isLoading={isLoading && !aggregationStats && !isError}
        isNotConfigured={!isChartConfigured}
        isError={isError}
        height={150}
        isNotConfiguredMessage={t("please_configure_chart")}
        errorMessage={t("cannot_render_chart_error")}
      />

      {config && !isError && aggregationStats && isChartConfigured && (
        <ResponsiveContainer width="100%" aspect={1.2}>
          <PieChart onMouseEnter={() => handleChartHover(true)} onMouseLeave={() => handleChartHover(false)}>
            <Pie
              activeIndex={activeIndex}
              activeShape={{
                fill: baseColors[activeIndex % baseColors.length],
                strokeWidth: 0,
              }}
              data={displayData}
              dataKey="operation_value"
              nameKey="grouped_value"
              cx="50%"
              cy="50%"
              innerRadius="65%"
              cursor="pointer"
              isAnimationActive={false}
              paddingAngle={data.length > 0 ? 5 : 0}
              onMouseEnter={handlePieEnter}>
              {displayData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={computedColors[index]} stroke="none" />
              ))}

              <Label
                value={`${formatNumber(
                  displayData[activeIndex].operation_value / totalOperationValue,
                  "percent_1d",
                  i18n.language
                )}`}
                position="centerBottom"
                fontSize={14}
                fontWeight="bold"
                fill={baseColors[activeIndex % baseColors.length]}
              />

              <Label
                value={displayData[activeIndex].grouped_value}
                position="centerTop"
                fontSize={12}
                dy={8}
                fontWeight="bold"
                fill={baseColors[activeIndex % baseColors.length]}
              />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      )}
      <StaleDataLoader isLoading={isLoading} hasData={!!aggregationStats} />
    </>
  );
};
