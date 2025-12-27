import type { SystemSettings } from "@/lib/validations/system";

export const getSystemSettings = async (token: string): Promise<SystemSettings | null> => {
  const SYSTEM_API_BASE_URL = new URL("api/v2/system", process.env.NEXT_PUBLIC_API_URL).href;
  if (!token) return null;
  const res = await fetch(`${SYSTEM_API_BASE_URL}/settings`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return null;
  return res.json();
};
