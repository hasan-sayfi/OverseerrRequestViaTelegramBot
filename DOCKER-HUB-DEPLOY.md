# 🚀 Docker Hub Deployment Guide

## Prerequisites

1. **Docker Hub Account**: Create account at [hub.docker.com](https://hub.docker.com)
2. **Docker Login**: Login to Docker Hub from your terminal
3. **Repository Access**: Ensure you have push access to `hsayfi/overseerr-telegram-bot`

## 🔐 Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password/token
```

## 🏗️ Build and Push Options

### Option 1: Quick Single-Platform Build

```bash
# Build for current platform (fastest)
docker build -t hsayfi/overseerr-telegram-bot:3.0.0 .
docker build -t hsayfi/overseerr-telegram-bot:latest .

# Push to Docker Hub
docker push hsayfi/overseerr-telegram-bot:3.0.0
docker push hsayfi/overseerr-telegram-bot:latest
```

### Option 2: Using Build Scripts

**Windows:**
```cmd
docker-build.bat 3.0.0
```

**Linux/macOS:**
```bash
chmod +x docker-build.sh
./docker-build.sh 3.0.0
```

### Option 3: Multi-Platform Build (Advanced)

```bash
# Set up buildx builder (one-time setup)
docker buildx create --name multiarch-builder --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag hsayfi/overseerr-telegram-bot:3.0.0 \
  --tag hsayfi/overseerr-telegram-bot:latest \
  --push \
  .
```

## 📋 Pre-Push Checklist

- [ ] All tests pass locally
- [ ] Docker build succeeds: `docker build -t test-image .`
- [ ] Environment variables documented
- [ ] Version tag is appropriate
- [ ] DOCKER.md is up to date
- [ ] .dockerignore excludes unnecessary files

## 🏷️ Tagging Strategy

| Tag | Purpose | Example |
|-----|---------|---------|
| `latest` | Latest stable release | `hsayfi/overseerr-telegram-bot:latest` |
| `X.Y.Z` | Specific version | `hsayfi/overseerr-telegram-bot:3.0.0` |
| `X.Y` | Minor version | `hsayfi/overseerr-telegram-bot:3.0` |
| `branch-name` | Development branch | `hsayfi/overseerr-telegram-bot:refactored` |

## 🎯 Step-by-Step Deployment

### 1. Final Testing
```bash
# Test local build
docker build -t overseerr-bot-test .

# Test run (optional - requires env vars)
docker run --rm -e TELEGRAM_TOKEN="test" overseerr-bot-test python -c "import bot; print('Import successful')"
```

### 2. Version and Tag
```bash
# Tag current commit
git tag v3.0.0
git push origin v3.0.0

# Build with version tag
docker build -t hsayfi/overseerr-telegram-bot:3.0.0 .
docker build -t hsayfi/overseerr-telegram-bot:latest .
```

### 3. Push to Docker Hub
```bash
# Push specific version
docker push hsayfi/overseerr-telegram-bot:3.0.0

# Push latest
docker push hsayfi/overseerr-telegram-bot:latest
```

### 4. Verify Deployment
```bash
# Pull and test the published image
docker pull hsayfi/overseerr-telegram-bot:latest
docker run --rm hsayfi/overseerr-telegram-bot:latest python --version
```

## 🎯 Automated Deployment Commands

Copy and run these commands for quick deployment:

```bash
# 1. Login to Docker Hub
docker login

# 2. Build the image
docker build -t hsayfi/overseerr-telegram-bot:3.0.0 .
docker build -t hsayfi/overseerr-telegram-bot:latest .

# 3. Push to Docker Hub
docker push hsayfi/overseerr-telegram-bot:3.0.0
docker push hsayfi/overseerr-telegram-bot:latest

# 4. Verify
echo "✅ Deployment complete!"
echo "🐳 Image: hsayfi/overseerr-telegram-bot:3.0.0"
echo "📦 Latest: hsayfi/overseerr-telegram-bot:latest"
```

## 📊 Image Information

After successful push, your image will be available at:
- **Docker Hub**: https://hub.docker.com/r/hsayfi/overseerr-telegram-bot
- **Pull Command**: `docker pull hsayfi/overseerr-telegram-bot:latest`

## 🔍 Post-Deployment Testing

Test the deployed image:

```bash
# Pull the image
docker pull hsayfi/overseerr-telegram-bot:latest

# Test with docker-compose
cat > test-compose.yml << EOF
version: "3.9"
services:
  bot:
    image: hsayfi/overseerr-telegram-bot:latest
    environment:
      OVERSEERR_API_URL: "http://your-overseerr:5055/api/v1"
      OVERSEERR_API_KEY: "your-api-key"
      TELEGRAM_TOKEN: "your-bot-token"
    volumes:
      - ./test-data:/app/data
EOF

# Test run
docker-compose -f test-compose.yml up -d
docker-compose -f test-compose.yml logs
```

## 🎉 Success Verification

Your deployment is successful when:
- ✅ Image builds without errors
- ✅ Image pushes to Docker Hub successfully
- ✅ Image is publicly accessible
- ✅ Bot starts and responds to commands
- ✅ All features work as expected

## 📞 Support

If you encounter issues:
1. Check Docker Hub build logs
2. Verify your Docker Hub permissions
3. Test local builds first
4. Review environment variable configuration

**Repository**: https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot
**Docker Hub**: https://hub.docker.com/r/hsayfi/overseerr-telegram-bot
