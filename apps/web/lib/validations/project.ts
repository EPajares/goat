import * as z from "zod";

import { basicLayout } from "@/lib/constants/dashboard-builder-template-layouts";
import {
  contentMetadataSchema,
  getContentQueryParamsSchema,
  orderByEnum,
  statisticOperationEnum,
} from "@/lib/validations/common";
import { layerSchema } from "@/lib/validations/layer";
import { responseSchema } from "@/lib/validations/response";
import { publicUserSchema } from "@/lib/validations/user";
import { configSchemas } from "@/lib/validations/widget";

export const projectRoleEnum = z.enum(["project-owner", "project-viewer", "project-editor"]);

export const projectRoles = {
  OWNER: "project-owner",
  VIEWER: "project-viewer",
  EDITOR: "project-editor",
} as const;

export const projectShareRoleEnum = z.enum(["project-viewer", "project-editor"]);

export const shareProjectWithTeamOrOrganizationSchema = z.object({
  id: z.string(),
  name: z.string().optional(),
  avatar: z.string().optional(),
  role: projectShareRoleEnum,
});

export const shareProjectSchema = z.object({
  teams: z.array(shareProjectWithTeamOrOrganizationSchema).optional(),
  organizations: z.array(shareProjectWithTeamOrOrganizationSchema).optional(),
});

export const builderWidgetSchema = z.object({
  id: z.string(),
  type: z.literal("widget"),
  config: configSchemas.optional(),
});

export const builderPanelConfigSchema = z.object({
  options: z
    .object({
      style: z.enum(["default", "rounded", "floated"]).optional().default("default"),
    })
    .optional()
    .default({}),
  appearance: z
    .object({
      opacity: z.number().min(0).max(1).optional().default(1),
      backgroundBlur: z.number().min(0).max(20).optional().default(0),
      shadow: z.number().min(0).max(10).optional().default(0),
    })
    .optional()
    .default({}),
  position: z
    .object({
      alignItems: z.enum(["start", "center", "end"]).default("start"),
      spacing: z.number().min(0).max(15).optional().default(0),
    })
    .optional()
    .default({ alignItems: "start" }),
});

export const builderPanelSchema = z.object({
  id: z.string(),
  type: z.literal("panel").optional().default("panel"),
  position: z.enum(["top", "bottom", "left", "right"]),
  config: builderPanelConfigSchema.optional().default({}),
  widgets: z.array(builderWidgetSchema).optional().default([]),
});

export const builderConfigSchema = z.object({
  settings: z.object({
    location: z.boolean().default(true),
    scalebar: z.boolean().default(true),
    measure: z.boolean().default(false),
    find_my_location: z.boolean().default(false),
    zoom_controls: z.boolean().default(true),
    basemap: z.boolean().default(true),
    fullscreen: z.boolean().default(true),
    toolbar: z.boolean().default(true),
    project_info: z.boolean().default(true),
  }),
  interface: z.preprocess(
    // Convert empty arrays to `undefined` to trigger the default, todo: remove this when dashboard is completed
    (val) => (Array.isArray(val) && val.length === 0 ? undefined : val),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    z.array(builderPanelSchema).default(basicLayout.interface as any)
  ),
});

export const projectSchema = contentMetadataSchema.extend({
  folder_id: z.string(),
  id: z.string(),
  layer_order: z.array(z.number()),
  max_extent: z.tuple([z.number(), z.number(), z.number(), z.number()]).optional().nullable(),
  builder_config: builderConfigSchema.default({
    settings: {},
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    interface: basicLayout.interface as any,
  }),
  active_scenario_id: z.string().nullable().optional(),
  basemap: z.string().nullable().default("streets"),
  updated_at: z.string().optional(),
  created_at: z.string().optional(),
  shared_with: shareProjectSchema.optional(),
  owned_by: publicUserSchema.optional(),
});

export const projectPublicSchemaConfig = z.object({
  project: projectSchema,
  layers: z.array(layerSchema),
});

export const projectPublicSchema = z.object({
  created_at: z.string(),
  updated_at: z.string(),
  project_id: z.string(),
  config: projectPublicSchemaConfig,
});

