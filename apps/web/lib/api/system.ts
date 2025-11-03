import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { SystemSettings, SystemSettingsUpdate } from "@/lib/validations/system";

export const SYSTEM_API_BASE_URL = new URL("api/v2/system", process.env.NEXT_PUBLIC_API_URL).href;

export const useSystemSettings = () => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<SystemSettings>(
    `${SYSTEM_API_BASE_URL}/settings`,
    fetcher
  );
  return {
    systemSettings: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const updateSystemSettings = async (
  system_settings: SystemSettingsUpdate
): Promise<SystemSettings> => {
  const response = await apiRequestAuth(`${SYSTEM_API_BASE_URL}/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(system_settings),
  });
  if (!response.ok) {
    throw new Error("Failed to update system settings");
  }
  return await response.json();
};
