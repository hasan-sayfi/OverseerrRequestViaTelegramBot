#!/bin/bash

# Docker build and push script for Overseerr Telegram Bot
# Usage: ./docker-build.sh [version]

set -e

# Configuration
DOCKER_REPO="hsayfi/overseerr-telegram-bot"
DEFAULT_VERSION="4.1.0"
PLATFORMS="linux/amd64,linux/arm64"

# Get version from argument or use default
VERSION=${1:-$DEFAULT_VERSION}
echo "Building version: $VERSION"

# Ensure we're in the right directory
if [ ! -f "bot.py" ]; then
    echo "Error: bot.py not found. Please run this script from the project root."
    exit 1
fi

echo "🏗️  Building Docker image..."

# Build multi-platform image
docker buildx build \
    --platform $PLATFORMS \
    --tag $DOCKER_REPO:$VERSION \
    --tag $DOCKER_REPO:latest \
    --push \
    .

echo "✅ Successfully built and pushed:"
echo "   - $DOCKER_REPO:$VERSION"
echo "   - $DOCKER_REPO:latest"

echo ""
echo "🚀 To run the bot:"
echo "   docker run -d --name overseerr-bot \\"
echo "     -e OVERSEERR_API_URL='http://your-overseerr:5055/api/v1' \\"
echo "     -e OVERSEERR_API_KEY='your-api-key' \\"
echo "     -e TELEGRAM_TOKEN='your-bot-token' \\"
echo "     -v ./data:/app/data \\"
echo "     $DOCKER_REPO:latest"

echo ""
echo "📦 Or use docker-compose:"
echo "   docker-compose up -d"
