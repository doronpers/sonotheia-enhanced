#!/bin/bash
# set-branch-protection.sh
#
# Script to configure branch protection rules for a GitHub repository using the GitHub API.
# This enforces CI checks, code review requirements, and prevents force pushes.
#
# Usage:
#   GITHUB_TOKEN=ghp_xxxxx ./scripts/set-branch-protection.sh owner repo branch
#
# Example:
#   GITHUB_TOKEN=ghp_xxxxx ./scripts/set-branch-protection.sh doronpers sonotheia-enhanced main
#
# Requirements:
#   - GitHub personal access token with 'repo' scope
#   - curl and jq installed
#   - Admin access to the repository

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
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required scopes: repo"
    exit 1
fi

# Check for required tools
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed (optional but recommended)"
    echo "Install with: apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
fi

API_URL="https://api.github.com/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection"

echo "Setting branch protection for ${OWNER}/${REPO}:${BRANCH}"
echo "API URL: ${API_URL}"
echo ""

# Create the protection configuration
# See: https://docs.github.com/en/rest/branches/branch-protection
PROTECTION_CONFIG=$(cat <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "test"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 2,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF
)

# Apply the branch protection
echo "Applying branch protection rules..."
echo ""

HTTP_CODE=$(curl -s -o /tmp/gh-response.json -w "%{http_code}" \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "${API_URL}" \
  -d "${PROTECTION_CONFIG}")

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
    echo "✓ Branch protection rules applied successfully!"
    echo ""
    echo "Protection summary:"
    echo "  - Required status checks: lint, test"
    echo "  - Required reviews: 2"
    echo "  - Dismiss stale reviews: Yes"
    echo "  - Require code owner reviews: Yes"
    echo "  - Enforce for administrators: Yes"
    echo "  - Allow force pushes: No"
    echo "  - Allow deletions: No"
    echo ""
    
    if command -v jq &> /dev/null; then
        echo "Full response:"
        cat /tmp/gh-response.json | jq '.'
    else
        echo "Response saved to: /tmp/gh-response.json"
    fi
else
    echo "✗ Failed to apply branch protection (HTTP ${HTTP_CODE})"
    echo ""
    echo "Response:"
    cat /tmp/gh-response.json
    echo ""
    echo ""
    echo "Common issues:"
    echo "  - Invalid token or insufficient permissions (need 'repo' scope)"
    echo "  - Branch doesn't exist"
    echo "  - Not an admin of the repository"
    echo "  - Required status checks (lint, test) don't exist yet"
    echo ""
    echo "To debug:"
    echo "  - Verify token at: https://github.com/settings/tokens"
    echo "  - Check repository admin access"
    echo "  - Ensure status checks have run at least once"
    exit 1
fi

# Clean up
rm -f /tmp/gh-response.json

echo ""
echo "View protection settings at:"
echo "https://github.com/${OWNER}/${REPO}/settings/branches"
