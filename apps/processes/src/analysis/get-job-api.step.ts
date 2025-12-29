import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";

/**
 * Get job status API endpoint.
 *
 * Returns the status and details of an analysis job by ID.
 */

export const config: ApiRouteConfig = {
  name: "GetJobAPI",
  type: "api",
  path: "/jobs/:jobId",
  method: "GET",
  description: "Get status and details of an analysis job",
  emits: [],
  flows: ["analysis-flow"],
  responseSchema: {
    200: z.object({
      jobId: z.string(),
      status: z.string(),
      tool_name: z.string().optional(),
      output_layer_id: z.string().optional(),
      feature_count: z.number().optional(),
      error: z.string().optional(),
    }),
    404: z.object({
      error: z.string(),
    }),
  },
};

export const handler: Handlers["GetJobAPI"] = async (req, { logger, state }) => {
  const { jobId } = req.pathParams;

  logger.info("Getting job status", { jobId });

  // TODO: Look up job in state/database
  // For now, return a placeholder
  // In production, you'd store job status in Redis/database via the log step

  return {
    status: 200,
    body: {
      jobId,
      status: "unknown",
      // In production: retrieve actual status from state store
    },
  };
};
