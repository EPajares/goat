import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { GetContentQueryParams } from "@/lib/validations/common";
import type { FolderResponse } from "@/lib/validations/folder";

export const FOLDERS_API_BASE_URL = new URL("api/v2/folder", process.env.NEXT_PUBLIC_API_URL).href;

export const useFolders = (queryParams?: GetContentQueryParams) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<FolderResponse>(
    [`${FOLDERS_API_BASE_URL}`, queryParams],
    fetcher
  );
  return {
    folders: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const deleteFolder = async (id: string) => {
  const response = await apiRequestAuth(`${FOLDERS_API_BASE_URL}/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete folder");
  }
  return await response;
};

export const createFolder = async (name: string) => {
  const response = await apiRequestAuth(`${FOLDERS_API_BASE_URL}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error("Failed to create folder");
  }
  return await response.json();
};

export const updateFolder = async (id: string, name: string) => {
  const response = await apiRequestAuth(`${FOLDERS_API_BASE_URL}/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error("Failed to update folder");
  }
  return await response.json();
};
