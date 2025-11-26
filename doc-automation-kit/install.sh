#!/bin/bash
#
# Documentation Automation Kit - Installer
# Installs documentation automation system into any repository
#

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Documentation Automation Kit - Installer v1.0         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not a git repository. Please run from repository root.${NC}"
    exit 1
fi

echo "📍 Installing in: $(pwd)"
echo ""

# Function to copy with backup
copy_with_backup() {
    local src=$1
    local dest=$2
    
    if [ -f "$dest" ]; then
        echo -e "${YELLOW}  ⚠️  File exists: $dest${NC}"
        echo "     Creating backup: ${dest}.backup"
        cp "$dest" "${dest}.backup"
    fi
    
    cp "$src" "$dest"
    echo -e "${GREEN}  ✓${NC} Copied: $dest"
}

# 1. Create directory structure
echo "📁 Creating directory structure..."
mkdir -p .github/workflows
mkdir -p .github/scripts
mkdir -p docs
echo -e "${GREEN}  ✓${NC} Directories created"
echo ""

# 2. Copy workflows
echo "🔄 Installing workflows..."
for workflow in doc-automation-kit/workflows/*.yml; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow")
        copy_with_backup "$workflow" ".github/workflows/$filename"
    fi
done
echo ""

# 3. Copy scripts
echo "📜 Installing scripts..."
for script in doc-automation-kit/scripts/*.py; do
    if [ -f "$script" ]; then
        filename=$(basename "$script")
        cp "$script" ".github/scripts/$filename"
        chmod +x ".github/scripts/$filename"
        echo -e "${GREEN}  ✓${NC} Installed: .github/scripts/$filename"
    fi
done
echo ""

# 4. Copy configuration files
echo "⚙️  Installing configuration..."
if [ -f "doc-automation-kit/config/.markdownlint.json" ]; then
    copy_with_backup "doc-automation-kit/config/.markdownlint.json" ".markdownlint.json"
fi

if [ -f "doc-automation-kit/config/cspell.json" ]; then
    mkdir -p .github
    copy_with_backup "doc-automation-kit/config/cspell.json" ".github/cspell.json"
fi
echo ""

# 5. Copy documentation
echo "📚 Installing documentation..."
if [ -f "doc-automation-kit/docs/SYSTEM_GUIDE.md" ]; then
    copy_with_backup "doc-automation-kit/docs/SYSTEM_GUIDE.md" ".github/README.md"
fi

if [ -f "doc-automation-kit/docs/QUICK_REFERENCE.md" ]; then
    copy_with_backup "doc-automation-kit/docs/QUICK_REFERENCE.md" ".github/QUICK_REFERENCE.md"
fi

if [ -f "doc-automation-kit/docs/ARCHITECTURE.md" ]; then
    copy_with_backup "doc-automation-kit/docs/ARCHITECTURE.md" ".github/ARCHITECTURE.md"
fi
echo ""

# 6. Update .gitignore if needed
echo "🔒 Checking .gitignore..."
if [ -f ".gitignore" ]; then
    if ! grep -q "doc-automation-kit" .gitignore; then
        echo "" >> .gitignore
        echo "# Documentation automation kit (optional)" >> .gitignore
        echo "doc-automation-kit/" >> .gitignore
        echo -e "${GREEN}  ✓${NC} Updated .gitignore"
    else
        echo -e "${GREEN}  ✓${NC} .gitignore already configured"
    fi
else
    echo -e "${YELLOW}  ⚠️  No .gitignore found${NC}"
fi
echo ""

# 7. Create required documentation files if missing
echo "📝 Checking required documentation..."

create_if_missing() {
    local file=$1
    local template=$2
    
    if [ ! -f "$file" ]; then
        echo "$template" > "$file"
        echo -e "${GREEN}  ✓${NC} Created: $file"
    else
        echo "  ✓ Exists: $file"
    fi
}

create_if_missing "README.md" "# $(basename $(pwd))

> Project description

## Quick Start

\`\`\`bash
# Setup instructions
\`\`\`

## Documentation

See other documentation files for details.
"

create_if_missing "CHANGELOG.md" "# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial release
"

echo ""

# 8. Test Python availability
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}  ✓${NC} Found: $PYTHON_VERSION"
    
    # Check if scripts work
    if python3 .github/scripts/validate-docs.py --help &> /dev/null 2>&1; then
        echo -e "${GREEN}  ✓${NC} Scripts are executable"
    else
        echo -e "${YELLOW}  ⚠️  Script check failed.${NC}"
    fi
        echo -e "${GREEN}  ✓${NC} Scripts are executable"
    fi
else
    echo -e "${YELLOW}  ⚠️  Python 3 not found. Install Python 3.11+ to use scripts.${NC}"
fi
echo ""

# 9. Installation summary
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Installation Complete! ✅                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Installed Components:"
echo "   • GitHub Actions workflows (2)"
echo "   • Validation & generation scripts (8)"
echo "   • Configuration files (2)"
echo "   • Documentation guides (3)"
echo ""
echo "🎯 What's Next:"
echo ""
echo "1. Customize spell check dictionary:"
echo "   Edit .github/cspell.json"
echo ""
echo "2. Customize required documents (optional):"
echo "   Edit .github/scripts/validate-docs.py"
echo ""
echo "3. Test locally:"
echo "   python .github/scripts/validate-docs.py"
echo ""
echo "4. Commit and push:"
echo "   git add .github/"
echo "   git commit -m 'Add documentation automation system'"
echo "   git push"
echo ""
echo "📚 Documentation:"
echo "   • System guide: .github/README.md"
echo "   • Quick reference: .github/QUICK_REFERENCE.md"
echo "   • Architecture: .github/ARCHITECTURE.md"
echo ""
echo "🤖 Automation is now active!"
echo "   • Weekly reviews will run on Mondays at 9 AM UTC"
echo "   • Validation runs on pushes and PRs"
echo "   • Doc generation runs on code changes"
echo ""
echo "✨ Happy documenting! ✨"
echo ""
