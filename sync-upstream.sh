#!/bin/bash
# This script synchronizes the local main branch with the upstream main branch.

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Check if the current branch is main
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "Error: This script should be run on the main branch."
  echo "You are currently on the '$CURRENT_BRANCH' branch."
  exit 1
fi

echo "Fetching updates from upstream..."
git fetch upstream

echo "Rebasing local main onto upstream/main..."
git rebase upstream/main

echo "Force pushing to origin/main..."
git push origin main --force

echo "Synchronization complete."
