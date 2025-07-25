# 🐳 Docker Deployment Guide

This guide covers deploying the Overseerr Telegram Bot using Docker.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose v2+ (optional but recommended)
- Docker Hub account (for custom builds)

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Download docker-compose.yml**:
   ```bash
   wget https://raw.githubusercontent.com/hasan-sayfi/OverseerrRequestViaTelegramBot/refactored-modular-structure/docker-compose.yml
   ```

2. **Edit environment variables**:
   ```bash
   nano docker-compose.yml
   ```
   
   Update these required values:
   ```yaml
   OVERSEERR_API_URL: "http://YOUR_OVERSEERR_IP:5055/api/v1"
   OVERSEERR_API_KEY: "YOUR_OVERSEERR_API_KEY"
   TELEGRAM_TOKEN: "YOUR_TELEGRAM_BOT_TOKEN"
   ```

3. **Create data directory**:
   ```bash
   mkdir -p ./data
   ```

4. **Start the bot**:
   ```bash
   docker-compose up -d
   ```

### Option 2: Using Docker Run

```bash
docker run -d \
  --name overseerr-telegram-bot \
  --restart unless-stopped \
  -e OVERSEERR_API_URL="http://YOUR_OVERSEERR_IP:5055/api/v1" \
  -e OVERSEERR_API_KEY="YOUR_OVERSEERR_API_KEY" \
  -e TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN" \
  -e PASSWORD="your_optional_password" \
  -v ./data:/app/data \
  hasansayfi/overseerr-telegram-bot:latest
```

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OVERSEERR_API_URL` | ✅ | - | Your Overseerr API URL (e.g., `http://192.168.1.100:5055/api/v1`) |
| `OVERSEERR_API_KEY` | ✅ | - | Your Overseerr API key |
| `TELEGRAM_TOKEN` | ✅ | - | Your Telegram bot token from @BotFather |
| `PASSWORD` | ❌ | `""` | Optional password for bot access control |
| `BOT_MODE` | ❌ | `normal` | Bot operation mode: `normal`, `api`, or `shared` |

## 📁 Volume Mounts

| Container Path | Purpose | Required |
|----------------|---------|----------|
| `/app/data` | Persistent data storage (sessions, configs) | ✅ |

## 🔍 Bot Modes

- **Normal Mode** (`BOT_MODE=normal`): Users login with their Overseerr credentials
- **API Mode** (`BOT_MODE=api`): Users select from existing Overseerr users
- **Shared Mode** (`BOT_MODE=shared`): All users share one account (admin managed)

## 🏗️ Building Custom Image

### Prerequisites for Building
- Docker Buildx enabled
- Multi-platform support configured

### Build Commands

**Linux/macOS**:
```bash
chmod +x docker-build.sh
./docker-build.sh [version]
```

**Windows**:
```cmd
docker-build.bat [version]
```

**Manual Build**:
```bash
# Single platform
docker build -t hasansayfi/overseerr-telegram-bot:latest .

# Multi-platform (requires buildx)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag hasansayfi/overseerr-telegram-bot:latest \
  --push .
```

## 🔧 Management Commands

### View Logs
```bash
# Docker Compose
docker-compose logs -f

# Docker Run
docker logs -f overseerr-telegram-bot
```

### Update Bot
```bash
# Docker Compose
docker-compose pull
docker-compose up -d

# Docker Run
docker pull hasansayfi/overseerr-telegram-bot:latest
docker stop overseerr-telegram-bot
docker rm overseerr-telegram-bot
# Then run the docker run command again
```

### Backup Data
```bash
# Backup persistent data
tar -czf overseerr-bot-backup-$(date +%Y%m%d).tar.gz ./data/
```

### Restore Data
```bash
# Stop container first
docker-compose down

# Restore data
tar -xzf overseerr-bot-backup-YYYYMMDD.tar.gz

# Start container
docker-compose up -d
```

## 🩺 Health Checks

The container includes built-in health checks:

- **Interval**: 60 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 10 seconds

Check health status:
```bash
docker ps  # Shows health status
docker inspect overseerr-telegram-bot | grep Health -A 10
```

## 🐛 Troubleshooting

### Container Won't Start
1. Check logs: `docker-compose logs`
2. Verify environment variables are set correctly
3. Ensure data directory has proper permissions
4. Check if ports are available

### Bot Not Responding
1. Verify Telegram token is correct
2. Check Overseerr API connectivity:
   ```bash
   docker exec overseerr-telegram-bot curl -H "X-Api-Key: YOUR_API_KEY" YOUR_OVERSEERR_URL/status
   ```
3. Check container health: `docker ps`

### Permission Issues
```bash
# Fix data directory permissions
sudo chown -R 1000:1000 ./data
```

### Reset Bot Data
```bash
# Stop container
docker-compose down

# Clear persistent data
rm -rf ./data/*

# Start container
docker-compose up -d
```

## 🔒 Security Best Practices

1. **Use specific image tags** instead of `latest` in production
2. **Set strong passwords** if using password protection
3. **Limit network access** to required services only
4. **Regular updates** - monitor for new releases
5. **Backup data** regularly
6. **Use Docker secrets** for sensitive environment variables in swarm mode

## 📊 Resource Requirements

### Minimum Requirements
- **CPU**: 0.1 cores
- **Memory**: 128MB
- **Disk**: 100MB

### Recommended Requirements
- **CPU**: 0.25 cores
- **Memory**: 256MB
- **Disk**: 500MB (for logs and data)

## 🆙 Version Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release |
| `3.0.0` | Specific version |
| `refactored` | Latest refactored modular version |

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/discussions)
- **Docker Hub**: [hasansayfi/overseerr-telegram-bot](https://hub.docker.com/r/hasansayfi/overseerr-telegram-bot)
