<div id="top"></div>

<p align="center">
<a href="https://plan4better.de/goat" target="_blank" rel="noopener noreferrer">
<img width="120" alt="GOAT Frontend Alternative Logo" src="https://assets.plan4better.de/img/logo/goat_icon_standard.png">
</a>

<h1 align="center">GOAT</h1>

<p align="center">
Intelligent software for modern web mapping and integrated planning
<br />
<a href="https://plan4better.de/goat" target="_blank" rel="noopener noreferrer">Website</a>
</p>
</p>

<p align="center">
   <a href="https://github.com/plan4better/goat/blob/main/LICENSE" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/License-GPLv3-purple" alt="License"></a>
   <a href="https://github.com/plan4better/goat/pulse" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/github/commit-activity/m/plan4better/goat" alt="Commits-per-month"></a>
    <a href="https://github.com/plan4better/goat/issues?q=is:issue+is:open+label:%22%F0%9F%99%8B%F0%9F%8F%BB%E2%80%8D%E2%99%82%EF%B8%8Fhelp+wanted%22" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Help%20Wanted-Contribute-blue"></a>
</p>

<br/>

## ✨ About GOAT

<p align="center">
  <picture>
    <!-- Dark theme -->
    <source srcset="apps/docs/assets/goat_screenshot_dark.webp" media="(prefers-color-scheme: dark)">
    <!-- Light theme -->
    <source srcset="apps/docs/assets/goat_screenshot_light.webp" media="(prefers-color-scheme: light)">
    <!-- Fallback -->
    <img src="apps/docs/assets/goat_screenshot_light.webp" alt="GOAT Screenshot" width="1527">
  </picture>
</p>


<br/>

GOAT is a free and open source WebGIS platform. It is an all-in-one solution for integrated planning, with powerful GIS tools, integrated data, and comprehensive accessibility analyses for efficient planning and fact-based decision-making.

**Try it out in the cloud at <a href="https://goat.plan4better.de" target="_blank" rel="noopener noreferrer">goat.plan4better.de</a>**

For more information check out:

<a href="https://goat.plan4better.de/docs" target="_blank" rel="noopener noreferrer">GOAT Docs</a>

<a href="https://www.linkedin.com/company/plan4better" target="_blank" rel="noopener noreferrer">Follow GOAT on LinkedIn</a>

<a href="https://twitter.com/plan4better" target="_blank" rel="noopener noreferrer">Follow GOAT on Twitter</a>

<br/>

## Built on Open Source

GOAT is a **monorepo** project leveraging a modern, full-stack architecture.

### Frontend & Shared UI Components

- 💻 <a href="https://www.typescriptlang.org/" target="_blank" rel="noopener noreferrer">Typescript</a>

- 🚀 <a href="https://nextjs.org/" target="_blank" rel="noopener noreferrer">Next.js</a>

- ⚛️ <a href="https://reactjs.org/" target="_blank" rel="noopener noreferrer">React</a>

- 🗺️ <a href="https://maplibre.org/" target="_blank" rel="noopener noreferrer">Maplibre GL JS</a>

- 🎨 <a href="https://mui.com/" target="_blank" rel="noopener noreferrer">MUI</a>

- 🔀 <a href="https://reactflow.dev/" target="_blank" rel="noopener noreferrer">React Flow</a>

- 🔒 <a href="https://authjs.dev/" target="_blank" rel="noopener noreferrer">Auth.js</a>

- 🧘‍♂️ <a href="https://zod.dev/" target="_blank" rel="noopener noreferrer">Zod</a>

### Backend & API Services

- 🐍 <a href="https://www.python.org/" target="_blank" rel="noopener noreferrer">Python</a>

- ⚡️ <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noopener noreferrer">FastAPI</a>

- 📦 <a href="https://pydantic.dev/" target="_blank" rel="noopener noreferrer">Pydantic</a>

- 🗄️ <a href="https://www.sqlalchemy.org/" target="_blank" rel="noopener noreferrer">SQLAlchemy</a>

- 🐘 <a href="https://www.postgresql.org/" target="_blank" rel="noopener noreferrer">PostgreSQL</a>

