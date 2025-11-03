import { Box, Typography } from "@mui/material";

import type { WidgetChartConfig } from "@/lib/validations/widget";
import { chartTypes } from "@/lib/validations/widget";

import { CategoriesChartWidget } from "@/components/builder/widgets/chart/Categories";
import { HistogramChartWidget } from "@/components/builder/widgets/chart/Histogram";
import { PieChartWidget } from "@/components/builder/widgets/chart/Pie";

interface WidgetChartProps {
  config: WidgetChartConfig;
  viewOnly?: boolean;
}

const WidgetChart: React.FC<WidgetChartProps> = ({ config }) => {
  return (
    <Box sx={{ minHeight: 200 }}>
      <Typography variant="body1" fontWeight="bold" align="left" gutterBottom>
        {config.setup?.title}
      </Typography>
      {config.type === chartTypes.Values.histogram_chart && <HistogramChartWidget config={config} />}
      {config.type === chartTypes.Values.pie_chart && <PieChartWidget config={config} />}
      {config.type === chartTypes.Values.categories_chart && <CategoriesChartWidget config={config} />}
      {config.options?.description && (
        <Typography variant="body2" align="left">
          {config.options.description}
        </Typography>
      )}
    </Box>
  );
};

export default WidgetChart;
