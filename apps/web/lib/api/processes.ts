/**
 * OGC API Processes client
 *
 * This module provides functions to interact with the OGC API Processes
 * service for:
 * - Process execution (analytics tools, layer operations)
 * - Job status tracking and management
 * - Analytics operations (feature-count, class-breaks, etc.)
 */
import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import { PROCESSES_BASE_URL } from "@/lib/constants";

// OGC API Processes base URLs
export const PROCESSES_API_BASE_URL = `${PROCESSES_BASE_URL}/processes`;
export const JOBS_API_BASE_URL = `${PROCESSES_BASE_URL}/jobs`;

// ============================================================================
// Types for OGC API Processes
// ============================================================================

export interface ProcessSummary {
  id: string;
  title: string;
  description: string;
  version: string;
  jobControlOptions: string[];
  outputTransmission: string[];
  links: ProcessLink[];
}

export interface ProcessLink {
  href: string;
  rel: string;
  type: string;
  title?: string;
}

export interface ProcessList {
  processes: ProcessSummary[];
  links: ProcessLink[];
}

// ============================================================================
// OGC Job Types
// ============================================================================

/**
 * OGC API Processes job status types
 * See: https://docs.ogc.org/is/18-062r2/18-062r2.html#sc_job_status
 */
export type JobStatusType = "accepted" | "running" | "successful" | "failed" | "dismissed";

/**
 * Process/Job types (process IDs)
 */
export type JobType =
  | "LayerImport"
  | "LayerExport"
  | "LayerUpdate"
  | "LayerDelete"
  | "buffer"
  | "join"
  | "catchment_area_active_mobility"
  | "catchment_area_pt"
  | "catchment_area_car"
  | "oev_gueteklasse"
  | "heatmap_connectivity_active_mobility"
  | "heatmap_connectivity_pt"
  | "heatmap_connectivity_car"
  | "heatmap_closest_average_active_mobility"
  | "heatmap_closest_average_pt"
  | "heatmap_closest_average_car"
  | "heatmap_gravity_active_mobility"
  | "heatmap_gravity_pt"
  | "heatmap_gravity_car"
  | "aggregate_point"
  | "aggregate_polygon"
  | "trip_count_station"
  | "origin_destination"
  | "nearby_station_access"
  | "print_report";

/**
 * OGC Job status response
 */
export interface Job {
  jobID: string;
  processID: JobType;
  status: JobStatusType;
  message?: string;
  created?: string;
  started?: string;
  finished?: string;
  updated?: string;
  progress?: number;
  links?: ProcessLink[];
  // Extended fields from our implementation
  user_id?: string;
  read?: boolean;
  project_id?: string;
  payload?: Record<string, unknown>;
}

/**
 * Paginated jobs response
 */
export interface JobsResponse {
  jobs: Job[];
  links?: ProcessLink[];
  numberMatched?: number;
  numberReturned?: number;
}

/**
 * Query parameters for listing jobs
 */
export interface GetJobsQueryParams {
  status?: JobStatusType;
  processID?: JobType;
  limit?: number;
  offset?: number;
  read?: boolean; // Filter by read status
}

// Feature Count types
export interface FeatureCountInput {
  collection: string;
  filter?: string;
}

export interface FeatureCountOutput {
  count: number;
}

// Area Statistics types
export type AreaStatisticsOperation = "sum" | "mean" | "min" | "max";

export interface AreaStatisticsInput {
  collection: string;
  operation: AreaStatisticsOperation;
  filter?: string;
}

export interface AreaStatisticsOutput {
  total_area: number;
  feature_count: number;
  result: number;
  unit: string;
}

// Unique Values types
export type UniqueValuesOrder = "ascendent" | "descendent";

export interface UniqueValuesInput {
  collection: string;
  attribute: string;
  order?: UniqueValuesOrder;
  filter?: string;
  limit?: number;
  offset?: number;
}

export interface UniqueValue {
  value: string | number | null;
  count: number;
}

export interface UniqueValuesOutput {
  attribute: string;
  total: number;
  values: UniqueValue[];
}

