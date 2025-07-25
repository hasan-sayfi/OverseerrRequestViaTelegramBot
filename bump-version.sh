#!/bin/bash
# Version bumping utility
# Usage: ./bump-version.sh [patch|minor|major]

get_current_version() {
    if [ -f "docker-build.sh" ]; then
        grep 'DEFAULT_VERSION=' docker-build.sh | cut -d'"' -f2
    else
        echo "4.0.1"
    fi
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

current_version=$(get_current_version)
bump_type="${1:-patch}"
new_version=$(bump_version "$current_version" "$bump_type")

echo "🔄 Version Bump: $current_version → $new_version ($bump_type)"
echo ""
echo "Run one of these commands:"
echo "  ./quick-docker.sh $new_version        # Full deployment"
echo "  ./quick-docker.sh $new_version build  # Build only"
echo "  ./quick-docker.sh $new_version push   # Build and push"
