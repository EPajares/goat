import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { AssetTypeEnum, UploadedAsset } from "@/lib/validations/assets";
import { uploadedAssetSchema } from "@/lib/validations/assets";

export const ASSETS_API_BASE_URL = new URL("api/v2/asset", process.env.NEXT_PUBLIC_API_URL).href;

export const useAssets = (queryParams?: { asset_type?: AssetTypeEnum }) => {
    const { data, isLoading, error, mutate, isValidating } = useSWR<UploadedAsset[]>(
        [`${ASSETS_API_BASE_URL}`, queryParams],
        fetcher
    );
    return {
        assets: data,
        isLoading: isLoading,
        isError: error,
        mutate,
        isValidating,
    };
};

export const uploadAsset = async (
    file: File,
    assetType: AssetTypeEnum,
    options?: {
        displayName?: string;
        category?: string;
    }
): Promise<UploadedAsset> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("asset_type", assetType);

    if (options?.displayName) formData.append("display_name", options.displayName);
    if (options?.category) formData.append("category", options.category);

    const response = await apiRequestAuth(`${ASSETS_API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${errorText}`);
    }

    const data = await response.json();
    return uploadedAssetSchema.parse(data);
};

export const updateAsset = async (
    assetId: string,
    updates: {
        display_name?: string;
        category?: string;
    }
): Promise<UploadedAsset> => {
    const response = await apiRequestAuth(`${ASSETS_API_BASE_URL}/${assetId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Update failed: ${errorText}`);
    }

    const data = await response.json();
    return uploadedAssetSchema.parse(data);
};

export const deleteAsset = async (assetId: string): Promise<void> => {
    const response = await apiRequestAuth(`${ASSETS_API_BASE_URL}/${assetId}`, {
        method: "DELETE",
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Delete failed: ${errorText}`);
    }
    return;
};
