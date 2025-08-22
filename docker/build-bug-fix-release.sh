#!/bin/bash
# Docker Release Script for Bug Fix Version 4.1.0
# Run this script from the project root directory

VERSION="4.1.0"
BUILD_DATE=$(date '+%Y.%m.%d.%H%M')
REPO_NAME="hsayfi/overseerr-telegram-bot"

echo "🚀 Building Docker image for Bug Fix Release v$VERSION"
echo "Build: $BUILD_DATE"
echo "================================================"

# Ensure we're in the right directory
if [ ! -f "bot.py" ]; then
    echo "❌ Error: bot.py not found. Please run this script from the project root."
    exit 1
fi

echo "📝 Bug Fixes Included in this Release:"
echo "✅ Fixed anime selection TypeError (seasons parameter)"
echo "✅ Fixed logout functionality with persistent session clearing"  
echo "✅ Fixed Telegram message editing API errors"
echo "✅ Fixed notification bitmask for proper Telegram notifications"
echo "✅ Enhanced error handling and user experience"
echo ""

# Build Docker image locally (for testing)
echo "🔨 Building Docker image locally..."
docker build -t $REPO_NAME:$VERSION .
docker tag $REPO_NAME:$VERSION $REPO_NAME:latest

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "🏷️  Tagged images:"
    echo "   - $REPO_NAME:$VERSION"
    echo "   - $REPO_NAME:latest"
    echo ""
    
    echo "🚢 To push to Docker Hub, run:"
    echo "   docker push $REPO_NAME:$VERSION"
    echo "   docker push $REPO_NAME:latest"
    echo ""
    
    echo "🧪 To test locally, run:"
    echo "   docker run -it --rm \\"
    echo "     -e OVERSEERR_API_URL=\"http://your-overseerr:5055/api/v1\" \\"
    echo "     -e OVERSEERR_API_KEY=\"your-api-key\" \\"
    echo "     -e TELEGRAM_TOKEN=\"your-bot-token\" \\"
    echo "     $REPO_NAME:$VERSION"
else
    echo "❌ Docker build failed!"
    exit 1
fi
