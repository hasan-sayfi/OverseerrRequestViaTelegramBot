@echo off
:: Quick Docker version manager and builder (Windows)
:: Usage: quick-docker.bat [new-version] [action]

setlocal enabledelayedexpansion

set REPO_NAME=hsayfi/overseerr-telegram-bot

:: Check if we're in the right directory
if not exist "bot.py" (
    echo ❌ Error: bot.py not found. Please run this script from the project root.
    exit /b 1
)

:: Get current version from docker-build.bat
set CURRENT_VERSION=
for /f "tokens=2 delims==" %%a in ('findstr "DEFAULT_VERSION=" docker-build.bat') do (
    set CURRENT_VERSION=%%a
)

:: Parse arguments
set NEW_VERSION=%1
set ACTION=%2

:: Show help
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

:: Show status
if "%1"=="show" goto :show_status
if "%1"=="status" goto :show_status

:: Interactive mode if no arguments
if "%1"=="" goto :interactive_mode

:: Main logic
if "%ACTION%"=="" (
    echo 🚀 Full deployment for version %NEW_VERSION%
    call :update_version %CURRENT_VERSION% %NEW_VERSION%
    call :build_images %NEW_VERSION%
    call :push_images %NEW_VERSION%
    call :git_operations %NEW_VERSION%
) else (
    if "%ACTION%"=="build" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
        call :build_images %NEW_VERSION%
    ) else if "%ACTION%"=="push" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
        call :build_images %NEW_VERSION%
        call :push_images %NEW_VERSION%
    ) else if "%ACTION%"=="update" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
    ) else (
        echo ❌ Unknown action: %ACTION%
        echo Available actions: build, push, update
        exit /b 1
    )
)

echo ✅ Operation completed successfully!
goto :end

:update_version
    set OLD_VER=%1
    set NEW_VER=%2
    echo 📝 Updating version from %OLD_VER% to %NEW_VER%...
    
    :: Update docker-build.bat
    powershell -Command "(gc docker-build.bat) -replace 'DEFAULT_VERSION=%OLD_VER%', 'DEFAULT_VERSION=%NEW_VER%' | Out-File -encoding ASCII docker-build.bat"
    echo   ✅ Updated docker-build.bat
    
    :: Update docker-build.sh
    if exist docker-build.sh (
        powershell -Command "(gc docker-build.sh) -replace 'DEFAULT_VERSION=\"%OLD_VER%\"', 'DEFAULT_VERSION=\"%NEW_VER%\"' | Out-File -encoding ASCII docker-build.sh"
        echo   ✅ Updated docker-build.sh
    )
    
    :: Update documentation
    if exist DOCKER-HUB-DEPLOY.md (
        powershell -Command "(gc DOCKER-HUB-DEPLOY.md) -replace '%OLD_VER%', '%NEW_VER%' | Out-File -encoding UTF8 DOCKER-HUB-DEPLOY.md"
        echo   ✅ Updated DOCKER-HUB-DEPLOY.md
    )
goto :eof

:build_images
    set VERSION=%1
    echo 🏗️ Building Docker images for version %VERSION%...
    
    docker build -t %REPO_NAME%:%VERSION% .
    if %errorlevel% neq 0 (
        echo ❌ Build failed!
        exit /b 1
    )
    echo   ✅ Built %REPO_NAME%:%VERSION%
    
    docker tag %REPO_NAME%:%VERSION% %REPO_NAME%:latest
    echo   ✅ Tagged as %REPO_NAME%:latest
goto :eof

:push_images
    set VERSION=%1
    echo 🚀 Pushing images to Docker Hub...
    
    docker push %REPO_NAME%:%VERSION%
    if %errorlevel% neq 0 (
        echo ❌ Push failed!
        exit /b 1
    )
    echo   ✅ Pushed %REPO_NAME%:%VERSION%
    
    docker push %REPO_NAME%:latest
    echo   ✅ Pushed %REPO_NAME%:latest
goto :eof

:git_operations
    set VERSION=%1
    echo 📝 Committing changes and creating git tag...
    
    git add .
    git commit -m "Update Docker version to %VERSION%" 2>nul
    git tag v%VERSION% 2>nul
    git push origin refactored-modular-structure
    git push origin v%VERSION% 2>nul
    
    echo   ✅ Git operations completed
goto :eof

:show_status
    echo 📊 Current Docker Configuration
    echo ================================
    echo 🏷️ Current Version: %CURRENT_VERSION%
    echo 🐳 Repository: %REPO_NAME%
    echo.
    echo 🖼️ Recent Docker Images:
    docker images %REPO_NAME% 2>nul
    echo.
    echo 🏷️ Recent Git Tags:
    git tag --sort=-version:refname 2>nul | head -5
goto :end

:interactive_mode
    echo 🤖 Interactive Docker Version Manager
    echo =====================================
    echo Current version: %CURRENT_VERSION%
    echo.
    
    set /p NEW_VERSION=Enter new version (e.g., 4.0.3, 4.1.0): 
    
    if "%NEW_VERSION%"=="" (
        echo ❌ No version provided. Exiting.
        exit /b 1
    )
    
    echo.
    echo What would you like to do?
    echo 1) Update version only
    echo 2) Update + Build images
    echo 3) Update + Build + Push to Docker Hub
    echo 4) Full deployment (Update + Build + Push + Git commit/tag)
    echo.
    
    set /p CHOICE=Choose option (1-4): 
    
    if "%CHOICE%"=="1" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
    ) else if "%CHOICE%"=="2" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
        call :build_images %NEW_VERSION%
    ) else if "%CHOICE%"=="3" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
        call :build_images %NEW_VERSION%
        call :push_images %NEW_VERSION%
    ) else if "%CHOICE%"=="4" (
        call :update_version %CURRENT_VERSION% %NEW_VERSION%
        call :build_images %NEW_VERSION%
        call :push_images %NEW_VERSION%
        call :git_operations %NEW_VERSION%
    ) else (
        echo ❌ Invalid option. Exiting.
        exit /b 1
    )
goto :end

:show_help
    echo 🐳 Quick Docker Version Manager
    echo.
    echo Usage:
    echo   %0                          # Interactive mode
    echo   %0 show                     # Show current status
    echo   %0 ^<version^>                # Full deployment (update + build + push + git)
    echo   %0 ^<version^> build          # Update version and build only
    echo   %0 ^<version^> push           # Update, build, and push to Docker Hub
    echo   %0 ^<version^> update         # Update version in files only
    echo.
    echo Examples:
    echo   %0 4.0.3                    # Deploy version 4.0.3
    echo   %0 4.1.0 build              # Update to 4.1.0 and build
    echo   %0 show                     # Show current configuration
goto :end

:end
pause
