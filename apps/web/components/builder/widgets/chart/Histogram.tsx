import { Stack, Typography, useTheme } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import type { TooltipProps } from "recharts";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";

import { useProjectLayerHistogramStats } from "@/lib/api/projects";
import { formatNumber } from "@/lib/utils/format-number";
import type { HistogramStatsQueryParams } from "@/lib/validations/project";
import { histogramStatsQueryParams } from "@/lib/validations/project";
import type { HistogramChartSchema } from "@/lib/validations/widget";
import { histogramChartConfigSchema } from "@/lib/validations/widget";

import { useChartWidget } from "@/hooks/map/DashboardBuilderHooks";

import { StaleDataLoader } from "@/components/builder/widgets/common/StaleDataLoader";
import { WidgetStatusContainer } from "@/components/builder/widgets/common/WidgetStatusContainer";

const CustomTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  const { t } = useTranslation("common");
  if (active && payload?.length) {
    const { rangeStart, rangeEnd, count } = payload[0].payload;
    return (
      <Stack>
        <Typography variant="caption" fontWeight="bold">
          [{formatNumber(rangeStart)} - {formatNumber(rangeEnd)}]
        </Typography>
        <Typography variant="body2" fontWeight="bold">
          {`${t("count")}: ${count}`}
        </Typography>
      </Stack>
    );
  }
  return null;
};

export const HistogramChartWidget = ({ config: rawConfig }: { config: HistogramChartSchema }) => {
  const theme = useTheme();
  const { t, i18n } = useTranslation("common");
  const { config, queryParams, projectId } = useChartWidget(
    rawConfig,
    histogramChartConfigSchema,
    histogramStatsQueryParams
  );
  const { histogramStats, isLoading, isError } = useProjectLayerHistogramStats(
    projectId,
    config?.setup?.layer_project_id,
    queryParams as HistogramStatsQueryParams
  );

  // ✅ Transform API data into flat numeric values
  const chartData = useMemo(() => {
    if (!histogramStats?.bins) return [];
    return histogramStats.bins.map((bin) => ({
      rangeStart: Number(bin.range[0]),
      rangeEnd: Number(bin.range[1]),
      count: bin.count,
    }));
  }, [histogramStats]);

  const isChartConfigured = useMemo(() => {
    return config?.setup?.layer_project_id && queryParams;
  }, [config, queryParams]);

  return (
    <>
      <WidgetStatusContainer
        isLoading={isLoading && !histogramStats && !isError}
        isNotConfigured={!isChartConfigured}
        isError={isError}
        height={150}
        isNotConfiguredMessage={t("please_configure_chart")}
        errorMessage={t("cannot_render_chart_error")}
      />

      {config && histogramStats && !isError && isChartConfigured && (
        <ResponsiveContainer width="100%" aspect={1.2}>
          <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 10 }}>
            <XAxis
              dataKey="rangeStart"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickFormatter={(value) => formatNumber(value, config.options?.format, i18n.language)}
              tick={{ fontSize: 10, fill: theme.palette.text.secondary }}
              tickMargin={5}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: "transparent" }}
              wrapperStyle={{
                backgroundColor: theme.palette.background.paper,
                borderColor: theme.palette.divider,
                borderRadius: theme.shape.borderRadius,
                borderStyle: "ridge",
                padding: "5px",
              }}
              content={<CustomTooltip />}
            />
            <YAxis
              width={40}
              label={{ position: "left" }}
              axisLine={false}
              tickLine={false}
              tickMargin={10}
              tickFormatter={(value) =>
                new Intl.NumberFormat("en-US", {
                  notation: "compact",
                  compactDisplay: "short",
                }).format(value)
              }
              tick={{
                fontSize: 10,
                fontFamily: theme.typography.caption.fontFamily,
                fill: theme.palette.text.secondary,
              }}
            />
            <Bar
              dataKey="count"
              fill={config.options?.color || "#0e58ff"}
              radius={[4, 4, 0, 0]}
              cursor="pointer"
              activeBar={{ fill: config.options?.highlight_color || "#f5b704" }}
            />
          </BarChart>
        </ResponsiveContainer>
      )}

      <StaleDataLoader isLoading={isLoading} hasData={!!histogramStats?.bins?.length} />

      {config && histogramStats && histogramStats.total_rows > 0 && !isError && (
        <Typography variant="caption" align="left" gutterBottom>
          <Trans
            i18nKey="common:all_features_have_column"
            values={{
              nr_features: histogramStats.total_rows,
              column_name: config?.setup?.column_name,
            }}
            components={{ b: <b /> }}
          />
        </Typography>
      )}

      {config && histogramStats?.total_rows === 0 && config?.options?.filter_by_viewport && !isError && (
        <Typography variant="caption" align="left" gutterBottom>
          {t("no_features_in_viewport")}
        </Typography>
      )}

      {config && histogramStats?.total_rows === 0 && !config?.options?.filter_by_viewport && !isError && (
        <Typography variant="caption" align="left" gutterBottom>
          {t("no_features_in_layer")}
        </Typography>
      )}
    </>
  );
};