// Class Breaks types
export type ClassBreaksMethod = "quantile" | "equal_interval" | "standard_deviation" | "heads_and_tails";

export interface ClassBreaksInput {
  collection: string;
  attribute: string;
  method: ClassBreaksMethod;
  breaks: number;
  filter?: string;
  strip_zeros?: boolean;
}

export interface ClassBreaksOutput {
  attribute: string;
  method: string;
  breaks: number[];
  min: number | null;
  max: number | null;
  mean: number | null;
  std_dev: number | null;
}

// Generic process execution request/response
export interface ProcessExecuteRequest<T> {
  inputs: T;
}

// ============================================================================
// Process execution functions
// ============================================================================

/**
 * Execute a process on the GeoAPI server
 */
async function executeProcess<TInput, TOutput>(processId: string, inputs: TInput): Promise<TOutput> {
  const response = await apiRequestAuth(`${PROCESSES_API_BASE_URL}/${processId}/execution`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inputs }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.detail || error.detail || `Process execution failed: ${processId}`);
  }

  return await response.json();
}

/**
 * Execute a process and return the job status (for async processes)
 */
export async function executeProcessAsync<TInput>(processId: string, inputs: TInput): Promise<Job> {
  const response = await apiRequestAuth(`${PROCESSES_API_BASE_URL}/${processId}/execution`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inputs }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.detail || error.detail || `Process execution failed: ${processId}`);
  }

  return await response.json();
}

// ============================================================================
// Job Management Functions
// ============================================================================

/**
 * Get job status by ID
 */
export async function getJob(jobId: string): Promise<Job> {
  const response = await apiRequestAuth(`${JOBS_API_BASE_URL}/${jobId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to get job: ${jobId}`);
  }

  return await response.json();
}

/**
 * Dismiss/cancel a job
 */
export async function dismissJob(jobId: string): Promise<void> {
  const response = await apiRequestAuth(`${JOBS_API_BASE_URL}/${jobId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to dismiss job: ${jobId}`);
  }
}

/**
 * Mark jobs as read (clear from notification list)
 * For completed jobs, this dismisses them from the system
 */
export async function setJobsReadStatus(jobIds: string[]): Promise<void> {
  // Dismiss all jobs to clear them from the notification list
  // This is the OGC-standard way to remove jobs from the system
  const results = await Promise.allSettled(jobIds.map((id) => dismissJob(id)));

  // Log any failures but don't throw
  const failures = results.filter((r) => r.status === "rejected");
  if (failures.length > 0) {
    console.warn(`Failed to dismiss ${failures.length} of ${jobIds.length} jobs`);
  }
}

// ============================================================================
// Job SWR Hooks
// ============================================================================

/**
 * Hook to fetch and poll jobs list
 */
