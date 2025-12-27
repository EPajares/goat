import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { ReportLayout, ReportLayoutCreate, ReportLayoutUpdate } from "@/lib/validations/reportLayout";

import { PROJECTS_API_BASE_URL } from "./projects";

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetch all report layouts for a project
 */
export const useReportLayouts = (projectId?: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ReportLayout[]>(
    () => (projectId ? [`${PROJECTS_API_BASE_URL}/${projectId}/report-layout`] : null),
    fetcher
  );

  return {
    reportLayouts: data,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

/**
 * Fetch a specific report layout
 */
export const useReportLayout = (projectId?: string, layoutId?: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ReportLayout>(
    () =>
      projectId && layoutId ? [`${PROJECTS_API_BASE_URL}/${projectId}/report-layout/${layoutId}`] : null,
    fetcher
  );

  return {
    reportLayout: data,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

// ============================================================================
// API Functions
// ============================================================================

/**
 * Create a new report layout
 */
export const createReportLayout = async (
  projectId: string,
  layout: ReportLayoutCreate
): Promise<ReportLayout> => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/report-layout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(layout),
  });
  if (!response.ok) {
    throw new Error("Failed to create report layout");
  }
  return await response.json();
};

/**
 * Update an existing report layout
 */
export const updateReportLayout = async (
  projectId: string,
  layoutId: string,
  layout: ReportLayoutUpdate
): Promise<ReportLayout> => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/report-layout/${layoutId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(layout),
  });
  if (!response.ok) {
    throw new Error("Failed to update report layout");
  }
  return await response.json();
};

/**
 * Delete a report layout
 */
export const deleteReportLayout = async (projectId: string, layoutId: string): Promise<void> => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/report-layout/${layoutId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete report layout");
  }
};

/**
 * Duplicate a report layout
 */
export const duplicateReportLayout = async (
  projectId: string,
  layoutId: string,
  newName?: string
): Promise<ReportLayout> => {
  let url = `${PROJECTS_API_BASE_URL}/${projectId}/report-layout/${layoutId}/duplicate`;
  if (newName) {
    url += `?new_name=${encodeURIComponent(newName)}`;
  }
  const response = await apiRequestAuth(url, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to duplicate report layout");
  }
  return await response.json();
};
