#!/bin/bash
# Quick Docker version manager and builder
# Usage: ./quick-docker.sh [new-version] [action]
# Examples:
#   ./quick-docker.sh 4.0.2        # Update version and build+push
#   ./quick-docker.sh 4.1.0 build  # Update version and build only
#   ./quick-docker.sh show          # Show current version
#   ./quick-docker.sh               # Interactive mode

set -e

REPO_NAME="hsayfi/overseerr-telegram-bot"
CONFIG_FILES=("docker-build.sh" "docker-build.bat" "DOCKER-HUB-DEPLOY.md")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to get current version from docker-build.sh
get_current_version() {
    if [ -f "docker-build.sh" ]; then
        grep 'DEFAULT_VERSION=' docker-build.sh | cut -d'"' -f2
    else
        echo "unknown"
    fi
}

# Function to get current build number
get_current_build() {
    if [ -f "config/constants.py" ]; then
        grep 'BUILD = ' config/constants.py | cut -d'"' -f2
    else
        date '+%Y.%m.%d.%H%M'
    fi
}

# Function to generate new build number
generate_build_number() {
    date '+%Y.%m.%d.%H%M'
}

# Function to update version and build in all config files
update_version() {
    local old_version="$1"
    local new_version="$2"
    local old_build=$(get_current_build)
    local new_build=$(generate_build_number)
    
    echo -e "${BLUE}📝 Updating version from ${old_version} to ${new_version}...${NC}"
    echo -e "${BLUE}🏗️ Updating build from ${old_build} to ${new_build}...${NC}"
    
    # Update docker-build.sh
    if [ -f "docker-build.sh" ]; then
        sed -i "s/DEFAULT_VERSION=\"${old_version}\"/DEFAULT_VERSION=\"${new_version}\"/g" docker-build.sh
        echo "  ✅ Updated docker-build.sh"
    fi
    
    # Update docker-build.bat
    if [ -f "docker-build.bat" ]; then
        sed -i "s/DEFAULT_VERSION=${old_version}/DEFAULT_VERSION=${new_version}/g" docker-build.bat
        echo "  ✅ Updated docker-build.bat"
    fi
    
    # Update config/constants.py
    if [ -f "config/constants.py" ]; then
        sed -i "s/VERSION = \"${old_version}\"/VERSION = \"${new_version}\"/g" config/constants.py
        sed -i "s/BUILD = \"${old_build}\"/BUILD = \"${new_build}\"/g" config/constants.py
        echo "  ✅ Updated config/constants.py"
    fi
    
    # Update telegram_overseerr_bot.py
    if [ -f "telegram_overseerr_bot.py" ]; then
        sed -i "s/VERSION = \"${old_version}\"/VERSION = \"${new_version}\"/g" telegram_overseerr_bot.py
        sed -i "s/BUILD = \"${old_build}\"/BUILD = \"${new_build}\"/g" telegram_overseerr_bot.py
        echo "  ✅ Updated telegram_overseerr_bot.py"
    fi
    
    # Update bot.py
    if [ -f "bot.py" ]; then
        sed -i "s/Version: ${old_version}/Version: ${new_version}/g" bot.py
        sed -i "s/Build: ${old_build}/Build: ${new_build}/g" bot.py
        echo "  ✅ Updated bot.py"
    fi
    
    # Update documentation
    if [ -f "DOCKER-HUB-DEPLOY.md" ]; then
        sed -i "s/${old_version}/${new_version}/g" DOCKER-HUB-DEPLOY.md
        echo "  ✅ Updated DOCKER-HUB-DEPLOY.md"
    fi
}

# Function to build Docker images
build_images() {
    local version="$1"
    
    echo -e "${BLUE}🏗️  Building Docker images for version ${version}...${NC}"
    
    # Build with version tag
    docker build -t "${REPO_NAME}:${version}" .
    echo -e "${GREEN}  ✅ Built ${REPO_NAME}:${version}${NC}"
    
    # Tag as latest
    docker tag "${REPO_NAME}:${version}" "${REPO_NAME}:latest"
    echo -e "${GREEN}  ✅ Tagged as ${REPO_NAME}:latest${NC}"
}

# Function to push images to Docker Hub
push_images() {
    local version="$1"
    
    echo -e "${BLUE}🚀 Pushing images to Docker Hub...${NC}"
    
    # Push version tag
    docker push "${REPO_NAME}:${version}"
    echo -e "${GREEN}  ✅ Pushed ${REPO_NAME}:${version}${NC}"
    
    # Push latest tag
    docker push "${REPO_NAME}:latest"
    echo -e "${GREEN}  ✅ Pushed ${REPO_NAME}:latest${NC}"
}

