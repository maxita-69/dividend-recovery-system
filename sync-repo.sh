#!/bin/bash
# Sync Repository Script
# Synchronizes local repository with remote changes
#
# Usage:
#   ./sync-repo.sh              # Sync current branch
#   ./sync-repo.sh --with-main  # Also merge changes from main

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Starting repository sync...${NC}\n"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}📍 Current branch: ${CURRENT_BRANCH}${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    git status --short
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Sync cancelled${NC}"
        exit 1
    fi
fi

# Fetch all remote changes
echo -e "\n${BLUE}📥 Fetching remote changes...${NC}"
if git fetch origin; then
    echo -e "${GREEN}✅ Fetch completed${NC}"
else
    echo -e "${RED}❌ Fetch failed${NC}"
    exit 1
fi

# Check if current branch exists on remote
if git show-ref --verify --quiet "refs/remotes/origin/${CURRENT_BRANCH}"; then
    echo -e "\n${BLUE}🔽 Pulling changes for ${CURRENT_BRANCH}...${NC}"

    # Check if we're behind remote
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse "@{u}" 2>/dev/null || echo "")

    if [ -n "$REMOTE" ]; then
        BASE=$(git merge-base @ "@{u}")

        if [ "$LOCAL" = "$REMOTE" ]; then
            echo -e "${GREEN}✅ Already up-to-date${NC}"
        elif [ "$LOCAL" = "$BASE" ]; then
            echo -e "${YELLOW}⬇️  Pulling new changes...${NC}"
            git pull origin "$CURRENT_BRANCH"
            echo -e "${GREEN}✅ Pull completed${NC}"
        elif [ "$REMOTE" = "$BASE" ]; then
            echo -e "${YELLOW}⬆️  Local branch is ahead of remote${NC}"
        else
            echo -e "${YELLOW}⚠️  Branches have diverged${NC}"
            echo -e "${YELLOW}   Consider rebasing or merging${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Branch ${CURRENT_BRANCH} not found on remote${NC}"
    echo -e "${YELLOW}   This is a local-only branch${NC}"
fi

# Sync with main branch if requested
if [ "$1" = "--with-main" ] || [ "$1" = "-m" ]; then
    echo -e "\n${BLUE}🔄 Syncing with main branch...${NC}"

    # Fetch main branch
    if git fetch origin main:main 2>/dev/null || git fetch origin main 2>/dev/null; then
        echo -e "${GREEN}✅ Main branch updated${NC}"

        # Offer to merge main into current branch
        if [ "$CURRENT_BRANCH" != "main" ]; then
            echo -e "\n${YELLOW}Merge main into ${CURRENT_BRANCH}?${NC}"
            read -p "Continue? (y/n) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git merge main
                echo -e "${GREEN}✅ Merged main into ${CURRENT_BRANCH}${NC}"
            else
                echo -e "${BLUE}ℹ️  Skipped merge${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Could not fetch main branch${NC}"
    fi
fi

# Show summary
echo -e "\n${BLUE}📊 Repository Status:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━${NC}"
git status --short --branch

# Show recent commits
echo -e "\n${BLUE}📝 Recent commits (last 5):${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━${NC}"
git log --oneline --graph --decorate -5

echo -e "\n${GREEN}✅ Sync completed!${NC}"
