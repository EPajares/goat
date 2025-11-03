import { Box, Typography, useTheme } from "@mui/material";
import LinearProgress from "@mui/material/LinearProgress";
import { useMemo, useState } from "react";

import { useTranslation } from "@/i18n/client";

import { useProjectLayerAggregationStats } from "@/lib/api/projects";
import { formatNumber } from "@/lib/utils/format-number";
import type { AggregationStatsQueryParams } from "@/lib/validations/project";
import { aggregationStatsQueryParams } from "@/lib/validations/project";
import type { CategoriesChartSchema } from "@/lib/validations/widget";
import { categoriesChartConfigSchema } from "@/lib/validations/widget";

import { useChartWidget } from "@/hooks/map/DashboardBuilderHooks";

import { StaleDataLoader } from "@/components/builder/widgets/common/StaleDataLoader";
import { WidgetStatusContainer } from "@/components/builder/widgets/common/WidgetStatusContainer";

const DEFAULT_COLOR = "#0e58ff";
const OPACITY_MODIFIER = "33";

export const CategoriesChartWidget = ({ config: rawConfig }: { config: CategoriesChartSchema }) => {
  const { t, i18n } = useTranslation("common");
  const theme = useTheme();
  const { config, queryParams, projectId } = useChartWidget(
    rawConfig,
    categoriesChartConfigSchema,
    aggregationStatsQueryParams
  );

  const { aggregationStats, isLoading, isError } = useProjectLayerAggregationStats(
    projectId,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (config as any)?.setup?.layer_project_id,
    queryParams as AggregationStatsQueryParams
  );

  // Data handling
  const originalData = useMemo(() => aggregationStats?.items || [], [aggregationStats]);

  const displayData = useMemo(() => {
    if (originalData.length > 0) return originalData;
    return [{ grouped_value: t("no_data"), operation_value: 0 }];
  }, [originalData, t]);

  // Calculate max value for progress scaling
  const maxValue = useMemo(() => {
    return originalData.length > 0 ? Math.max(...originalData.map((item) => item.operation_value)) : 1; // For "No data" state
  }, [originalData]);

  const [activeCategory, setActiveCategory] = useState<string | undefined>();
  const [isHovering, setIsHovering] = useState(false);

  const getColor = (category: (typeof displayData)[number]) => {
    const baseColor = originalData.length > 0 ? config?.options?.color || DEFAULT_COLOR : "#e0e0e0";
    const shouldDim = originalData.length === 0 || (isHovering && activeCategory !== category.grouped_value);

    return shouldDim ? `${baseColor}${OPACITY_MODIFIER}` : baseColor;
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

      {config && !isError && isChartConfigured && (
        <Box
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => {
            setIsHovering(false);
            setActiveCategory(undefined);
          }}
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            p: 2,
          }}>
          {displayData.map((category) => {
            const percentage = (category.operation_value / maxValue) * 100;
            const displayValue = formatNumber(
              category.operation_value,
              config.options?.format,
              i18n.language
            );

            return (
              <Box
                key={category.grouped_value}
                onMouseEnter={() => setActiveCategory(category.grouped_value)}
                sx={{
                  width: "100%",
                  cursor: "pointer",
                  py: 1,
                  opacity:
                    originalData.length > 0 && activeCategory && activeCategory !== category.grouped_value
                      ? 0.5
                      : 1,
                  transition: "opacity 0.2s ease",
                }}>
                <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                  <Typography variant="caption" fontWeight={500}>
                    {category.grouped_value}
                  </Typography>
                  <Typography variant="caption" fontWeight={500}>
                    {displayValue}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={percentage}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: theme.palette.grey[200],
                    "& .MuiLinearProgress-bar": {
                      borderRadius: 4,
                      backgroundColor: getColor(category),
                    },
                  }}
                />
              </Box>
            );
          })}
        </Box>
      )}
      <StaleDataLoader isLoading={isLoading} hasData={!!originalData.length} />
    </>
  );
};
