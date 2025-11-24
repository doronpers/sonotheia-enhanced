# Documentation Automation Kit

> A portable, plug-and-play documentation automation system for any repository

## 🚀 Quick Install

Copy this kit to any repository and run the installer:

```bash
# Clone or download this kit
cp -r doc-automation-kit /path/to/your-repo/

# Run installer
cd /path/to/your-repo
./doc-automation-kit/install.sh
```

That's it! The automation system is now active in your repository.

## 📦 What's Included

### Automated Review System
- ✅ Validates documentation structure
- ✅ Checks for broken links (internal & external)
- ✅ Detects outdated dates
- ✅ Spell checking
- ✅ Markdown linting
- ✅ Runs weekly + on changes

### Automated Generation System
- 🔧 Generates API documentation from code
- 🧩 Generates component documentation
- 📝 Updates CHANGELOG from commits
- 🔄 Creates PRs for review

### Developer Tools
- 8 Python validation & generation scripts
- Pre-configured workflows
- Spell check dictionary
- Markdown linting rules

## 🛠️ Installation

### Option 1: Automatic (Recommended)

```bash
cd your-repository
./doc-automation-kit/install.sh
```

The installer will:
1. Copy workflows to `.github/workflows/`
2. Copy scripts to `.github/scripts/`
3. Copy configuration files
4. Create documentation templates
5. Update `.gitignore` if needed

### Option 2: Manual

```bash
# Copy workflows
cp doc-automation-kit/workflows/* .github/workflows/

# Copy scripts
cp doc-automation-kit/scripts/* .github/scripts/
chmod +x .github/scripts/*.py

# Copy config
cp doc-automation-kit/config/.markdownlint.json .
cp doc-automation-kit/config/cspell.json .github/

# Copy docs
cp doc-automation-kit/docs/*.md .github/
```

## ⚙️ Configuration

### 1. Update Spell Check Dictionary

Edit `.github/cspell.json` to add project-specific terms:

```json
{
  "words": [
    "YourProjectName",
    "YourTechStack",
    "YourTerminology"
  ]
}
```

### 2. Customize Required Documents

Edit `.github/scripts/validate-docs.py` to change required docs:

```python
REQUIRED_DOCS = [
    'README.md',
    'API.md',          # Remove if not needed
    'CONTRIBUTING.md',
    'CHANGELOG.md'
]
```

### 3. Configure Workflows

Edit `.github/workflows/documentation-review.yml`:

```yaml
# Change schedule (default: Monday 9 AM UTC)
schedule:
  - cron: '0 9 * * 1'  # Modify as needed

# Change paths to monitor
paths:
  - '**.md'
  - 'your-docs-path/**'
```

## 📝 Usage

### Automatic Operation

Once installed, the system runs automatically:
- **Weekly reviews**: Creates issues if problems found
- **On code changes**: Generates documentation
- **On PRs**: Validates and comments

### Manual Commands

```bash
# Validate documentation
python .github/scripts/validate-docs.py

# Check links
python .github/scripts/check-links.py

# Check dates
python .github/scripts/check-dates.py

# Generate API docs
python .github/scripts/generate-api-docs.py

# Generate component docs
python .github/scripts/generate-component-docs.py

# Update changelog
python .github/scripts/update-changelog.py
```

## 🎯 Adapting to Your Project

### For Python Projects

The kit works out-of-the-box for Python projects using FastAPI.

**Customize generation:**
- Edit `generate-api-docs.py` for other frameworks (Flask, Django, etc.)
- Update `generate-component-docs.py` for your class structure

### For JavaScript/TypeScript Projects

**Update generation scripts:**

```python
# In generate-component-docs.py
# Add TypeScript parsing
def extract_typescript_component_info(file_path: Path):
    # Parse .ts/.tsx files
    # Extract JSDoc comments
    # Return component info
```

### For Other Languages

**Adapt scripts for your language:**
- Copy script templates from `scripts/`
- Modify parsing logic for your language
- Update file patterns (`.py` → `.go`, `.rs`, etc.)

### For Non-Code Documentation

**Disable code generation:**

