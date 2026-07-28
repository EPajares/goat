# Build from the monorepo root:
#   docker build -f packages/js/keycloak-theme/Dockerfile .
FROM node:22-alpine AS base

FROM base AS builder
RUN apk add --no-cache libc6-compat
WORKDIR /app
RUN npm install -g turbo@2.10.7
COPY . .
RUN turbo prune @p4b/keycloak-theme --docker

FROM base AS installer
# keycloakify v8 shells out to maven to package the theme jar
RUN apk add --no-cache libc6-compat maven rsync
WORKDIR /app

COPY --from=builder /app/out/json/ .
COPY --from=builder /app/out/pnpm-lock.yaml ./pnpm-lock.yaml
RUN npm install -g corepack@latest
RUN corepack enable
RUN pnpm install --frozen-lockfile

COPY --from=builder /app/out/full/ .
ENV KEYCLOAKIFY_ARTIFACT_ID=p4b-keycloak-theme
ENV KEYCLOAKIFY_GROUP_ID=com.plan4better.auth.keycloak
RUN cd packages/js/keycloak-theme \
  && pnpm run build-keycloak-theme \
  && mv build_keycloak/target/*.jar build_keycloak/target/p4b-keycloak-theme.jar

FROM alpine:3.20 AS providers
RUN wget -q -O /keycloak-metrics-spi-4.0.0.jar \
    https://assets.plan4better.de/other/keycloak/keycloak-metrics-spi-4.0.0.jar \
  && wget -q -O /io.phasetwo.keycloak-keycloak-events-0.19.jar \
    https://assets.plan4better.de/other/keycloak/phasetwo_keycloak_22.0.3/io.phasetwo.keycloak-keycloak-events-0.19.jar \
  && echo "0f434d06e73d6018b2c06a2ae611b875ca22ba7c86fc2d995fbde9e254b9bf8b  /keycloak-metrics-spi-4.0.0.jar" | sha256sum -c - \
  && echo "23454c7878ee8c8f72f2d3ce9ef57f07a8e888997483ca3cb81ac339ae5880e5  /io.phasetwo.keycloak-keycloak-events-0.19.jar" | sha256sum -c -

# Same base the dev + prod clusters run today; theme and SPI jars are baked in
# so no init container or runtime downloads are needed.
FROM docker.io/bitnamilegacy/keycloak:22.0.3-debian-11-r0
COPY --from=providers --chown=1001:0 \
  /keycloak-metrics-spi-4.0.0.jar \
  /io.phasetwo.keycloak-keycloak-events-0.19.jar \
  /opt/bitnami/keycloak/providers/
COPY --from=installer --chown=1001:0 \
  /app/packages/js/keycloak-theme/build_keycloak/target/p4b-keycloak-theme.jar \
  /opt/bitnami/keycloak/providers/p4b-keycloak-theme.jar