export function useJobs(queryParams?: GetJobsQueryParams) {
  const { data, isLoading, error, mutate, isValidating } = useSWR<JobsResponse>(
    [`${JOBS_API_BASE_URL}`, queryParams],
    fetcher,
    {
      refreshInterval: 5000, // Poll every 5 seconds
    }
  );

  return {
    jobs: data,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
}

/**
 * Hook to fetch and poll a single job by ID
 */
export function useJob(jobId?: string, refreshInterval = 2000) {
  const { data, isLoading, error, mutate } = useSWR<Job>(
    jobId ? [`${JOBS_API_BASE_URL}/${jobId}`] : null,
    fetcher,
    {
      refreshInterval: (data) => {
        if (!data) return refreshInterval;
        // Stop polling when job is finished
        if (data.status === "successful" || data.status === "failed" || data.status === "dismissed") {
          return 0;
        }
        return refreshInterval;
      },
    }
  );

  return {
    job: data,
    isLoading,
    isError: error,
    mutate,
  };
}

/**
 * Get feature count for a collection
 */
export async function getFeatureCount(layerId: string, filter?: string): Promise<FeatureCountOutput> {
  const inputs: FeatureCountInput = {
    collection: layerId,
    ...(filter && { filter }),
  };
  return executeProcess<FeatureCountInput, FeatureCountOutput>("feature-count", inputs);
}

/**
 * Get area statistics for a polygon collection
 */
export async function getAreaStatistics(
  layerId: string,
  operation: AreaStatisticsOperation,
  filter?: string
): Promise<AreaStatisticsOutput> {
  const inputs: AreaStatisticsInput = {
    collection: layerId,
    operation,
    ...(filter && { filter }),
  };
  return executeProcess<AreaStatisticsInput, AreaStatisticsOutput>("area-statistics", inputs);
}

/**
 * Get unique values for an attribute in a collection
 */
export async function getUniqueValues(
  layerId: string,
  attribute: string,
  options?: {
    order?: UniqueValuesOrder;
    filter?: string;
    limit?: number;
    offset?: number;
  }
): Promise<UniqueValuesOutput> {
  const inputs: UniqueValuesInput = {
    collection: layerId,
    attribute,
    ...options,
  };
  return executeProcess<UniqueValuesInput, UniqueValuesOutput>("unique-values", inputs);
}

/**
 * Get class breaks for a numeric attribute
 */
export async function getClassBreaks(
  layerId: string,
  attribute: string,
  method: ClassBreaksMethod,
  breaks: number,
  options?: {
    filter?: string;
    strip_zeros?: boolean;
  }
): Promise<ClassBreaksOutput> {
  const inputs: ClassBreaksInput = {
    collection: layerId,
    attribute,
    method,
    breaks,
    ...options,
  };
  return executeProcess<ClassBreaksInput, ClassBreaksOutput>("class-breaks", inputs);
}

// ============================================================================
// SWR Hooks for process results
// ============================================================================

/**
 * Hook to get class breaks using SWR
 */
export function useClassBreaks(
  layerId: string | undefined,
  attribute: string | undefined,
  method: ClassBreaksMethod | undefined,
  breaks: number | undefined,
  options?: {
    filter?: string;
    strip_zeros?: boolean;
  }
) {
  const shouldFetch = layerId && attribute && method && breaks;

  const { data, isLoading, error, mutate } = useSWR<ClassBreaksOutput>(
    shouldFetch
      ? [
          `${PROCESSES_API_BASE_URL}/class-breaks/execution`,
          {
            inputs: {
              collection: layerId,
              attribute,
              method,
              breaks,
              ...options,
            },
          },
        ]
      : null,
    async ([url, body]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || error.detail || "Failed to get class breaks");
      }
      return response.json();
    }
  );

  return {
    classBreaks: data,
    isLoading,
    isError: error,
    mutate,
  };
}

/**
 * Hook to get unique values using SWR
 */
export function useUniqueValues(
  layerId: string | undefined,
  attribute: string | undefined,
  options?: {
    order?: UniqueValuesOrder;
    filter?: string;
    limit?: number;
    offset?: number;
  }
) {
  const shouldFetch = layerId && attribute;

  const { data, isLoading, error, mutate, isValidating } = useSWR<UniqueValuesOutput>(
    shouldFetch
      ? [
          `${PROCESSES_API_BASE_URL}/unique-values/execution`,
          {
            inputs: {
              collection: layerId,
              attribute,
              ...options,
            },
          },
        ]
      : null,
    async ([url, body]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || error.detail || "Failed to get unique values");
      }
      return response.json();
    }
  );

  return {
    data,
    isLoading,
    error,
    mutate,
    isValidating,
  };
}

/**
 * Hook to get feature count using SWR
 */
export function useFeatureCount(layerId: string | undefined, filter?: string) {
  const shouldFetch = !!layerId;

  const { data, isLoading, error, mutate } = useSWR<FeatureCountOutput>(
    shouldFetch
      ? [
          `${PROCESSES_API_BASE_URL}/feature-count/execution`,
          {
            inputs: {
              collection: layerId,
              ...(filter && { filter }),
            },
          },
        ]
      : null,
    async ([url, body]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || error.detail || "Failed to get feature count");
      }
      return response.json();
    }
  );

  return {
    featureCount: data?.count,
    isLoading,
    isError: error,
    mutate,
  };
}
