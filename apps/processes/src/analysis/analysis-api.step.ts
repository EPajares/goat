import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";

/**
 * Generic Analysis API endpoint with RESTful paths.
 *
 * This single API handles ALL goatlib analysis tools via URL path:
 *   POST /clip
 *   POST /buffer
 *   POST /intersection
 *   etc.
 *
 * Tools are auto-discovered from goatlib - any class following the naming convention:
 * - *Params (schema) → auto-generates *LayerParams
 * - *Tool (execution)
 *
 * will be automatically available at /{tool_name}
 *
 * The request body is passed through to Python where the tool registry
 * validates it against the dynamically generated LayerParams schema.
 */

export const config: ApiRouteConfig = {
  name: "AnalysisAPI",
  type: "api",
  path: "/:tool_name",
  method: "POST",
  description: "Triggers any goatlib analysis tool as a background task",
  emits: ["analysis-requested"],
  flows: ["analysis-flow"],
  // Flexible schema - actual validation happens in Python against the tool's LayerParams
  bodySchema: z.object({
    user_id: z.string().describe("UUID of the user who owns the layers"),
  }),
  responseSchema: {
    200: z.object({
      message: z.string(),
      status: z.string(),
      jobId: z.string(),
      tool_name: z.string(),
      output_layer_id: z.string(),
    }),
    400: z.object({
      error: z.string(),
    }),
  },
};

export const handler: Handlers["AnalysisAPI"] = async (req, { emit, logger }) => {
  // Get tool_name from URL path parameter
  const tool_name = req.pathParams?.tool_name;
  const { user_id, ...toolParams } = req.body;

  // Validate required fields
  if (!tool_name || !user_id) {
    return {
      status: 400,
      body: {
        error: "tool_name (in URL) and user_id are required",
      },
    };
  }

  const jobId = `${tool_name}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  const timestamp = new Date().toISOString();

  // Generate output layer ID if not provided
  const output_layer_id = toolParams.output_layer_id || crypto.randomUUID();

  logger.info("Analysis API endpoint called", {
    jobId,
    tool_name,
    user_id,
  });

  // Build event payload - pass all params through for Python validation
  const eventData: Record<string, unknown> = {
    jobId,
    timestamp,
    tool_name,
    user_id,
    output_layer_id,
    ...toolParams, // Pass all tool-specific params through
  };

  // Emit event for background processing in Python
  await emit({
    topic: "analysis-requested",
    data: eventData,
  });

  return {
    status: 200,
    body: {
      message: `${tool_name} job submitted for background processing`,
      status: "processing",
      jobId,
      tool_name,
      output_layer_id,
    },
  };
};
