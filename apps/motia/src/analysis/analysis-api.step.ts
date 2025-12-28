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
 */

export const config: ApiRouteConfig = {
  name: "AnalysisAPI",
  type: "api",
  path: "/:tool_name",
  method: "POST",
  description: "Triggers any goatlib analysis tool as a background task",
  emits: ["analysis-requested"],
  flows: ["analysis-flow"],
  bodySchema: z.object({
    // Required: user context
    user_id: z.string().uuid().describe("UUID of the user who owns the layers"),

    // Required for most tools: input layer
    input_layer_id: z.string().uuid().describe("UUID of the primary input layer"),

    // Optional: overlay layer (for clip, intersection, etc.)
    overlay_layer_id: z.string().uuid().optional().describe("UUID of the overlay layer"),

    // Optional: filters
    input_filter: z.string().optional().describe("SQL WHERE clause to filter input layer"),
    overlay_filter: z.string().optional().describe("SQL WHERE clause to filter overlay layer"),

    // Optional: output
    output_layer_id: z
      .string()
      .uuid()
      .optional()
      .describe("UUID for output layer (auto-generated if not provided)"),
    output_crs: z.string().optional().describe("Target CRS for output (e.g., EPSG:4326)"),
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

  const {
    user_id,
    input_layer_id,
    overlay_layer_id,
    input_filter,
    overlay_filter,
    output_layer_id,
    output_crs,
  } = req.body;

  // Validate required fields
  if (!tool_name || !user_id || !input_layer_id) {
    return {
      status: 400,
      body: {
        error: "tool_name (in URL), user_id, and input_layer_id are required",
      },
    };
  }

  // Tool-specific validation
  if (tool_name === "clip" && !overlay_layer_id) {
    return {
      status: 400,
      body: {
        error: "overlay_layer_id is required for clip tool",
      },
    };
  }

  const jobId = `${tool_name}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  const timestamp = new Date().toISOString();

  // Generate output layer ID if not provided
  const finalOutputLayerId = output_layer_id || crypto.randomUUID();

  logger.info("Analysis API endpoint called", {
    jobId,
    tool_name,
    user_id,
    input_layer_id,
    overlay_layer_id,
  });

  // Build event payload with all params
  const eventData: Record<string, unknown> = {
    jobId,
    timestamp,
    tool_name,
    user_id,
    input_layer_id,
    overlay_layer_id: overlay_layer_id || null,
    input_filter: input_filter || null,
    overlay_filter: overlay_filter || null,
    output_layer_id: finalOutputLayerId,
    output_crs: output_crs || "EPSG:4326",
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
      output_layer_id: finalOutputLayerId,
    },
  };
};
