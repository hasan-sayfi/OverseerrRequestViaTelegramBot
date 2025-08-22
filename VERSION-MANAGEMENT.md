# 🚀 Quick Docker Version Management

This project includes powerful scripts to automatically manage both **version numbers AND build timestamps** across all files.

## 🔄 What Gets Updated Automatically

When you bump versions, the system automatically updates:

### 📝 Bot Source Files (Version + Build)
- **`config/constants.py`** - VERSION and BUILD constants
- **`telegram_overseerr_bot.py`** - VERSION and BUILD constants  
- **`bot.py`** - Version and Build in docstring

### 🐳 Docker Configuration (Version)
- **`docker-build.sh`** - DEFAULT_VERSION variable
- **`docker-build.bat`** - DEFAULT_VERSION variable

### 📚 Documentation (Version)
- **`DOCKER-HUB-DEPLOY.md`** - All version references

### 🏗️ Build Numbers
- **Auto-generated** using format: `YYYY.MM.DD.HHMM`
- **Example**: `2025.07.25.1530` (July 25, 2025 at 3:30 PM)

## 📋 Quick Commands Overview

| Command | Description |
|---------|-------------|
| `./quick-docker.sh` | Interactive mode - guided setup |
| `./quick-docker.sh 4.0.3` | Full deployment (update files + build + push + git) |
| `./quick-docker.sh 4.0.3 build` | Update files and build only |
| `./quick-docker.sh 4.0.3 push` | Update files, build, and push to Docker Hub |
| `./quick-docker.sh show` | Show current version and status |
| `./bump-version.sh patch` | Suggest next patch version (4.0.1 → 4.0.2) |
| `./bump-version.sh patch --auto` | Auto-update files to next patch version |
| `./bump-version.sh minor --auto` | Auto-update files to next minor version |
| `./bump-version.sh major --auto` | Auto-update files to next major version |

## 🎯 Common Use Cases

### 1. Quick Bug Fix Release (Automatic Files + Build)
```bash
# Option A: One command does everything
./quick-docker.sh 4.0.2           # Updates files + builds + pushes + git

# Option B: Step by step  
./bump-version.sh patch --auto     # Updates files: 4.0.1 → 4.0.2
./quick-docker.sh 4.0.2           # Build and deploy
```

### 2. New Feature Release (Automatic Files + Build)
```bash
# Get suggested version
./bump-version.sh minor           # Shows: 4.0.1 → 4.1.0

# Deploy it
./quick-docker.sh 4.1.0           # Full deployment
```

### 3. Test Build Only
```bash
./quick-docker.sh 4.0.3 build     # Just build, don't push
```

### 4. Check Current Status
```bash
./quick-docker.sh show            # See current version, images, tags
```

### 5. Interactive Mode
```bash
./quick-docker.sh                 # Guided interactive setup
```

## 🪟 Windows Users

Use the `.bat` versions:
```cmd
quick-docker.bat                  # Interactive mode
quick-docker.bat 4.0.3            # Full deployment
quick-docker.bat 4.0.3 build      # Build only
quick-docker.bat show             # Show status
```

## 🔄 Version Management Workflow

### Typical Release Process:
1. **Check current version**: `./quick-docker.sh show`
2. **Get next version**: `./bump-version.sh patch` (or `minor`/`major`)
3. **Deploy**: `./quick-docker.sh X.Y.Z`

### What happens during full deployment:
1. ✅ Updates version in all config files
2. ✅ Builds Docker images with new tag
3. ✅ Pushes to Docker Hub
4. ✅ Commits changes to git
5. ✅ Creates and pushes git tag

## 📁 Files That Get Updated

The scripts automatically update these files:
- `docker-build.sh` - Linux/macOS build script
- `docker-build.bat` - Windows build script  
- `DOCKER-HUB-DEPLOY.md` - Documentation examples

## 🎮 Interactive Mode Features

When you run `./quick-docker.sh` without arguments:
- Shows current version
- Prompts for new version
- Offers action choices:
  1. Update version only
  2. Update + Build
  3. Update + Build + Push
  4. Full deployment (includes Git)

## 🚨 Safety Features

- ✅ Checks if you're in the right directory (`bot.py` must exist)
- ✅ Shows what will happen before doing it
- ✅ Colored output for easy reading
- ✅ Error handling for failed builds/pushes
- ✅ Git operations handle existing tags gracefully

## 🔍 Examples

### Example 1: Quick Patch Release
```bash
$ ./bump-version.sh patch
🔄 Version Bump: 4.0.1 → 4.0.2 (patch)

Run one of these commands:
  ./quick-docker.sh 4.0.2        # Full deployment
  ./quick-docker.sh 4.0.2 build  # Build only

$ ./quick-docker.sh 4.0.2
🚀 Full deployment for version 4.0.2
📝 Updating version from 4.0.1 to 4.0.2...
  ✅ Updated docker-build.sh
  ✅ Updated docker-build.bat
  ✅ Updated DOCKER-HUB-DEPLOY.md
🏗️ Building Docker images for version 4.0.2...
  ✅ Built hsayfi/overseerr-telegram-bot:4.0.2
  ✅ Tagged as hsayfi/overseerr-telegram-bot:latest
🚀 Pushing images to Docker Hub...
  ✅ Pushed hsayfi/overseerr-telegram-bot:4.0.2
  ✅ Pushed hsayfi/overseerr-telegram-bot:latest
📝 Committing changes and creating git tag...
  ✅ Git operations completed
✅ Operation completed successfully!
```

### Example 2: Check Status
```bash
$ ./quick-docker.sh show
📊 Current Docker Configuration
================================
🏷️ Current Version: 4.0.2
🐳 Repository: hsayfi/overseerr-telegram-bot
📁 Config Files: docker-build.sh docker-build.bat DOCKER-HUB-DEPLOY.md

🖼️ Recent Docker Images:
REPOSITORY                    TAG       CREATED        SIZE
hsayfi/overseerr-telegram-bot 4.0.2     2 minutes ago  245MB
hsayfi/overseerr-telegram-bot latest    2 minutes ago  245MB

🏷️ Recent Git Tags:
  v4.0.2
  v4.0.1
  v4.0.0
```

## 💡 Pro Tips

1. **Always check status first**: `./quick-docker.sh show`
2. **Use version bumping**: `./bump-version.sh patch` then copy the suggested command
3. **Test builds locally**: Use `build` action before pushing
4. **Interactive mode is great for learning**: Run `./quick-docker.sh` with no args

## 🔧 Customization

You can edit these variables in the scripts:
- `REPO_NAME` - Your Docker Hub repository name
- `CONFIG_FILES` - Files to update with new versions

This makes version management super fast and consistent! 🚀
