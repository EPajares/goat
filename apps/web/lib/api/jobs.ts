import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { GetJobsQueryParam, JobPaginated } from "@/lib/validations/jobs";
import { type Job, jobSchema } from "@/lib/validations/jobs";

export const JOBS_API_BASE_URL = new URL("api/v2/job", process.env.NEXT_PUBLIC_API_URL).href;

export const useJobs = (queryParams?: GetJobsQueryParam) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<JobPaginated>(
    [`${JOBS_API_BASE_URL}`, queryParams],
    fetcher
  );
  return {
    jobs: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const getJob = async (id: string): Promise<Job> => {
  const response = await apiRequestAuth(`${JOBS_API_BASE_URL}/${id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to delete folder");
  }
  const json = await response.json();
  const parsed = jobSchema.safeParse(json);
  if (!parsed.success) {
    throw new Error("Failed to parse job");
  }

  return parsed.data;
};

export const setJobsReadStatus = async (ids: string[]) => {
  const response = await apiRequestAuth(`${JOBS_API_BASE_URL}/read`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(ids),
  });
  if (!response.ok) {
    throw new Error("Failed to set jobs read status");
  }

  return true;
};
