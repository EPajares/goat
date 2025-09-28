import { z } from "zod";

// Request schema
export const datasetImportRequestSchema = z.object({
    filename: z.string().min(1),
    content_type: z.string().default("application/octet-stream"),
    file_size: z.number().positive(),
});

export type DatasetImportRequest = z.infer<typeof datasetImportRequestSchema>;

// Response schema (presigned POST)
export const presignedPostResponseSchema = z.object({
    url: z.string().url(),
    fields: z.record(z.string()),
});

export type PresignedPostResponse = z.infer<typeof presignedPostResponseSchema>;