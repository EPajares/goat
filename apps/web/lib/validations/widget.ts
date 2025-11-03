import * as z from "zod";

import { DEFAULT_COLOR_RANGE } from "@/lib/constants/color";
import { sortTypes, statisticOperationEnum } from "@/lib/validations/common";
import { colorRange } from "@/lib/validations/layer";

export const informationTypes = z.enum(["layers", "bookmarks", "comments"]);
export const dataTypes = z.enum(["filter", "table", "numbers", "feature_list"]);
export const chartTypes = z.enum(["histogram_chart", "categories_chart", "pie_chart"]);
export const elementTypes = z.enum(["text", "divider", "image"]);
export const widgetTypes = z.enum([
  ...informationTypes.options,
  ...dataTypes.options,
  ...chartTypes.options,
  ...elementTypes.options,
]);

export const widgetTypesWithoutConfig = [elementTypes.Values.text, elementTypes.Values.divider];

export const formatNumberTypes = z.enum([
  "none", // 1000
  "decimal_max", // All decimals (up to 3)
  "integer", // 1000 (no commas)
  "grouping", // 1,000
  "grouping_2d", // 12,345.67
  "signed_2d", // +12,345.67
  "compact", // 1k
  "compact_1d", // 12.3k
  "decimal_2", // 1.23
  "decimal_3", // 1.234
  "currency_usd", // $12,345.67
  "currency_eur", // €12,345.67
  "percent", // 1%
  "percent_1d", // 1.0%
  "percent_2d", // 1.00%
]);

const chartConfigSetupBaseSchema = z.object({
  title: z.string().optional().default("Chart"),
  layer_project_id: z.number().optional(),
});

// Information configuration schemas
const informationConfigSetupBaseSchema = z.object({
  title: z.string().optional().default("Information"),
});
const informationConfigOptionsBaseSchema = z.object({
  description: z.string().optional(),
});

export const informationConfigSchema = z.object({
  type: informationTypes,
  setup: informationConfigSetupBaseSchema.optional(),
  options: informationConfigOptionsBaseSchema.optional().default({}),
});

export const informationLayersConfigSchema = informationConfigSchema.extend({
  type: z.literal("layers"),
  setup: informationConfigSetupBaseSchema.extend({}).default({}),
  options: informationConfigOptionsBaseSchema
    .extend({
      show_search: z.boolean().optional().default(false),
      open_legend_by_default: z.boolean().optional().default(false),
    })
    .default({}),
});

// Data configuration schemas
const dataConfigSetupBaseSchema = z.object({
  title: z.string().optional().default("Data"),
});
const dataConfigOptionsBaseSchema = z.object({
  description: z.string().optional(),
});

export const dataConfigSchema = z.object({
  type: dataTypes,
  setup: dataConfigSetupBaseSchema.optional(),
  options: dataConfigOptionsBaseSchema.optional().default({}),
});

export const numbersDataConfigSchema = dataConfigSchema.extend({
  type: z.literal("numbers"),
  setup: chartConfigSetupBaseSchema
    .extend({
      operation_type: statisticOperationEnum.optional(),
      operation_value: z.string().optional(),
      icon: z.string().optional(),
    })
    .default({}),
  options: dataConfigOptionsBaseSchema
    .extend({
      filter_by_viewport: z.boolean().optional().default(true),
      cross_filter: z.boolean().optional().default(true),
      format: formatNumberTypes.optional().default("none"),
      description: z.string().optional(),
    })
    .default({}),
});

export const filterLayoutTypes = z.enum(["checkbox", "cards", "chips", "select", "range"]);
export const filterDataConfigSchema = dataConfigSchema.extend({
  type: z.literal("filter"),
  setup: chartConfigSetupBaseSchema
    .extend({
      layout: filterLayoutTypes.optional().default("select"),
      column_name: z.string().optional(),
      placeholder: z.string().optional(),
      multiple: z.boolean().optional().default(false),
    })
    .default({}),
  options: dataConfigOptionsBaseSchema
    .extend({
      description: z.string().optional(),
      cross_filter: z.boolean().optional().default(false),
      zoom_to_selection: z.boolean().optional().default(true),
    })
    .default({}),
});

// Chart configuration schemas
const chartConfigOptionsBaseSchema = z.object({
  filter_by_viewport: z.boolean().optional().default(true),
  cross_filter: z.boolean().optional().default(true),
  description: z.string().optional(),
});
export const chartsConfigBaseSchema = z.object({
  type: widgetTypes,
  setup: chartConfigSetupBaseSchema.optional().default({}),
  options: chartConfigOptionsBaseSchema.optional().default({}),
});

