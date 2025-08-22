# 🔄 Automatic Version & Build Management

## ✨ What's New

Your version management system now **automatically updates both version AND build numbers** in all necessary files!

## 🎯 Files Updated Automatically

### 📝 Bot Source Files (Version + Build)
- **`config/constants.py`** → `VERSION = "4.0.2"` + `BUILD = "2025.07.25.0602"`
- **`telegram_overseerr_bot.py`** → `VERSION = "4.0.2"` + `BUILD = "2025.07.25.0602"`
- **`bot.py`** → `Version: 4.0.2` + `Build: 2025.07.25.0602`

### 🐳 Docker Config Files (Version)
- **`docker-build.sh`** → `DEFAULT_VERSION="4.0.2"`
- **`docker-build.bat`** → `DEFAULT_VERSION=4.0.2`

### 📚 Documentation (Version)
- **`DOCKER-HUB-DEPLOY.md`** → All examples use `4.0.2`

## 🚀 Usage Examples

### Method 1: One-Command Deployment
```bash
# This does EVERYTHING automatically:
# ✅ Updates version 4.0.1 → 4.0.2
# ✅ Updates build timestamp  
# ✅ Updates all 6 files above
# ✅ Builds Docker images
# ✅ Pushes to Docker Hub
# ✅ Creates git tag and pushes

./quick-docker.sh 4.0.2
```

### Method 2: Smart Version Bumping
```bash
# Auto-bump patch version (4.0.1 → 4.0.2) and update all files
./bump-version.sh patch --auto

# Auto-bump minor version (4.0.1 → 4.1.0) and update all files  
./bump-version.sh minor --auto

# Auto-bump major version (4.0.1 → 5.0.0) and update all files
./bump-version.sh major --auto

# Then deploy with the new version
./quick-docker.sh [new-version]
```

### Method 3: Windows Users
```cmd
REM Auto-bump and update files on Windows
bump-version.bat patch --auto
bump-version.bat minor --auto  
bump-version.bat major --auto

REM Deploy
quick-docker.bat [new-version]
```

### Method 4: Planning Mode
```bash
# See what version would be next (no changes made)
./bump-version.sh patch     # Shows: 4.0.1 → 4.0.2
./bump-version.sh minor     # Shows: 4.0.1 → 4.1.0
./bump-version.sh major     # Shows: 4.0.1 → 5.0.0
```

## 🏗️ Build Number Format

Build numbers are automatically generated as: **`YYYY.MM.DD.HHMM`**

- **Example**: `2025.07.25.1430` = July 25, 2025 at 2:30 PM
- **Updated**: Every time you bump version or deploy
- **Visible**: In bot welcome message and logs

## ✅ Benefits

1. **No Manual Editing**: Never manually edit version/build numbers again
2. **Consistency**: All files always have matching versions
3. **Traceability**: Build timestamps show exactly when each version was created
4. **Zero Errors**: No typos or forgotten files
5. **Fast Deployment**: One command does everything

## 🎉 Bot Welcome Message

Your users will now see the updated version:

```
Welcome to Overseerr Telegram Bot!

📱 Version: 4.0.2  
🔧 Build: 2025.07.25.0602
```

## 🔧 Next Release Workflow

For your next update:

```bash
# Quick patch fix
./bump-version.sh patch --auto && ./quick-docker.sh 4.0.3

# New feature  
./bump-version.sh minor --auto && ./quick-docker.sh 4.1.0

# Major release
./bump-version.sh major --auto && ./quick-docker.sh 5.0.0
```

That's it! Your version management is now fully automated! 🎉
