FROM node:20-alpine AS base

FROM base AS builder
RUN apk add --no-cache libc6-compat
RUN apk update

# Set working directory
WORKDIR /app
RUN npm install -g turbo@1.13.3
COPY . .
RUN turbo prune --scope=@p4b/web --docker


# Add lockfile and package.json's of isolated subworkspace
FROM base AS installer
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app

# First install the dependencies (as they change less often)
COPY --from=builder /app/out/json/ .
COPY --from=builder /app/out/pnpm-lock.yaml ./pnpm-lock.yaml
RUN npm install -g corepack@latest
RUN corepack enable
RUN pnpm install --frozen-lockfile

# Build the project
COPY --from=builder /app/out/full/ .

ARG NEXT_PUBLIC_APP_URL=APP_NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_MAP_TOKEN=APP_NEXT_PUBLIC_MAP_TOKEN
ARG NEXT_PUBLIC_ACCOUNTS_API_URL=APP_NEXT_PUBLIC_ACCOUNTS_API_URL
ARG NEXT_PUBLIC_GEOAPI_URL=APP_NEXT_PUBLIC_GEOAPI_URL
ARG NEXT_PUBLIC_API_URL=APP_NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SENTRY_DSN=APP_NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_APP_ENVIRONMENT=APP_NEXT_PUBLIC_APP_ENVIRONMENT
ARG NEXT_PUBLIC_KEYCLOAK_ISSUER=APP_NEXT_PUBLIC_KEYCLOAK_ISSUER
ARG NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=APP_NEXT_PUBLIC_KEYCLOAK_CLIENT_ID

RUN pnpm dlx turbo run build --filter=web

FROM base AS runner
RUN apk add bash

WORKDIR /app
# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=installer /app/apps/web/next.config.js .
COPY --from=installer /app/apps/web/package.json .

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=installer --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=installer --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

ENV HOSTNAME=localhost

COPY ./apps/web/entrypoint.sh /app/apps/web/entrypoint.sh
ENTRYPOINT ["/app/apps/web/entrypoint.sh"]
CMD ["node", "apps/web/server.js"]
