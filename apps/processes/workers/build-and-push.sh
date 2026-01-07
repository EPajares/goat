#!/bin/bash
# Build and push multi-platform Windmill worker images to GHCR
#
# Usage:
#   ./build-and-push.sh                    # Build and push with git commit SHA tag
#   ./build-and-push.sh v2.3.0             # Build and push with specific version tag
#   ./build-and-push.sh --no-push          # Build only (no push), uses git SHA
#   ./build-and-push.sh v2.3.0 --no-push   # Build only with specific version
#
# Prerequisites:
#   - Docker with buildx enabled
#   - Logged in to GHCR: echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

set -e

# Configuration
# Use ghcr.io/OWNER/REPO/IMAGE format to link packages to the repository
REGISTRY="ghcr.io/plan4better/goat"
DOCKERFILE="apps/processes/workers/Dockerfile"
PLATFORMS="linux/amd64,linux/arm64"
TARGETS=("worker-default" "worker-tools" "worker-print")

# Parse arguments - detect if first arg is --no-push or a version
if [ "$1" = "--no-push" ]; then
    VERSION=""
    NO_PUSH="--no-push"
else
    VERSION="${1:-}"
    NO_PUSH="${2:-}"
fi

# Get git commit SHA if no version specified
if [ -z "$VERSION" ]; then
    VERSION=$(git rev-parse --short=7 HEAD)
    echo "Using git commit SHA as version: $VERSION"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Windmill Workers Multi-Platform Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Registry:  ${YELLOW}${REGISTRY}${NC}"
echo -e "Version:   ${YELLOW}${VERSION}${NC}"
echo -e "Platforms: ${YELLOW}${PLATFORMS}${NC}"
echo -e "Targets:   ${YELLOW}${TARGETS[*]}${NC}"
echo ""

# Check if logged in to GHCR
if ! docker info 2>/dev/null | grep -q "ghcr.io"; then
    echo -e "${YELLOW}Warning: May not be logged in to GHCR${NC}"
    echo "Run: echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
fi

# Ensure buildx builder exists with multi-platform support
BUILDER_NAME="goat-multiplatform"
if ! docker buildx inspect "$BUILDER_NAME" &>/dev/null; then
    echo -e "${YELLOW}Creating buildx builder: ${BUILDER_NAME}${NC}"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap --use
else
    docker buildx use "$BUILDER_NAME"
fi

# Change to repo root (script is in apps/processes/workers/)
cd "$(dirname "$0")/../../.."

echo -e "\n${GREEN}Building from: $(pwd)${NC}\n"

# Build and push each target
for TARGET in "${TARGETS[@]}"; do
    IMAGE_NAME="${REGISTRY}/windmill-${TARGET}"

    echo -e "${GREEN}----------------------------------------${NC}"
    echo -e "${GREEN}Building: ${IMAGE_NAME}${NC}"
    echo -e "${GREEN}Target:   ${TARGET}${NC}"
    echo -e "${GREEN}----------------------------------------${NC}"

    # Build tags - always use version (commit SHA or explicit)
    TAGS="-t ${IMAGE_NAME}:${VERSION}"

    # Build command
    BUILD_CMD="docker buildx build \
        --platform ${PLATFORMS} \
        --file ${DOCKERFILE} \
        --target ${TARGET} \
        ${TAGS}"

    if [ "$NO_PUSH" != "--no-push" ]; then
        BUILD_CMD="${BUILD_CMD} --push"
        echo -e "${YELLOW}Will push to registry${NC}"
    else
        BUILD_CMD="${BUILD_CMD} --load"
        echo -e "${YELLOW}Local build only (--no-push)${NC}"
    fi

    BUILD_CMD="${BUILD_CMD} ."

    echo -e "\n${YELLOW}Running: ${BUILD_CMD}${NC}\n"

    eval $BUILD_CMD

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully built ${IMAGE_NAME}:${VERSION}${NC}\n"
    else
        echo -e "${RED}✗ Failed to build ${IMAGE_NAME}${NC}"
        exit 1
    fi
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All images built successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

if [ "$NO_PUSH" != "--no-push" ]; then
    echo -e "\nPushed images:"
    for TARGET in "${TARGETS[@]}"; do
        echo -e "  ${YELLOW}${REGISTRY}/windmill-${TARGET}:${VERSION}${NC}"
    done
    echo -e "\nInstall from command line:"
    echo -e "  docker pull ${REGISTRY}/windmill-server:${VERSION}"
fi
