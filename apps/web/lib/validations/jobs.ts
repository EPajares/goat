import * as z from "zod";

import { paginatedSchema } from "@/lib/validations/common";
import { responseSchema } from "@/lib/validations/response";

export const msgTypeEnum = z.enum(["info", "warning", "error"]);
export const jobTypeEnum = z.enum([
  "file_import",
  "join",
  "catchment_area_active_mobility",
  "catchment_area_pt",
  "catchment_area_car",
  "oev_gueteklasse",
  "heatmap_connectivity_active_mobility",
  "heatmap_connectivity_pt",
  "heatmap_connectivity_car",
  "heatmap_closest_average_active_mobility",
  "heatmap_closest_average_pt",
  "heatmap_closest_average_car",
  "heatmap_gravity_active_mobility",
  "heatmap_gravity_pt",
  "heatmap_gravity_car",
  "aggregate_point",
  "aggregate_polygon",
  "buffer",
  "trip_count_station",
  "origin_destination",
  "nearby_station_access",
  "print_report",
]);
export const jobStatusTypeEnum = z.enum(["pending", "running", "finished", "failed", "killed", "timeout"]);

export const msgSchema = z.object({
  type: msgTypeEnum,
  msg: z.string(),
});

const jobStepSchema = z.object({
  status: jobStatusTypeEnum.optional(),
  timestamp_start: z.date().nullable(),
  timestamp_end: z.date().nullable(),
  msg: msgSchema.optional(),
});

const jobStatusLayerUpload = z.object({
  validation: jobStepSchema.optional(),
  upload: jobStepSchema.optional(),
  migration: jobStepSchema.optional(),
});

// Payload schema for print_report jobs
export const printReportPayloadSchema = z.object({
  download_url: z.string().optional(),
  file_name: z.string().optional(),
  file_size_bytes: z.number().optional(),
  page_count: z.number().optional(),
  format: z.string().optional(),
  layout_id: z.string().uuid().optional(),
});

export const jobSchema = z.object({
  updated_at: z.string(),
  created_at: z.string(),
  id: z.string().uuid(),
  type: jobTypeEnum,
  status: jobStatusLayerUpload,
  status_simple: jobStatusTypeEnum,
  msg_simple: z.string().optional(),
  read: z.boolean().optional(),
  project_id: z.string().uuid().optional(),
  payload: z.record(z.unknown()).optional(),
});

export const getJobsQueryParamsSchema = paginatedSchema.extend({
  job_type: jobTypeEnum.optional(),
  project_id: z.string().uuid().optional(),
  start_data: z.string().optional(),
  read: z.boolean().optional(),
  end_data: z.string().optional(),
  authorization: z.string().optional(),
});

export const jobResponseSchema = responseSchema(jobSchema);

export type JobStatusType = z.infer<typeof jobStatusTypeEnum>;
export type JobType = z.infer<typeof jobTypeEnum>;
export type MsgType = z.infer<typeof msgTypeEnum>;
export type JobStep = z.infer<typeof jobStepSchema>;
export type Job = z.infer<typeof jobSchema>;
export type JobPaginated = z.infer<typeof jobResponseSchema>;
export type GetJobsQueryParam = z.infer<typeof getJobsQueryParamsSchema>;
export type PrintReportPayload = z.infer<typeof printReportPayloadSchema>;
