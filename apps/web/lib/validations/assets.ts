import { z } from "zod";


export const ASSETS_MAX_FILE_SIZE_MB = 4; //mb

// Enum for AssetType
export const assetTypeEnum = z.enum(["image", "icon"]);

// UploadedAsset Zod schema
export const uploadedAssetSchema = z.object({
    id: z.string().uuid().optional(),
    file_name: z.string().max(255),
    display_name: z.string().max(255).nullable().optional(),
    category: z.string().max(100).nullable().optional(),
    user_id: z.string().uuid(),
    url: z.string().url(),
    mime_type: z.string().max(100),
    file_size: z.number().int().nonnegative(),
    asset_type: assetTypeEnum,
    created_at: z.string().datetime().optional(),
    updated_at: z.string().datetime().optional(),
});

export type UploadedAsset = z.infer<typeof uploadedAssetSchema>;
export type AssetTypeEnum = z.infer<typeof assetTypeEnum>;