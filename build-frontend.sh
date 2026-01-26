#!/bin/bash

# Build frontend Docker image with production environment variables
# This script builds the frontend with the backend URL baked into the build

set -e

BACKEND_URL="https://apiproagent.harjadi.com"
API_KEY="Th3zcM61GGDHMqKuYgfgZVTJF"

echo "🏗️  Building frontend Docker image..."
echo "Backend URL: $BACKEND_URL"
echo ""

# Build the image with build args
docker build \
  --no-cache \
  --build-arg NEXT_PUBLIC_BACKEND_URL=$BACKEND_URL \
  --build-arg NEXT_PUBLIC_API_KEY=$API_KEY \
  -t procode-agent-framework-frontend:latest \
  -f frontend/Dockerfile \
  frontend/

echo ""
echo "✅ Frontend image built successfully!"
echo ""
echo "To tag and push to Docker Hub:"
echo "  docker tag procode-agent-framework-frontend:latest tempolong/procode-frontend:latest"
echo "  docker push tempolong/procode-frontend:latest"
