#!/bin/bash
#
# Documentation Automation Kit - Uninstaller
# Removes documentation automation system from repository
#

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Documentation Automation Kit - Uninstaller v1.0        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  This will remove the documentation automation system.${NC}"
echo ""
echo "The following will be removed:"
echo "  • .github/workflows/documentation-review.yml"
echo "  • .github/workflows/auto-generate-docs.yml"
echo "  • .github/scripts/*.py (8 scripts)"
echo "  • .github/cspell.json"
echo "  • .markdownlint.json"
echo "  • .github/README.md"
echo "  • .github/QUICK_REFERENCE.md"
echo "  • .github/ARCHITECTURE.md"
echo ""
echo -e "${YELLOW}Backup files (.backup) will be preserved.${NC}"
echo ""

read -p "Continue with uninstallation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "🗑️  Removing files..."

# Remove workflows
rm -f .github/workflows/documentation-review.yml
rm -f .github/workflows/auto-generate-docs.yml
echo "  ✓ Removed workflows"

# Remove scripts
rm -f .github/scripts/validate-docs.py
rm -f .github/scripts/check-links.py
rm -f .github/scripts/check-dates.py
rm -f .github/scripts/check-completeness.py
rm -f .github/scripts/generate-api-docs.py
rm -f .github/scripts/generate-component-docs.py
rm -f .github/scripts/update-changelog.py
rm -f .github/scripts/generate-report.py
echo "  ✓ Removed scripts"

# Remove config
rm -f .github/cspell.json
rm -f .markdownlint.json
echo "  ✓ Removed configuration"

# Remove documentation
rm -f .github/README.md
rm -f .github/QUICK_REFERENCE.md
rm -f .github/ARCHITECTURE.md
echo "  ✓ Removed documentation"

echo ""
echo "✅ Uninstallation complete"
echo ""
echo "Backup files (.backup) have been preserved if they exist."
echo ""
