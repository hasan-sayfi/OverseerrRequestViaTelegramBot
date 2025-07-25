@echo off
:: Docker build and push script for Overseerr Telegram Bot (Windows)
:: Usage: docker-build.bat [version]

setlocal enabledelayedexpansion

:: Configuration
set DOCKER_REPO=hsayfi/overseerr-telegram-bot
set DEFAULT_VERSION=4.0.2
set PLATFORMS=linux/amd64,linux/arm64

:: Get version from argument or use default
if "%~1"=="" (
    set VERSION=%DEFAULT_VERSION%
) else (
    set VERSION=%~1
)

echo Building version: %VERSION%

:: Ensure we're in the right directory
if not exist "bot.py" (
    echo Error: bot.py not found. Please run this script from the project root.
    exit /b 1
)

echo 🏗️  Building Docker image...

:: Build multi-platform image
docker buildx build --platform %PLATFORMS% --tag %DOCKER_REPO%:%VERSION% --tag %DOCKER_REPO%:latest --push .

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    exit /b 1
)

echo ✅ Successfully built and pushed:
echo    - %DOCKER_REPO%:%VERSION%
echo    - %DOCKER_REPO%:latest

echo.
echo 🚀 To run the bot:
echo    docker run -d --name overseerr-bot ^
echo      -e OVERSEERR_API_URL="http://your-overseerr:5055/api/v1" ^
echo      -e OVERSEERR_API_KEY="your-api-key" ^
echo      -e TELEGRAM_TOKEN="your-bot-token" ^
echo      -v ./data:/app/data ^
echo      %DOCKER_REPO%:latest

echo.
echo 📦 Or use docker-compose:
echo    docker-compose up -d

pause
