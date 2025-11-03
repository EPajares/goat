This is a Monorepo repository for our GOAT project with a FastAPI/Python backend and a React/NextJS/TypeScript frontend.
Please follow these guidelines when contributing:

## Code Standards
- Run `sh ./scripts/lint-web` before committing any changes to ensure proper code formatting for the frontend projects/libraries
- Run `sh ./scripts/lint-python` before committing any changes to ensure proper code formatting for the FastAPI/Python backend

## Repository Structure
- `.devcontainer/`: Contains configuration for development containers
- `.github/`: GitHub-specific files, including workflows and issue templates
- `.husky/`: Husky hooks for managing Git hooks
- `.vscode/`: VSCode-specific settings and configurations
- `apps/`: Contains the main applications for the project
  - `core/`: The main FastAPI/Python backend application.
  - `docs/`: Documentation for the project. It's using docusaurus
  - `geoapi/`: A separate FastAPI/Python API service for geodata services. It's serving OGC data to the frontend. 
  - `routing/`: A separate FastAPI/Python API service for routing services. It's serving OGC data to the frontend.
  - `storybook/`: A separate React/NextJS/TypeScript application for Storybook, used for UI component development and testing.
  - `web/`: The main frontend application built with React/NextJS/TypeScript
- `packages/`: Contains shared libraries and components used across the applications. It can contain both frontend and backend libraries.
  - `eslint-config-p4b/`: Shared ESLint configuration for the project.
  - `keycloak-theme/`: A shared Keycloak theme for consistent branding across authentication interfaces.
  - `prettier-config/`: Shared Prettier configuration for the project.
  - `tsconfig/`: Shared TypeScript configuration for the project.
  - `types/`: Shared TypeScript types used across the project.
  - `ui/`: Shared UI components and libraries used across the frontend applications.
- `scripts/`: Contains various scripts for development, testing, and deployment tasks.

## Key Guidelines
1. Follow Go best practices and idiomatic patterns
2. Maintain existing code structure and organization
3. Document public APIs and complex logic. Suggest changes to the `apps/docs/` folder when appropriate

