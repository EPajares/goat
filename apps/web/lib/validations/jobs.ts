/**
 * Job validations - OGC API Processes compatible
 *
 * Types are primarily defined in lib/api/processes.ts
 * This file re-exports for backward compatibility during migration
 */

// Re-export types from processes.ts for components that still use this import path
export type { Job, JobStatusType, JobType, GetJobsQueryParams, JobsResponse } from "@/lib/api/processes";

// Job type enum for runtime validation (matches processID values)
export const jobTypeValues = [
  "layer_import",
  "layer_export",
  "layer_update",
  "layer_delete",
  "print_report",
  "buffer",
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
  "trip_count_station",
  "origin_destination",
  "nearby_station_access",
] as const;

// Job status enum for runtime validation (OGC status codes)
export const jobStatusValues = ["accepted", "running", "successful", "failed", "dismissed"] as const;

// Helper to check if a process is still running
export function isJobRunning(status: string): boolean {
  return status === "accepted" || status === "running";
}

// Helper to check if a process completed successfully
export function isJobSuccessful(status: string): boolean {
  return status === "successful";
}

// Helper to check if a process failed
export function isJobFailed(status: string): boolean {
  return status === "failed" || status === "dismissed";
}

/**
 * Backward compatible enum-like object for job types
 * Used by components that import jobTypeEnum from this file
 */
export const jobTypeEnum = {
  Enum: {
    layer_import: "layer_import",
    layer_export: "layer_export",
    layer_update: "layer_update",
    layer_delete: "layer_delete",
    print_report: "print_report",
    buffer: "buffer",
    join: "join",
    catchment_area_active_mobility: "catchment_area_active_mobility",
    catchment_area_pt: "catchment_area_pt",
    catchment_area_car: "catchment_area_car",
    oev_gueteklasse: "oev_gueteklasse",
    heatmap_connectivity_active_mobility: "heatmap_connectivity_active_mobility",
    heatmap_connectivity_pt: "heatmap_connectivity_pt",
    heatmap_connectivity_car: "heatmap_connectivity_car",
    heatmap_closest_average_active_mobility: "heatmap_closest_average_active_mobility",
    heatmap_closest_average_pt: "heatmap_closest_average_pt",
    heatmap_closest_average_car: "heatmap_closest_average_car",
    heatmap_gravity_active_mobility: "heatmap_gravity_active_mobility",
    heatmap_gravity_pt: "heatmap_gravity_pt",
    heatmap_gravity_car: "heatmap_gravity_car",
    aggregate_point: "aggregate_point",
    aggregate_polygon: "aggregate_polygon",
    trip_count_station: "trip_count_station",
    origin_destination: "origin_destination",
    nearby_station_access: "nearby_station_access",
  } as const,
} as const;
