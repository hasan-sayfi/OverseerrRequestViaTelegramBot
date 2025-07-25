@echo off
REM Version bumping utility for Windows with automatic file updates
REM Usage: bump-version.bat [patch|minor|major] [--auto]

setlocal enabledelayedexpansion

REM Function to get current version
:get_current_version
if exist "docker-build.bat" (
    for /f "tokens=2 delims==" %%i in ('findstr "DEFAULT_VERSION" docker-build.bat') do set CURRENT_VERSION=%%i
) else (
    set CURRENT_VERSION=4.0.1
)
goto :eof

REM Function to get current build
:get_current_build
if exist "config\constants.py" (
    for /f "tokens=3 delims=^"" %%i in ('findstr "BUILD = " config\constants.py') do set CURRENT_BUILD=%%i
) else (
    for /f "tokens=1-5 delims=:. " %%a in ("%date% %time%") do (
        set CURRENT_BUILD=%%c.%%a.%%b.%%d%%e
    )
)
goto :eof

REM Function to generate build number
:generate_build_number
for /f "tokens=1-5 delims=:. " %%a in ("%date% %time%") do (
    set NEW_BUILD=%%c.%%a.%%b.%%d%%e
)
goto :eof

REM Function to bump version
:bump_version
set CURRENT=%1
set BUMP_TYPE=%2

for /f "tokens=1-3 delims=." %%a in ("%CURRENT%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

if "%BUMP_TYPE%"=="patch" (
    set /a PATCH=!PATCH!+1
) else if "%BUMP_TYPE%"=="minor" (
    set /a MINOR=!MINOR!+1
    set PATCH=0
) else if "%BUMP_TYPE%"=="major" (
    set /a MAJOR=!MAJOR!+1
    set MINOR=0
    set PATCH=0
) else (
    echo ❌ Invalid bump type. Use: patch, minor, or major
    exit /b 1
)

set NEW_VERSION=!MAJOR!.!MINOR!.!PATCH!
goto :eof

REM Function to update version in files
:update_version_in_files
set OLD_VERSION=%1
set NEW_VERSION=%2
set OLD_BUILD=%3
set NEW_BUILD=%4

echo 📝 Updating version and build numbers in files...

REM Update config/constants.py
if exist "config\constants.py" (
    powershell -Command "(Get-Content 'config\constants.py') -replace 'VERSION = \"%OLD_VERSION%\"', 'VERSION = \"%NEW_VERSION%\"' | Set-Content 'config\constants.py'"
    powershell -Command "(Get-Content 'config\constants.py') -replace 'BUILD = \"%OLD_BUILD%\"', 'BUILD = \"%NEW_BUILD%\"' | Set-Content 'config\constants.py'"
    echo    ✅ config/constants.py
)

REM Update telegram_overseerr_bot.py
if exist "telegram_overseerr_bot.py" (
    powershell -Command "(Get-Content 'telegram_overseerr_bot.py') -replace 'VERSION = \"%OLD_VERSION%\"', 'VERSION = \"%NEW_VERSION%\"' | Set-Content 'telegram_overseerr_bot.py'"
    powershell -Command "(Get-Content 'telegram_overseerr_bot.py') -replace 'BUILD = \"%OLD_BUILD%\"', 'BUILD = \"%NEW_BUILD%\"' | Set-Content 'telegram_overseerr_bot.py'"
    echo    ✅ telegram_overseerr_bot.py
)

REM Update bot.py
if exist "bot.py" (
    powershell -Command "(Get-Content 'bot.py') -replace 'Version: %OLD_VERSION%', 'Version: %NEW_VERSION%' | Set-Content 'bot.py'"
    powershell -Command "(Get-Content 'bot.py') -replace 'Build: %OLD_BUILD%', 'Build: %NEW_BUILD%' | Set-Content 'bot.py'"
    echo    ✅ bot.py
)

REM Update docker-build.sh
if exist "docker-build.sh" (
    powershell -Command "(Get-Content 'docker-build.sh') -replace 'DEFAULT_VERSION=\"%OLD_VERSION%\"', 'DEFAULT_VERSION=\"%NEW_VERSION%\"' | Set-Content 'docker-build.sh'"
    echo    ✅ docker-build.sh
)

REM Update docker-build.bat
if exist "docker-build.bat" (
    powershell -Command "(Get-Content 'docker-build.bat') -replace 'set DEFAULT_VERSION=%OLD_VERSION%', 'set DEFAULT_VERSION=%NEW_VERSION%' | Set-Content 'docker-build.bat'"
    echo    ✅ docker-build.bat
)

REM Update DOCKER-HUB-DEPLOY.md
if exist "DOCKER-HUB-DEPLOY.md" (
    powershell -Command "(Get-Content 'DOCKER-HUB-DEPLOY.md') -replace '%OLD_VERSION%', '%NEW_VERSION%' | Set-Content 'DOCKER-HUB-DEPLOY.md'"
    echo    ✅ DOCKER-HUB-DEPLOY.md
)

echo ✅ All files updated successfully!
goto :eof

REM Main script
set AUTO_MODE=false
set BUMP_TYPE=patch

REM Parse arguments
:parse_args
if "%1"=="--auto" (
    set AUTO_MODE=true
    shift
    goto parse_args
)
if "%1"=="patch" set BUMP_TYPE=patch
if "%1"=="minor" set BUMP_TYPE=minor
if "%1"=="major" set BUMP_TYPE=major

call :get_current_version
call :get_current_build
call :bump_version %CURRENT_VERSION% %BUMP_TYPE%
call :generate_build_number

echo 🔄 Version Bump: %CURRENT_VERSION% → %NEW_VERSION% (%BUMP_TYPE%)
echo 🏗️ Build Update: %CURRENT_BUILD% → %NEW_BUILD%
echo.

if "%AUTO_MODE%"=="true" (
    echo 🚀 Auto mode: Updating files automatically...
    call :update_version_in_files "%CURRENT_VERSION%" "%NEW_VERSION%" "%CURRENT_BUILD%" "%NEW_BUILD%"
    echo.
    echo 🎯 Next steps:
    echo   git add .
    echo   git commit -m "Bump version to %NEW_VERSION%"
    echo   quick-docker.bat %NEW_VERSION%
) else (
    echo 💡 Manual mode: Choose your next action:
    echo.
    echo 📝 Update files automatically:
    echo   bump-version.bat %BUMP_TYPE% --auto
    echo.
    echo 🚀 Direct deployment (updates files + builds + deploys^):
    echo   quick-docker.bat %NEW_VERSION%
    echo.
    echo 🔧 Manual build commands:
    echo   quick-docker.bat %NEW_VERSION% build  # Build only
    echo   quick-docker.bat %NEW_VERSION% push   # Build and push
)

endlocal
