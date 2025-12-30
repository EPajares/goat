/**
 * OGC API Processes client
 *
 * This module provides functions to interact with the OGC API Processes
 * service for analytics operations like:
 * - feature-count: Count features with optional CQL2 filter
 * - area-statistics: Calculate area statistics for polygon layers
 * - unique-values: Get unique values with occurrence counts
 * - class-breaks: Calculate classification breaks for numeric attributes
 */
import useSWR from "swr";

import { apiRequestAuth } from "@/lib/api/fetcher";
import { PROCESSES_BASE_URL } from "@/lib/constants";

// OGC API Processes base URL
export const PROCESSES_API_BASE_URL = `${PROCESSES_BASE_URL}/processes`;

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