export const histogramChartConfigSchema = chartsConfigBaseSchema.extend({
  type: z.literal("histogram_chart"),
  setup: chartConfigSetupBaseSchema
    .extend({
      column_name: z.string().optional(),
    })
    .default({}),
  options: chartConfigOptionsBaseSchema
    .extend({
      num_bins: z.number().min(1).max(20).optional().default(10),
      min_value: z.number().optional(),
      max_value: z.number().optional(),
      include_outliers: z.boolean().optional().default(false),
      format: formatNumberTypes.optional().default("none"),
      color: z.string().optional().default("#0e58ff"),
      highlight_color: z.string().optional().default("#f5b704"),
    })
    .default({}),
});

export const categoriesChartConfigSchema = chartsConfigBaseSchema.extend({
  type: z.literal("categories_chart"),
  setup: chartConfigSetupBaseSchema
    .extend({
      operation_type: statisticOperationEnum.optional(),
      operation_value: z.string().optional(),
      group_by_column_name: z.string().optional(),
    })
    .default({}),
  options: chartConfigOptionsBaseSchema
    .extend({
      format: formatNumberTypes.optional().default("none"),
      sorting: sortTypes.optional().default("asc"),
      color: z.string().optional().default("#0e58ff"),
      width: z.number().min(3).max(15).optional().default(5),
      num_categories: z.number().min(1).max(15).optional().default(1),
      show_other_aggregate: z.boolean().optional().default(false),
    })
    .default({}),
});

export const pieChartConfigSchema = chartsConfigBaseSchema.extend({
  type: z.literal("pie_chart"),
  setup: chartConfigSetupBaseSchema
    .extend({
      operation_type: statisticOperationEnum.optional(),
      operation_value: z.string().optional(),
      group_by_column_name: z.string().optional(),
    })
    .default({}),
  options: chartConfigOptionsBaseSchema
    .extend({
      num_categories: z.number().min(1).max(15).optional().default(1),
      cap_others: z.boolean().optional().default(false),
      color_range: colorRange.optional().default(DEFAULT_COLOR_RANGE),
    })
    .default({}),
});

// Element configuration schemas
export const textElementConfigSchema = z.object({
  type: z.literal("text"),
  setup: z
    .object({
      text: z.string().optional().default("Text"),
    })
    .default({}),
});

export const dividerElementConfigSchema = z.object({
  type: z.literal("divider"),
  setup: z
    .object({
      size: z.number().min(1).max(10).optional().default(1),
    })
    .default({}),
});

export const imageElementConfigSchema = z.object({
  type: z.literal("image"),
  setup: z
    .object({
      url: z.string().optional(),
      alt: z.string().optional(),
    })
    .default({}),
  options: z
    .object({
      description: z.string().optional(),
      has_padding: z.boolean().optional().default(false),
    })
    .default({}),
});

export const configSchemas = z.union([
  informationLayersConfigSchema,
  numbersDataConfigSchema,
  filterDataConfigSchema,
  categoriesChartConfigSchema,
  histogramChartConfigSchema,
  pieChartConfigSchema,
  textElementConfigSchema,
  dividerElementConfigSchema,
  imageElementConfigSchema,
]);

export const widgetSchemaMap = {
  layers: informationLayersConfigSchema,
  numbers: numbersDataConfigSchema,
  filter: filterDataConfigSchema,
  histogram_chart: histogramChartConfigSchema,
  categories_chart: categoriesChartConfigSchema,
  pie_chart: pieChartConfigSchema,
  text: textElementConfigSchema,
  divider: dividerElementConfigSchema,
  image: imageElementConfigSchema,
};

export type WidgetTypes = z.infer<typeof widgetTypes>;
export type FormatNumberTypes = z.infer<typeof formatNumberTypes>;
export type ChartConfigBaseSchema = z.infer<typeof chartsConfigBaseSchema>;
export type HistogramChartSchema = z.infer<typeof histogramChartConfigSchema>;
export type CategoriesChartSchema = z.infer<typeof categoriesChartConfigSchema>;
export type PieChartSchema = z.infer<typeof pieChartConfigSchema>;
export type TextElementSchema = z.infer<typeof textElementConfigSchema>;
export type DividerElementSchema = z.infer<typeof dividerElementConfigSchema>;
export type ImageElementSchema = z.infer<typeof imageElementConfigSchema>;
export type LayerInformationSchema = z.infer<typeof informationLayersConfigSchema>;
export type NumbersDataSchema = z.infer<typeof numbersDataConfigSchema>;
export type FilterDataSchema = z.infer<typeof filterDataConfigSchema>;
export type FilterLayoutTypes = z.infer<typeof filterLayoutTypes>;

export type WidgetChartConfig = HistogramChartSchema | CategoriesChartSchema | PieChartSchema;
export type WidgetElementConfig = TextElementSchema | DividerElementSchema | ImageElementSchema;
export type WidgetInformationConfig = LayerInformationSchema;
export type WidgetDataConfig = NumbersDataSchema | FilterDataSchema;

export type WidgetConfigSchema = z.infer<typeof configSchemas>;