- 🔐 <a href="https://www.keycloak.org/" target="_blank" rel="noopener noreferrer">Keycloak</a>

### Geospatial & Analytics

- 🦆 <a href="https://duckdb.org/" target="_blank" rel="noopener noreferrer">DuckDB</a>

- 🛶 <a href="https://ducklake.select/" target="_blank" rel="noopener noreferrer">DuckLake</a>

- ⚙️ <a href="https://www.windmill.dev/" target="_blank" rel="noopener noreferrer">Windmill</a>

- 🌍 <a href="https://gdal.org/" target="_blank" rel="noopener noreferrer">GDAL</a>

- 🗃️ <a href="https://docs.protomaps.com/pmtiles/" target="_blank" rel="noopener noreferrer">PMTiles</a>

<br/>


## 🚀 Getting started

### ☁️ Cloud Version
GOAT is also available as a fully hosted cloud service.  If you prefer not to manage your own infrastructure, you can get started instantly with our trial version and choose from one of our available subscription tiers. Get started at <a href="https://goat.plan4better.de" target="_blank" rel="noopener noreferrer">goat.plan4better.de</a>.

### 🐳 Self-hosting (Docker)

**Official support:** We provide a maintained `compose.yaml` for running the full GOAT stack in a production‑like environment.

**Important:** While we provide Docker resources, **self‑hosted deployments are community‑supported**. We do not offer official support for managing your infrastructure.

The images for each GOAT service are published on GitHub Container Registry.


#### Requirements

Make sure the following are installed on your server or local machine:

- Docker  
- Docker Compose (plugin syntax: `docker compose`)  
- At least 12 GB RAM recommended

#### Docker Compose Profiles

The `compose.yaml` uses profiles to control which services start:

| Profile | Description |
|---------|-------------|
| (none) | Infrastructure only: PostgreSQL, MinIO, Redis, RabbitMQ, Windmill server/worker |
| `dev` | Infrastructure + devcontainer with local code mounts for development |
| `prod` | Infrastructure + all production services (core, geoapi, web, processes, workers) |

#### Running GOAT with Docker Compose (recommended for most users)

The `prod` profile provisions:

- PostgreSQL with PostGIS  
- MinIO (S3 compatible storage)  
- Redis & RabbitMQ  
- Windmill (workflow engine for analytics tools)
- GOAT Core (FastAPI backend)  
- GOAT GeoAPI (FastAPI backend for geodata)  
- GOAT Processes (OGC API Processes)
- GOAT Web (Next.js frontend)

#### 1. Clone the repository

```bash
git clone https://github.com/plan4better/goat.git
cd goat
```

#### 2. Create your configuration file

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update environment variables as needed (see "Environment Variables" section below).

#### 3. Start the GOAT stack

```bash
docker compose --profile prod up -d
```

This will automatically pull the latest images and start all services.

#### 4. Access GOAT

| Service | URL |
|---------|-----|
| Web UI | <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer">http://localhost:3000</a> |
| Core API | <a href="http://localhost:8000/api" target="_blank" rel="noopener noreferrer">http://localhost:8000/api</a> |
| GeoAPI | <a href="http://localhost:8100" target="_blank" rel="noopener noreferrer">http://localhost:8100</a> |
| Processes API | <a href="http://localhost:8300" target="_blank" rel="noopener noreferrer">http://localhost:8300</a> |
| Windmill UI | <a href="http://localhost:8110" target="_blank" rel="noopener noreferrer">http://localhost:8110</a> |
| MinIO Console | <a href="http://localhost:9001" target="_blank" rel="noopener noreferrer">http://localhost:9001</a> |

#### Updating GOAT

To update an existing installation:

```bash
docker compose --profile prod down
docker compose --profile prod pull
docker compose --profile prod up -d
```

#### Clean Restart (reset all data)

To completely reset the installation including all data:

```bash
docker compose --profile prod down
docker volume rm goat_goat-data
docker compose --profile prod up -d
```

#### Build Images Locally

