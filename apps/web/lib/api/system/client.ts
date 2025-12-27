// lib/api/system.ts
import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { SystemSettings, SystemSettingsUpdate } from "@/lib/validations/system";

export const SYSTEM_API_BASE_URL = new URL("api/v2/system", process.env.NEXT_PUBLIC_API_URL).href;

/**
 * SWR hook that fetches the logged‑in user's system settings from FastAPI
 */
export const useSystemSettings = () => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<SystemSettings>(
    `${SYSTEM_API_BASE_URL}/settings`,
    fetcher
  );

  return {
    systemSettings: data,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

/**
 * Update system settings (PUT /settings)
 */
export const updateSystemSettings = async (
  body: SystemSettingsUpdate,
  token: string
): Promise<SystemSettings | null> => {
  if (!token) return null;
  const res = await apiRequestAuth(`${SYSTEM_API_BASE_URL}/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to update system settings");
  // backend response is validated/normalized — use that
  return res.json();
};
