"""
Swagger UI endpoint.
GET /swagger

Serves Swagger UI HTML that loads OpenAPI spec from /openapi.json
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

config = {
    "name": "SwaggerUI",
    "type": "api",
    "path": "/swagger",
    "method": "GET",
    "description": "Swagger UI for API documentation and testing",
    "emits": [],
}

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GOAT Analysis API - Swagger UI</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>
    html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }
    .swagger-ui .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      window.ui = SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout",
        defaultModelsExpandDepth: 1,
        defaultModelExpandDepth: 1,
        tryItOutEnabled: true,
      });
    };
  </script>
</body>
</html>"""


async def handler(req, context):
    """Handle GET /swagger request - Swagger UI."""
    context.logger.info("Swagger UI requested")

    return {
        "status": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
        },
        "body": SWAGGER_HTML,
    }
