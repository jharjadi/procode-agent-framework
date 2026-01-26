#!/bin/bash

# Build frontend Docker image with production environment variables
# This script builds the frontend with the backend URL baked into the build
#
# Usage:
#   BACKEND_URL=https://apiproagent.harjadi.com API_KEY=your_key ./build-frontend.sh
#
# Or set them in your environment first:
#   export BACKEND_URL=https://apiproagent.harjadi.com
#   export API_KEY=your_key
#   ./build-frontend.sh

set -e

# Check if environment variables are set
if [ -z "$BACKEND_URL" ]; then
  echo "❌ Error: BACKEND_URL environment variable is not set"
  echo "Usage: BACKEND_URL=https://apiproagent.harjadi.com API_KEY=your_key ./build-frontend.sh"
  exit 1
fi

if [ -z "$API_KEY" ]; then
  echo "❌ Error: API_KEY environment variable is not set"
  echo "Usage: BACKEND_URL=https://apiproagent.harjadi.com API_KEY=your_key ./build-frontend.sh"
  exit 1
fi

echo "🏗️  Building frontend Docker image..."
echo "Backend URL: $BACKEND_URL"
echo "API Key: ${API_KEY:0:8}... (hidden)"
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