```yaml
# In .github/workflows/auto-generate-docs.yml
# Comment out or remove:
# - generate-api-docs.py
# - generate-component-docs.py
```

Keep validation and link checking active.

## 📚 Documentation

After installation, comprehensive guides are available:

- `.github/README.md` - Complete system documentation
- `.github/QUICK_REFERENCE.md` - Quick command reference
- `.github/ARCHITECTURE.md` - System architecture diagrams

## 🔧 Customization Examples

### Example 1: Add Custom Validation

```python
# In .github/scripts/validate-docs.py

def check_custom_requirement(file_path: Path) -> List[str]:
    """Add your custom validation."""
    issues = []
    # Your validation logic here
    return issues
```

### Example 2: Change Issue Labels

```yaml
# In .github/workflows/documentation-review.yml

- name: Create issue for documentation updates
  with:
    labels: ['docs', 'automated', 'your-label']  # Customize
```

### Example 3: Different PR Branch

```yaml
# In .github/workflows/auto-generate-docs.yml

- name: Create Pull Request
  with:
    branch: auto-docs/update  # Change branch name
```

## 🚀 Advanced Features

### Multi-Repository Setup

Use this kit across multiple repositories:

```bash
# Setup script for all repos
for repo in repo1 repo2 repo3; do
  cd $repo
  /path/to/doc-automation-kit/install.sh
  cd ..
done
```

### Custom Workflows

Create additional workflows based on templates:

```yaml
# .github/workflows/custom-doc-workflow.yml
name: Custom Documentation Task

on:
  workflow_dispatch:  # Manual trigger

jobs:
  custom-task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python .github/scripts/your-custom-script.py
```

## 🐛 Troubleshooting

### Scripts Not Executable

```bash
chmod +x .github/scripts/*.py
```

### Python Dependencies Missing

```bash
pip install pyyaml requests markdown beautifulsoup4
```

### Workflows Not Running

1. Check GitHub Actions are enabled
2. Verify workflow files are in `.github/workflows/`
3. Check for syntax errors: `yamllint .github/workflows/*.yml`

### Validation Failing

```bash
# Run locally to debug
python .github/scripts/validate-docs.py
```

## 📊 What Gets Automated

| Task | Frequency | Action |
|------|-----------|--------|
| Validation | Weekly + on push | Creates issues/comments |
| Link checking | Weekly + on push | Reports broken links |
| Date checking | Weekly | Flags outdated dates |
| API doc generation | On code changes | Creates PR |
| Component docs | On code changes | Creates PR |
| CHANGELOG update | On code changes | Creates PR |

## 🎁 Bonus Features

### Pre-commit Hook (Optional)

```bash
# .git/hooks/pre-commit
#!/bin/bash
python .github/scripts/validate-docs.py
if [ $? -ne 0 ]; then
  echo "Documentation validation failed. Fix errors before committing."
  exit 1
fi
```

### CI/CD Integration

Add to existing CI/CD:

```yaml
# In your existing CI workflow
- name: Validate Documentation
  run: python .github/scripts/validate-docs.py
```

## 📦 Package Contents

```
doc-automation-kit/
├── README.md              # This file
├── install.sh             # Automatic installer
├── uninstall.sh           # Removal script
├── workflows/             # GitHub Actions workflows
├── scripts/               # Validation & generation scripts
├── config/                # Configuration files
├── docs/                  # Documentation templates
└── examples/              # Usage examples
```

## 🔄 Updates

To update the kit in your repository:

```bash
# Pull latest version
cd doc-automation-kit
git pull

# Re-run installer
./install.sh
```

## 🤝 Support

For issues or questions:
1. Check `.github/README.md` in your repository
2. Review `.github/QUICK_REFERENCE.md` for commands
3. Check GitHub Actions logs for errors

## 📄 License

This kit is provided as-is for use in any project.

## 🎯 Success Metrics

You'll know it's working when:
- ✅ Weekly issues appear for doc problems
- ✅ PRs created when code changes
- ✅ PR comments show validation results
- ✅ Broken links caught before merge
- ✅ Documentation stays current

---

**Version**: 1.0  
**Last Updated**: 2025-11-24  
**Tested With**: Python 3.11+, GitHub Actions
