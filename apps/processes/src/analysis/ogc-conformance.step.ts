import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";

/**
 * OGC API Processes - Conformance
 * GET /conformance
 *
 * Returns list of conformance classes the API implements.
 */

const PROCESSES_CONFORMANCE = [
  "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
  "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
  "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
  "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list",
  "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/dismiss",
];

export const config: ApiRouteConfig = {
  name: "OGCConformance",
  type: "api",
  path: "/conformance",
  method: "GET",
  description: "OGC API Processes conformance classes",
  emits: [],
  responseSchema: {
    200: z.object({
      conformsTo: z.array(z.string()),
    }),
  },
};

export const handler: Handlers["OGCConformance"] = async (_req, { logger }) => {
  logger.info("OGC Conformance requested");

  return {
    status: 200,
    body: {
      conformsTo: PROCESSES_CONFORMANCE,
    },
  };
};