# Function to commit and tag with git
git_commit_and_tag() {
    local version="$1"
    
    echo -e "${BLUE}📝 Committing changes and creating git tag...${NC}"
    
    # Add all changes
    git add .
    
    # Commit changes
    git commit -m "Update Docker version to ${version}

- Updated build scripts and documentation
- Ready for Docker Hub deployment
- Version: ${version}" || echo "  ℹ️  No changes to commit"
    
    # Create git tag
    git tag "v${version}" 2>/dev/null || echo "  ℹ️  Tag v${version} already exists"
    
    # Push to origin
    git push origin refactored-modular-structure
    git push origin "v${version}" 2>/dev/null || echo "  ℹ️  Tag already pushed"
    
    echo -e "${GREEN}  ✅ Git operations completed${NC}"
}

# Function to show current status
show_status() {
    local current_version=$(get_current_version)
    
    echo -e "${BLUE}📊 Current Docker Configuration${NC}"
    echo "================================"
    echo "🏷️  Current Version: ${current_version}"
    echo "🐳 Repository: ${REPO_NAME}"
    echo "📁 Config Files: ${CONFIG_FILES[*]}"
    echo ""
    
    # Show recent Docker images
    echo -e "${BLUE}🖼️  Recent Docker Images:${NC}"
    docker images "${REPO_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedSince}}\t{{.Size}}" 2>/dev/null || echo "  No images found"
    echo ""
    
    # Show recent git tags
    echo -e "${BLUE}🏷️  Recent Git Tags:${NC}"
    git tag --sort=-version:refname | head -5 | sed 's/^/  /'
}

# Interactive mode
interactive_mode() {
    local current_version=$(get_current_version)
    
    echo -e "${YELLOW}🤖 Interactive Docker Version Manager${NC}"
    echo "====================================="
    echo "Current version: ${current_version}"
    echo ""
    
    read -p "Enter new version (e.g., 4.0.3, 4.1.0): " new_version
    
    if [ -z "$new_version" ]; then
        echo -e "${RED}❌ No version provided. Exiting.${NC}"
        exit 1
    fi
    
    echo ""
    echo "What would you like to do?"
    echo "1) Update version only"
    echo "2) Update + Build images"
    echo "3) Update + Build + Push to Docker Hub"
    echo "4) Full deployment (Update + Build + Push + Git commit/tag)"
    echo ""
    
    read -p "Choose option (1-4): " choice
    
    case $choice in
        1)
            update_version "$current_version" "$new_version"
            ;;
        2)
            update_version "$current_version" "$new_version"
            build_images "$new_version"
            ;;
        3)
            update_version "$current_version" "$new_version"
            build_images "$new_version"
            push_images "$new_version"
            ;;
        4)
            update_version "$current_version" "$new_version"
            build_images "$new_version"
            push_images "$new_version"
            git_commit_and_tag "$new_version"
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Exiting.${NC}"
            exit 1
            ;;
    esac
}

# Main script logic
main() {
    local new_version="$1"
    local action="$2"
    local current_version=$(get_current_version)
    
    # Check if we're in the right directory
    if [ ! -f "bot.py" ]; then
        echo -e "${RED}❌ Error: bot.py not found. Please run this script from the project root.${NC}"
        exit 1
    fi
    
    case "$new_version" in
        "show"|"status"|"")
            if [ -z "$new_version" ]; then
                interactive_mode
            else
                show_status
            fi
            ;;
        *)
            if [ -z "$action" ]; then
                # Default: full deployment
                echo -e "${YELLOW}🚀 Full deployment for version ${new_version}${NC}"
                update_version "$current_version" "$new_version"
                build_images "$new_version"
                push_images "$new_version"
                git_commit_and_tag "$new_version"
            else
                case "$action" in
                    "build")
                        update_version "$current_version" "$new_version"
                        build_images "$new_version"
                        ;;
                    "push")
                        update_version "$current_version" "$new_version"
                        build_images "$new_version"
                        push_images "$new_version"
                        ;;
                    "update")
                        update_version "$current_version" "$new_version"
                        ;;
                    *)
                        echo -e "${RED}❌ Unknown action: $action${NC}"
                        echo "Available actions: build, push, update"
                        exit 1
                        ;;
                esac
            fi
            ;;
    esac
    
    echo -e "${GREEN}✅ Operation completed successfully!${NC}"
}

# Show usage if --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "🐳 Quick Docker Version Manager"
    echo ""
    echo "Usage:"
    echo "  $0                          # Interactive mode"
    echo "  $0 show                     # Show current status"
    echo "  $0 <version>                # Full deployment (update + build + push + git)"
    echo "  $0 <version> build          # Update version and build only"
    echo "  $0 <version> push           # Update, build, and push to Docker Hub"
    echo "  $0 <version> update         # Update version in files only"
    echo ""
    echo "Examples:"
    echo "  $0 4.0.3                    # Deploy version 4.0.3"
    echo "  $0 4.1.0 build              # Update to 4.1.0 and build"
    echo "  $0 show                     # Show current configuration"
    exit 0
fi

# Run main function
main "$@"
