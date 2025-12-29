import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";

/**
 * OGC API Processes - Landing Page
 * GET /ogc
 *
 * Returns links to API endpoints per OGC spec.
 */

export const config: ApiRouteConfig = {
  name: "OGCLandingPage",
  type: "api",
  path: "/ogc",
  method: "GET",
  description: "OGC API Processes landing page with API links",
  emits: [],
  responseSchema: {
    200: z.object({
      title: z.string(),
      description: z.string().optional(),
      links: z.array(
        z.object({
          href: z.string(),
          rel: z.string(),
          type: z.string().optional(),
          title: z.string().optional(),
        })
      ),
    }),
  },
};

export const handler: Handlers["OGCLandingPage"] = async (req, { logger }) => {
  const defaultHost = process.env.PROCESSES_HOST || "localhost";
  const defaultPort = process.env.PROCESSES_PORT || "8200";
  const defaultHostPort = `${defaultHost}:${defaultPort}`;
  const baseUrl = `${req.headers["x-forwarded-proto"] || "http"}://${req.headers.host || defaultHostPort}`;

  logger.info("OGC Landing page requested", { baseUrl });

  return {
    status: 200,
    body: {
      title: "GOAT Analysis API",
      description: "OGC API Processes for geospatial analysis tools",
      links: [
        {
          href: baseUrl,
          rel: "self",
          type: "application/json",
          title: "This document",
        },
        {
          href: `${baseUrl}/openapi.json`,
          rel: "service-desc",
          type: "application/openapi+json;version=3.0",
          title: "API definition",
        },
        {
          href: `${baseUrl}/conformance`,
          rel: "http://www.opengis.net/def/rel/ogc/1.0/conformance",
          type: "application/json",
          title: "Conformance classes",
        },
        {
          href: `${baseUrl}/processes`,
          rel: "http://www.opengis.net/def/rel/ogc/1.0/processes",
          type: "application/json",
          title: "Processes",
        },
        {
          href: `${baseUrl}/jobs`,
          rel: "http://www.opengis.net/def/rel/ogc/1.0/job-list",
          type: "application/json",
          title: "Jobs",
        },
      ],
    },
  };
};