export const projectLayerSchema = layerSchema.extend({
  id: z.number(),
  folder_id: z.string(),
  query: z
    .object({
      metadata: z.object({}).optional(),
      cql: z.object({}).optional(),
    })
    .nullable()
    .optional(),
  layer_id: z.string().uuid(),
  charts: z.object({}).optional(),
  filtered_count: z.number().optional(),
  legend_urls: z.array(z.string()).optional(),
});

export const projectViewStateSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  zoom: z.number().min(0).max(24),
  min_zoom: z.number().min(0).max(24),
  max_zoom: z.number().min(0).max(24),
  bearing: z.number().min(0).max(360),
  pitch: z.number().min(0).max(60),
});

export const postProjectSchema = z.object({
  folder_id: z.string().optional(),
  name: z.string().optional(),
  description: z.string().optional(),
  tags: z.array(z.string()).optional(),
  thumbnail_url: z.string().optional(),
  layer_order: z.array(z.number()).optional(),
  active_scenario_id: z.string().optional(),
  max_extent: z.tuple([z.number(), z.number(), z.number(), z.number()]).optional(),
  initial_view_state: projectViewStateSchema.optional(),
});

const getProjectsQueryParamsSchema = getContentQueryParamsSchema.extend({});

export const projectResponseSchema = responseSchema(projectSchema);
export const projectLayersResponseSchema = responseSchema(projectLayerSchema);

// Stats for project layer
export const aggregationStatsQueryParams = z
  .object({
    operation_type: statisticOperationEnum,
    operation_value: z.string().optional(),
    group_by_column_name: z.string().optional(),
    size: z.number().default(10),
    query: z.string().optional(),
    order: orderByEnum.optional(),
  })
  .superRefine((val, ctx) => {
    if (val.operation_type !== statisticOperationEnum.Values.count && !val.operation_value) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "operation_value is required unless operation_type is 'count'",
        path: ["operation_value"],
      });
    }
  })
  .transform((data) => {
    if (data.operation_type === statisticOperationEnum.Enum.count) {
      delete data.operation_value;
    }
    Object.keys(data).forEach((key) => {
      if (data[key] === undefined) {
        delete data[key];
      }
    });
    return data;
  });

export const aggregationStatsResponseSchema = z.object({
  items: z.array(
    z.object({
      grouped_value: z.string(),
      operation_value: z.number(),
    })
  ),
  total_items: z.number(),
  total_count: z.number(),
});

export const histogramStatsQueryParams = z.object({
  column_name: z.string(),
  num_bins: z.number().default(10),
  query: z.string().optional(),
  order: orderByEnum.optional(),
});

export const histogramStatsResponseSchema = z.object({
  bins: z.array(
    z.object({
      range: z.tuple([z.number(), z.number()]),
      count: z.number(),
    })
  ),
  missing_count: z.number(),
  total_rows: z.number(),
});

export type Project = z.infer<typeof projectSchema>;
export type ProjectLayer = z.infer<typeof projectLayerSchema>;
export type ProjectPaginated = z.infer<typeof projectResponseSchema>;
export type PostProject = z.infer<typeof postProjectSchema>;
export type ProjectViewState = z.infer<typeof projectViewStateSchema>;
export type ProjectLayersPaginated = z.infer<typeof projectLayersResponseSchema>;
export type GetProjectsQueryParams = z.infer<typeof getProjectsQueryParamsSchema>;
export type ProjectSharedWith = z.infer<typeof shareProjectSchema>;
export type ProjectPublic = z.infer<typeof projectPublicSchema>;
export type BuilderConfigSchema = z.infer<typeof builderConfigSchema>;
export type BuilderPanelSchema = z.infer<typeof builderPanelSchema>;
export type BuilderWidgetSchema = z.infer<typeof builderWidgetSchema>;
export type AggregationStatsQueryParams = z.infer<typeof aggregationStatsQueryParams>;
export type AggregationStatsResponse = z.infer<typeof aggregationStatsResponseSchema>;
export type HistogramStatsQueryParams = z.infer<typeof histogramStatsQueryParams>;
export type HistogramStatsResponse = z.infer<typeof histogramStatsResponseSchema>;
