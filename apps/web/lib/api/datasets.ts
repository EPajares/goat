import { apiRequestAuth } from "@/lib/api/fetcher";
import type { DatasetImportRequest, PresignedPostResponse } from "@/lib/validations/datasets";
import { datasetImportRequestSchema, presignedPostResponseSchema } from "@/lib/validations/datasets";


export const DATASET_IMPORTS_API_BASE_URL = new URL(
    "api/v2/datasets",
    process.env.NEXT_PUBLIC_API_URL
).href;

export const requestDatasetUpload = async (
    req: DatasetImportRequest
): Promise<PresignedPostResponse> => {
    // validate client input with zod first
    const validatedReq = datasetImportRequestSchema.parse(req);

    const response = await apiRequestAuth(`${DATASET_IMPORTS_API_BASE_URL}/request-upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(validatedReq),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Request upload failed: ${errorText}`);
    }

    const data = await response.json();
    return presignedPostResponseSchema.parse(data);
};