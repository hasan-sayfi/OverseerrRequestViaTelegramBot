#!/bin/bash
# Docker Hub deployment verification script

echo "🔍 Docker Hub Deployment Verification"
echo "======================================"
echo ""

# Check if images exist locally
echo "📦 Local Images:"
docker images | grep hsayfi/overseerr-telegram-bot
echo ""

# Test pulling from Docker Hub (this will verify the push worked)
echo "🌐 Testing Docker Hub availability..."
echo "Pulling hsayfi/overseerr-telegram-bot:latest from Docker Hub..."

# Try to pull the image
if docker pull hsayfi/overseerr-telegram-bot:latest; then
    echo "✅ SUCCESS: Image successfully available on Docker Hub!"
    echo ""
    
    # Test running the image
    echo "🧪 Testing image functionality..."
    if docker run --rm hsayfi/overseerr-telegram-bot:latest python --version; then
        echo "✅ SUCCESS: Image runs correctly!"
    else
        echo "⚠️  WARNING: Image runs but Python test failed"
    fi
    
    # Test bot import
    echo ""
    echo "🤖 Testing bot import..."
    if docker run --rm hsayfi/overseerr-telegram-bot:latest python -c "import bot; print('✅ Bot module imports successfully!')"; then
        echo "✅ SUCCESS: Bot module imports correctly!"
    else
        echo "❌ ERROR: Bot module import failed"
    fi
    
else
    echo "❌ ERROR: Could not pull image from Docker Hub"
    echo "This might mean:"
    echo "  - Push is still in progress"
    echo "  - Authentication failed during push"
    echo "  - Repository name is incorrect"
fi

echo ""
echo "🎯 Your Docker Hub repository:"
echo "   https://hub.docker.com/r/hsayfi/overseerr-telegram-bot"
echo ""
echo "🚀 To use your image:"
echo "   docker run -d hsayfi/overseerr-telegram-bot:latest"
echo ""
echo "📦 To pull your image:"
echo "   docker pull hsayfi/overseerr-telegram-bot:latest"
