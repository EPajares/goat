"""
OpenAPI/Swagger UI endpoint for OGC API Processes.

Serves OpenAPI 3.0 spec for OGC-compliant endpoints only.
"""

import os
import sys
from typing import Any, Dict

sys.path.insert(0, "/app/apps/processes/src")
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path

config = {
    "name": "OpenAPISpec",
    "type": "api",
    "path": "/openapi.json",
    "method": "GET",
    "description": "OpenAPI 3.0 specification for OGC API Processes",
    "emits": [],
}


def generate_openapi_spec(base_url: str) -> Dict[str, Any]:
    """Generate OpenAPI 3.0 specification for OGC API Processes."""

    # OGC API Processes compliant paths only
    paths = {
        "/ogc": {
            "get": {
                "summary": "Landing Page",
                "description": "OGC API Processes landing page with API links",
                "operationId": "getLandingPage",
                "tags": ["Capabilities"],
                "responses": {
                    "200": {
                        "description": "Landing page with links",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LandingPage"}
                            }
                        },
                    }
                },
            }
        },
        "/conformance": {
            "get": {
                "summary": "Conformance Declaration",
                "description": "List of OGC conformance classes implemented by this server",
                "operationId": "getConformance",
                "tags": ["Capabilities"],
                "responses": {
                    "200": {
                        "description": "Conformance classes",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ConfClasses"}
                            }
                        },
                    }
                },
            }
        },
        "/processes": {
            "get": {
                "summary": "Process List",
                "description": "Retrieve the list of available processes",
                "operationId": "getProcesses",
                "tags": ["Processes"],
                "responses": {
                    "200": {
                        "description": "List of processes",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ProcessList"}
                            }
                        },
                    }
                },
            }
        },
        "/processes/{processId}": {
            "get": {
                "summary": "Process Description",
                "description": "Retrieve the description of a specific process",
                "operationId": "getProcessDescription",
                "tags": ["Processes"],
                "parameters": [
                    {
                        "name": "processId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Process identifier",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Process description",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Process"}
                            }
                        },
                    },
                    "404": {
                        "description": "Process not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Exception"}
                            }
                        },
                    },
                },
            }
        },
        "/processes/{processId}/execution": {
            "post": {
                "summary": "Execute Process",
                "description": "Execute a process asynchronously, returning a job ID",
                "operationId": "execute",
                "tags": ["Processes"],
                "parameters": [
                    {
                        "name": "processId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Process identifier",
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Execute"}
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Job created (async execution)",
                        "headers": {
                            "Location": {
                                "description": "URL to the job status",
                                "schema": {"type": "string"},
                            }
                        },
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StatusInfo"}
                            }
                        },
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Exception"}
                            }
                        },
                    },
                    "404": {
                        "description": "Process not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Exception"}
                            }
                        },
                    },
                },
            }
        },
        "/jobs/{jobId}": {
            "get": {
                "summary": "Job Status",
                "description": "Retrieve the status of a job",
                "operationId": "getStatus",
                "tags": ["Jobs"],
                "parameters": [
                    {
                        "name": "jobId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"},
                        "description": "Job identifier",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Job status",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StatusInfo"}
                            }
                        },
                    },
                    "404": {
                        "description": "Job not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Exception"}
                            }
                        },
                    },
                },
            },
            "delete": {
                "summary": "Dismiss Job",
                "description": "Cancel a running job or remove a completed job",
                "operationId": "dismiss",
                "tags": ["Jobs"],
                "parameters": [
                    {
                        "name": "jobId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"},
                        "description": "Job identifier",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Job dismissed",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StatusInfo"}
                            }
                        },
                    },
                    "404": {
                        "description": "Job not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Exception"}
                            }
                        },
                    },
                },
            },
        },
        "/jobs": {
            "get": {
                "summary": "Job List",
                "description": "Retrieve the list of jobs",
                "operationId": "getJobs",
                "tags": ["Jobs"],
                "parameters": [
                    {
                        "name": "type",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Filter by process type (e.g., file_import, file_export)",
                    },
                    {
                        "name": "status",
                        "in": "query",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["accepted", "running", "successful", "failed", "dismissed"],
                        },
                        "description": "Filter by job status",
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 10},
                        "description": "Maximum number of jobs to return",
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 0, "default": 0},
                        "description": "Offset for pagination",
                    },
                ],
                "responses": {
                    "200": {
                        "description": "List of jobs",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/JobList"}
                            }
                        },
                    },
                },
            }
        },
        "/jobs/{jobId}/results": {
            "get": {
                "summary": "Job Results",
                "description": "Retrieve the results of a completed job",
                "operationId": "getResults",
                "tags": ["Jobs"],
                "parameters": [
                    {
                        "name": "jobId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"},
                        "description": "Job identifier",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Job results",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Results"}
                            }
                        },
                    },
                    "404": {
                        "description": "Job not found or results not available",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Exception"}
                            }
                        },
                    },
                },
            }
        },
    }

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "GOAT OGC API Processes",
            "description": "OGC API Processes compliant geospatial analysis service for GOAT",
            "version": "1.0.0",
            "contact": {
                "name": "GOAT Team",
            },
            "license": {
                "name": "MIT",
            },
        },
        "servers": [{"url": base_url, "description": "Current server"}],
        "tags": [
            {"name": "Capabilities", "description": "API capabilities and conformance"},
            {"name": "Processes", "description": "Process discovery and execution"},
            {"name": "Jobs", "description": "Job monitoring and management"},
        ],
        "paths": paths,
        "components": {
            "schemas": {
                "LandingPage": {
                    "type": "object",
                    "required": ["title", "links"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"},
                        },
                    },
                },
                "ConfClasses": {
                    "type": "object",
                    "required": ["conformsTo"],
                    "properties": {
                        "conformsTo": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                        }
                    },
                },
                "Link": {
                    "type": "object",
                    "required": ["href", "rel"],
                    "properties": {
                        "href": {"type": "string", "format": "uri"},
                        "rel": {"type": "string"},
                        "type": {"type": "string"},
                        "title": {"type": "string"},
                    },
                },
                "ProcessList": {
                    "type": "object",
                    "required": ["processes"],
                    "properties": {
                        "processes": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ProcessSummary"},
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"},
                        },
                    },
                },
                "ProcessSummary": {
                    "type": "object",
                    "required": ["id", "version"],
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "version": {"type": "string"},
                        "description": {"type": "string"},
                        "jobControlOptions": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["sync-execute", "async-execute", "dismiss"],
                            },
                        },
                        "outputTransmission": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["value", "reference"]},
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"},
                        },
                    },
                },
                "Process": {
                    "allOf": [
                        {"$ref": "#/components/schemas/ProcessSummary"},
                        {
                            "type": "object",
                            "properties": {
                                "inputs": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "$ref": "#/components/schemas/InputDescription"
                                    },
                                },
                                "outputs": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "$ref": "#/components/schemas/OutputDescription"
                                    },
                                },
                            },
                        },
                    ]
                },
                "InputDescription": {
                    "type": "object",
                    "required": ["schema"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "minOccurs": {"type": "integer", "default": 1},
                        "maxOccurs": {"type": "integer"},
                        "schema": {"type": "object"},
                    },
                },
                "OutputDescription": {
                    "type": "object",
                    "required": ["schema"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "schema": {"type": "object"},
                    },
                },
                "Execute": {
                    "type": "object",
                    "required": ["inputs"],
                    "properties": {
                        "inputs": {
                            "type": "object",
                            "description": "Process input values",
                        },
                        "outputs": {
                            "type": "object",
                            "description": "Requested outputs configuration",
                        },
                        "response": {
                            "type": "string",
                            "enum": ["raw", "document"],
                            "default": "document",
                            "description": "Response format",
                        },
                    },
                },
                "StatusInfo": {
                    "type": "object",
                    "required": ["jobID", "status", "type"],
                    "properties": {
                        "processID": {"type": "string"},
                        "type": {"type": "string", "enum": ["process"]},
                        "jobID": {"type": "string", "format": "uuid"},
                        "status": {
                            "type": "string",
                            "enum": [
                                "accepted",
                                "running",
                                "successful",
                                "failed",
                                "dismissed",
                            ],
                        },
                        "message": {"type": "string"},
                        "created": {"type": "string", "format": "date-time"},
                        "started": {"type": "string", "format": "date-time"},
                        "finished": {"type": "string", "format": "date-time"},
                        "updated": {"type": "string", "format": "date-time"},
                        "progress": {"type": "integer", "minimum": 0, "maximum": 100},
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"},
                        },
                    },
                },
                "JobList": {
                    "type": "object",
                    "required": ["jobs", "links"],
                    "properties": {
                        "jobs": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/StatusInfo"},
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"},
                        },
                        "numberMatched": {
                            "type": "integer",
                            "description": "Total number of jobs matching the query",
                        },
                        "numberReturned": {
                            "type": "integer",
                            "description": "Number of jobs returned in this response",
                        },
                    },
                },
                "Results": {
                    "type": "object",
                    "description": "Job results as key-value pairs where keys are output IDs",
                    "additionalProperties": True,
                },
                "Exception": {
                    "type": "object",
                    "required": ["type", "title"],
                    "properties": {
                        "type": {"type": "string", "format": "uri"},
                        "title": {"type": "string"},
                        "status": {"type": "integer"},
                        "detail": {"type": "string"},
                        "instance": {"type": "string", "format": "uri"},
                    },
                },
            }
        },
    }


async def handler(req, context):
    """Handle GET /openapi.json request."""
    default_host = os.environ.get("PROCESSES_HOST", "localhost")
    default_port = os.environ.get("PROCESSES_PORT", "8200")
    default_host_port = f"{default_host}:{default_port}"
    proto = req.get("headers", {}).get("x-forwarded-proto", "http")
    host = req.get("headers", {}).get("host", default_host_port)
    base_url = f"{proto}://{host}"

    context.logger.info("OpenAPI spec requested")

    spec = generate_openapi_spec(base_url)

    return {
        "status": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": spec,
    }
