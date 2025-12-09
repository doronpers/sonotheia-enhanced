#!/bin/bash
# Script to set branch protection rules using GitHub API
# Usage: GITHUB_TOKEN=ghp_xxx ./scripts/set-branch-protection.sh owner repo branch
#
# Required GitHub token scopes: repo
# 
# This script configures branch protection with:
# - Required status checks (lint, test)
# - Required code owner reviews
# - 2 approving reviews required
# - Stale review dismissal
# - Admin enforcement
# - No force pushes or deletions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required arguments are provided
if [ $# -lt 3 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: GITHUB_TOKEN=ghp_xxx $0 <owner> <repo> <branch>"
    echo ""
    echo "Example:"
    echo "  GITHUB_TOKEN=ghp_xxx $0 doronpers sonotheia-enhanced main"
    exit 1
fi

OWNER=$1
REPO=$2
BRANCH=$3

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable is not set${NC}"
    echo "Please set your GitHub personal access token:"
    echo "  export GITHUB_TOKEN=ghp_xxx"
    echo ""
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required scopes: repo"
    exit 1
fi

echo -e "${GREEN}Setting branch protection for ${OWNER}/${REPO} on branch '${BRANCH}'...${NC}"
echo ""

# Branch protection configuration
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

# API endpoint
API_URL="https://api.github.com/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection"

# Make the API request
echo "Applying branch protection rules..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$API_URL" \
  -d "$PROTECTION_CONFIG")

# Extract HTTP status code
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

# Check response
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✅ Branch protection successfully configured!${NC}"
    echo ""
    echo "Protection settings:"
    echo "  - Required status checks: lint, test"
    echo "  - Required approving reviews: 2"
    echo "  - Dismiss stale reviews: enabled"
    echo "  - Require code owner reviews: enabled"
    echo "  - Enforce for admins: enabled"
    echo "  - Allow force pushes: disabled"
    echo "  - Allow deletions: disabled"
    echo ""
    echo -e "${GREEN}View protection rules at:${NC}"
    echo "  https://github.com/${OWNER}/${REPO}/settings/branches"
else
    echo -e "${RED}❌ Failed to set branch protection${NC}"
    echo "HTTP Status Code: $HTTP_CODE"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo "  - Token doesn't have 'repo' scope"
    echo "  - Branch doesn't exist yet"
    echo "  - User doesn't have admin permissions"
    echo "  - Repository name or owner is incorrect"
    exit 1
fi

# Additional note about status checks
echo ""
echo -e "${YELLOW}Note:${NC} Make sure the status checks 'lint' and 'test' exist in your CI workflow"
echo "Check .github/workflows/ci.yml to ensure job names match the required contexts."
echo ""
echo -e "${GREEN}Setup complete!${NC}"
