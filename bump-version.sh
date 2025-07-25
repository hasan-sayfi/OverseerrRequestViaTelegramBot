#!/bin/bash
# Version bumping utility with automatic file updates
# Usage: ./bump-version.sh [patch|minor|major] [--auto]

get_current_version() {
    if [ -f "docker-build.sh" ]; then
        grep 'DEFAULT_VERSION=' docker-build.sh | cut -d'"' -f2
    else
        echo "4.0.1"
    fi
}

get_current_build() {
    if [ -f "config/constants.py" ]; then
        grep 'BUILD = ' config/constants.py | cut -d'"' -f2
    else
        date '+%Y.%m.%d.%H%M'
    fi
}

generate_build_number() {
    date '+%Y.%m.%d.%H%M'
}

bump_version() {
    local current="$1"
    local bump_type="$2"
    
    IFS='.' read -ra PARTS <<< "$current"
    local major="${PARTS[0]}"
    local minor="${PARTS[1]}"
    local patch="${PARTS[2]}"
    
    case "$bump_type" in
        "patch")
            patch=$((patch + 1))
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        *)
            echo "❌ Invalid bump type. Use: patch, minor, or major"
            exit 1
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

update_version_in_files() {
    local old_version="$1"
    local new_version="$2"
    local old_build="$3"
    local new_build="$4"
    
    echo "📝 Updating version and build numbers in files..."
    
    # Update config/constants.py
    if [ -f "config/constants.py" ]; then
        sed -i "s/VERSION = \"$old_version\"/VERSION = \"$new_version\"/g" config/constants.py
        sed -i "s/BUILD = \"$old_build\"/BUILD = \"$new_build\"/g" config/constants.py
        echo "   ✅ config/constants.py"
    fi
    
    # Update telegram_overseerr_bot.py
    if [ -f "telegram_overseerr_bot.py" ]; then
        sed -i "s/VERSION = \"$old_version\"/VERSION = \"$new_version\"/g" telegram_overseerr_bot.py
        sed -i "s/BUILD = \"$old_build\"/BUILD = \"$new_build\"/g" telegram_overseerr_bot.py
        echo "   ✅ telegram_overseerr_bot.py"
    fi
    
    # Update bot.py
    if [ -f "bot.py" ]; then
        sed -i "s/Version: $old_version/Version: $new_version/g" bot.py
        sed -i "s/Build: $old_build/Build: $new_build/g" bot.py
        echo "   ✅ bot.py"
    fi
    
    # Update docker-build.sh
    if [ -f "docker-build.sh" ]; then
        sed -i "s/DEFAULT_VERSION=\"$old_version\"/DEFAULT_VERSION=\"$new_version\"/g" docker-build.sh
        echo "   ✅ docker-build.sh"
    fi
    
    # Update docker-build.bat
    if [ -f "docker-build.bat" ]; then
        sed -i "s/set DEFAULT_VERSION=$old_version/set DEFAULT_VERSION=$new_version/g" docker-build.bat
        echo "   ✅ docker-build.bat"
    fi
    
    # Update DOCKER-HUB-DEPLOY.md
    if [ -f "DOCKER-HUB-DEPLOY.md" ]; then
        sed -i "s/$old_version/$new_version/g" DOCKER-HUB-DEPLOY.md
        echo "   ✅ DOCKER-HUB-DEPLOY.md"
    fi
    
    echo "✅ All files updated successfully!"
}

# Parse arguments
auto_mode=false
bump_type="patch"

for arg in "$@"; do
    case $arg in
        --auto)
            auto_mode=true
            ;;
        patch|minor|major)
            bump_type="$arg"
            ;;
        *)
            if [ "$arg" != "--auto" ]; then
                bump_type="$arg"
            fi
            ;;
    esac
done

current_version=$(get_current_version)
current_build=$(get_current_build)
new_version=$(bump_version "$current_version" "$bump_type")
new_build=$(generate_build_number)

echo "🔄 Version Bump: $current_version → $new_version ($bump_type)"
echo "🏗️ Build Update: $current_build → $new_build"
echo ""

if [ "$auto_mode" = true ]; then
    echo "🚀 Auto mode: Updating files automatically..."
    update_version_in_files "$current_version" "$new_version" "$current_build" "$new_build"
    echo ""
    echo "🎯 Next steps:"
    echo "  git add ."
    echo "  git commit -m \"Bump version to $new_version\""
    echo "  ./quick-docker.sh $new_version"
else
    echo "💡 Manual mode: Choose your next action:"
    echo ""
    echo "📝 Update files automatically:"
    echo "  ./bump-version.sh $bump_type --auto"
    echo ""
    echo "🚀 Direct deployment (updates files + builds + deploys):"
    echo "  ./quick-docker.sh $new_version"
    echo ""
    echo "🔧 Manual build commands:"
    echo "  ./quick-docker.sh $new_version build  # Build only"
    echo "  ./quick-docker.sh $new_version push   # Build and push"
fi