If you are developing the GOAT codebase or making changes to `apps/core`, `apps/geoapi`, or `apps/web`, you may need to build images manually.

```bash
docker compose --profile prod up -d --build
```

Only use this if you're modifying the GOAT source code.


#### Required Environment Variables

| Variable | Description |
|---------|-------------|
| `POSTGRES_USER` | Username for PostgreSQL authentication |
| `POSTGRES_PASSWORD` | Password for PostgreSQL authentication |
| `POSTGRES_SERVER` | Hostname of the Postgres service (usually `db`) |
| `POSTGRES_DB` | Name of the PostgreSQL database |
| `S3_PROVIDER` | Storage provider (e.g., `minio`) |
| `S3_ACCESS_KEY_ID` | Access key for S3 / MinIO |
| `S3_SECRET_ACCESS_KEY` | Secret key for S3 / MinIO |
| `S3_ENDPOINT_URL` | Internal S3 endpoint (`http://minio:9000`) |
| `S3_BUCKET_NAME` | Name of the S3 bucket to create/use |
| `S3_REGION` | Region (may remain empty for MinIO) |
| `S3_PUBLIC_ENDPOINT_URL` | Public URL for accessing S3 objects |
| `AUTH` | Auth switch for all services and the web app (True/False). With `False`, the Keycloak variables are not needed and a default user/organization is seeded |
| `NEXT_PUBLIC_API_URL` | Public URL of the Core API |
| `NEXT_PUBLIC_GEOAPI_URL` | Public URL of the GeoAPI (tiles/features) |
| `NEXT_PUBLIC_PROCESSES_URL` | Public URL of the Processes API |
| `NEXT_PUBLIC_DOCS_URL` | URL for documentation |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox token for the map search control (geocoding) |
| `KEYCLOAK_SERVER_URL` | Base URL of the Keycloak server (derives the issuer together with `REALM_NAME`) |
| `REALM_NAME` | Keycloak realm |
| `KEYCLOAK_CLIENT_ID` | Keycloak client (web login, core admin, print worker) |
| `KEYCLOAK_CLIENT_SECRET` | Keycloak client secret |
| `WINDMILL_TOKEN` | Token for the Windmill workflow engine (analytics tools) |
| `NEXTAUTH_URL` | Public URL of the Web UI (also drives `NEXT_PUBLIC_APP_URL`) |
| `NEXTAUTH_SECRET` | Secret key for Auth.js sessions |

See [`.env.example`](/.env.example) for the full list, including optional
settings such as the `AUTH=False` default identity (`DEFAULT_USER_*`,
`DEFAULT_ORGANIZATION_NAME`, `DEFAULT_QUOTA_*`), SMTP, and Stripe.


## 👩‍⚖️ License

GOAT is a commercial open‑source project. The core platform is licensed under the
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank" rel="noopener noreferrer">GNU General Public License v3.0 (GPLv3)</a>,
which allows anyone to use, modify, and distribute the software under the terms of the GPL.

The full platform — including user management, teams, and organizations — is part
of the open-source core. Optional commercial services (hosting, support, and
enterprise capabilities) are available for organizations that need them.

This structure makes GOAT accessible for everyone, while providing extended functionalities through
optional commercial services.


|                                   | GPLv3 | Commercial |
| --------------------------------- | :---: | :--------: |
| Self‑host the core platform       | ✅    | ✅         |
| Use for commercial purposes       | ✅    | ✅         |
| Teams & organizations             | ✅    | ✅         |
| Clone privately                   | ✅    | ✅         |
| Fork publicly                     | ✅    | ✅         |
| Modify and redistribute           | ✅    | ❌ (commercial components excluded) |
| Keep derivative work private      | ❌    | ✅ (commercial components only) |
| Authentication integrations       | ❌    | ✅         |
| Hosted SaaS version               | ❌    | ✅         |
| Official support                  | ❌    | ✅         |


## ✍️ Contributing
We welcome contributions of all kinds, bug reports, documentation improvements, new features, and feedback that helps strengthen the platform. Please see our [contributing guide](/CONTRIBUTING.md).
