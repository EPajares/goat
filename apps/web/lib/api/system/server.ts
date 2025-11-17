import type { SystemSettings, SystemSettingsUpdate } from "@/lib/validations/system";

export const SYSTEM_API_BASE_URL = new URL(
    "api/v2/system",
    process.env.NEXT_PUBLIC_API_URL
).href;

export const getSystemSettings = async (token: string): Promise<SystemSettings | null> => {
    if (!token) return null;
    const res = await fetch(`${SYSTEM_API_BASE_URL}/settings`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return res.json();
};

export const updateSystemSettings = async (
    body: SystemSettingsUpdate,
    token: string
): Promise<SystemSettings | null> => {
    if (!token) return null;
    const res = await fetch(`${SYSTEM_API_BASE_URL}/settings`, {
        method: "PUT",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("Failed to update system settings");
    return res.json();
};