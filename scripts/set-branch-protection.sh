#!/bin/bash
# set-branch-protection.sh
#
# Script to configure branch protection rules for a GitHub repository using the GitHub API.
# Enforces required status checks, code owner reviews, and prevents force pushes.
#
# Usage:
#   GITHUB_TOKEN=ghp_xxxxx ./scripts/set-branch-protection.sh <owner> <repo> <branch>
# Example:
#   GITHUB_TOKEN=ghp_xxxxx ./scripts/set-branch-protection.sh doronpers sonotheia-enhanced main
#
# Requirements:
#   - GitHub personal access token with 'repo' scope
#   - curl and jq installed
#   - Admin access to the repository
#
# This script configures branch protection with:
# - Required status checks (CI, LFS Check)  # update names to match your workflows
# - Required code owner reviews
set -e

# Check arguments
if [ $# -ne 3 ]; then
  echo "Usage: GITHUB_TOKEN=ghp_xxxxx $0 <owner> <repo> <branch>"
  echo "Example: GITHUB_TOKEN=ghp_xxxxx $0 doronpers sonotheia-enhanced main"
  exit 1
fi

OWNER="$1"
REPO="$2"
BRANCH="$3"

# Check for required environment variable
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is not set"
  exit 1
fi
