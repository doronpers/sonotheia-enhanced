# Configuration Guide

Complete guide to configuring the Documentation Automation Kit for your project.

## Table of Contents

1. [Spell Check Configuration](#spell-check-configuration)
2. [Markdown Linting](#markdown-linting)
3. [Required Documents](#required-documents)
4. [Workflow Schedules](#workflow-schedules)
5. [Validation Rules](#validation-rules)
6. [Generation Scripts](#generation-scripts)
7. [Issue Templates](#issue-templates)
8. [PR Templates](#pr-templates)

---

## Spell Check Configuration

**File**: `.github/cspell.json`

### Basic Configuration

```json
{
  "version": "0.2",
  "language": "en",
  "words": [
    "ProjectName",
    "TechStackItem",
    "CustomTerm"
  ],
  "ignoreWords": [],
  "ignorePaths": [
    "node_modules/**",
    "**/.venv/**",
    "**/dist/**"
  ]
}
```

### Add Project-Specific Terms

```json
{
  "words": [
    "YourCompanyName",
    "YourProductName",
    "FastAPI",
    "PostgreSQL",
    "Kubernetes",
    "microservices",
    "API",
    "CLI"
  ]
}
```

### Ignore Specific Paths

```json
{
  "ignorePaths": [
    "node_modules/**",
    "vendor/**",
    "*.lock",
    "package-lock.json",
    "CHANGELOG.md"  // Often has version numbers
  ]
}
```

### Case-Sensitive Terms

```json
{
  "caseSensitive": true,
  "words": [
    "iOS",  // Not ios
    "macOS", // Not macos
    "PostgreSQL" // Not postgresql
  ]
}
```

---

## Markdown Linting

**File**: `.markdownlint.json`

### Default Configuration

```json
{
  "default": true,
  "MD013": {
    "line_length": 120,
    "code_blocks": false,
    "tables": false
  },
  "MD033": false,  // Allow HTML
  "MD041": false   // Don't require first line to be h1
}
```

### Strict Configuration

```json
{
  "default": true,
  "MD001": true,   // Heading levels increment by one
  "MD003": {
    "style": "atx"  // Use # style headers
  },
  "MD004": {
    "style": "dash" // Use - for lists
  },
  "MD013": {
    "line_length": 80,  // Stricter limit
    "code_blocks": false
  }
}
```

### Relaxed Configuration

```json
{
  "default": false,  // Start with nothing
  "MD001": true,     // Only check heading levels
  "MD002": true,     // Only check first heading
  "MD013": false     // No line length limit
}
```

---

## Required Documents

**File**: `.github/scripts/validate-docs.py`

### Default Requirements

```python
REQUIRED_DOCS = [
    'README.md',
    'QUICKSTART.md',
    'API.md',
    'INTEGRATION.md',
    'CONTRIBUTING.md',
    'ROADMAP.md',
    'CHANGELOG.md'
]
```

### Minimal Requirements

```python
REQUIRED_DOCS = [
    'README.md',
    'CONTRIBUTING.md',
    'CHANGELOG.md'
]
```

### Enterprise Requirements

```python
REQUIRED_DOCS = [
    'README.md',
    'CONTRIBUTING.md',
    'CODE_OF_CONDUCT.md',
    'SECURITY.md',
    'LICENSE',
    'CHANGELOG.md',
    'SUPPORT.md'
]
```

### Required Sections by Document

```python
REQUIRED_SECTIONS = {
    'README.md': ['Installation', 'Usage', 'License'],
    'CONTRIBUTING.md': ['Getting Started', 'Code Standards'],
    'SECURITY.md': ['Reporting', 'Policy'],
}
```

---

## Workflow Schedules

**File**: `.github/workflows/documentation-review.yml`

### Weekly Schedule (Default)

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM UTC
```

### Different Days

```yaml
schedule:
  - cron: '0 9 * * 3'   # Wednesday
  - cron: '0 9 * * 5'   # Friday
```

### Multiple Times

```yaml
schedule:
  - cron: '0 9 * * 1'   # Monday morning
  - cron: '0 17 * * 5'  # Friday evening
```

### Monthly

```yaml
schedule:
  - cron: '0 9 1 * *'   # First day of month
```

### Disable Schedule (Manual Only)

```yaml
on:
  workflow_dispatch:  # Remove schedule entirely
```

---

## Validation Rules

### Custom Date Threshold

**File**: `.github/scripts/check-dates.py`

```python
def check_dates(file_path: Path) -> List:
    # Change from 90 days to 180 days
    if age_days > 180:  # More lenient
        issues.append(...)
```

### Custom Link Timeout

**File**: `.github/scripts/check-links.py`

```python
def check_link(url: str, timeout: int = 30):  # Increase from 10
    # More patient with slow sites
```

### Skip Specific Links

```python
SKIP_DOMAINS = [
    'internal.company.com',
    'localhost',
    'example.com'
]

def check_link(url: str):
    for domain in SKIP_DOMAINS:
        if domain in url:
            return url, True, "Skipped (internal)"
```

---

## Generation Scripts

### Customize API Documentation

**File**: `.github/scripts/generate-api-docs.py`

#### For Django

```python
def extract_route_info(file_path: Path):
    # Look for Django URL patterns
    patterns = re.findall(r"path\('(.+?)',\s+(\w+)", content)
    for path, view in patterns:
        routes.append({
            'method': 'GET/POST',
            'path': f'/{path}',
            'function': view
        })
```

#### For Express.js

```python
def extract_express_routes(file_path: Path):
    # Parse JavaScript
    patterns = re.findall(r"router\.(get|post|put|delete)\('(.+?)',", content)
```

### Customize Component Documentation

**File**: `.github/scripts/generate-component-docs.py`

#### For Vue Components

```python
def extract_vue_component_info(file_path: Path):
    # Parse .vue files
    # Extract props from <script> section
    # Extract template documentation
```

---

## Issue Templates

Create custom templates for automated issues:

**File**: `.github/ISSUE_TEMPLATE/documentation_review.md`

```markdown
---
name: Documentation Review
about: Automated documentation review findings
labels: documentation, automated
---

## Documentation Review Report

**Date**: {{ date }}
**Triggered by**: Automated weekly review

### Issues Found

{{ issues_list }}

### Recommendations

{{ recommendations }}

### Action Required

Please review and address the issues above within 7 days.

---
*This issue was created automatically by the documentation automation system.*
```

---

## PR Templates

Customize PR templates for generated documentation:

**File**: `.github/workflows/auto-generate-docs.yml`

```yaml
- name: Create Pull Request
  with:
    title: '📚 [Auto] Update Documentation - {{ date }}'
    body: |
      ## Automated Documentation Update
      
      This PR contains automatically generated documentation.
      
      **Changes:**
      - Updated API reference from code
      - Updated component documentation
      - Updated CHANGELOG from commits
      
      **Review Checklist:**
      - [ ] API endpoints are correctly documented
      - [ ] Component props are accurate
      - [ ] CHANGELOG entries are relevant
      - [ ] No sensitive information exposed
      
      **Auto-generated by**: documentation-automation-system
      **Workflow run**: ${{ github.run_id }}
    labels: documentation, automated, needs-review
    assignees: your-team-lead
    reviewers: your-reviewer
```

---

## Advanced Configurations

### Organization-Wide Defaults

Create a template repository with pre-configured kit:

1. Create `org-doc-automation-template` repo
2. Install and configure the kit
3. Set as template repository
4. New repos can use it as template

### Environment-Specific Configuration

```yaml
# .github/workflows/documentation-review.yml
env:
  VALIDATION_LEVEL: ${{ github.ref == 'refs/heads/main' && 'strict' || 'lenient' }}
```

Then in scripts:

```python
import os

validation_level = os.getenv('VALIDATION_LEVEL', 'lenient')

if validation_level == 'strict':
    # More stringent checks
    max_age_days = 30
else:
    # Relaxed checks
    max_age_days = 90
```

### Multi-Language Support

```json
// .github/cspell.json
{
  "language": "en,es,fr",  // Multiple languages
  "dictionaries": [
    "en",
    "technical-terms",
    "company-terms"
  ]
}
```

---

## Testing Configuration

### Test Locally Before Committing

```bash
# Test spell check
npx cspell "**/*.md"

# Test markdown lint
npx markdownlint-cli2 "**/*.md"

# Test validation script
python .github/scripts/validate-docs.py

# Test link checker
python .github/scripts/check-links.py
```

### Dry Run Mode

Add to scripts:

```python
import sys

DRY_RUN = '--dry-run' in sys.argv

if DRY_RUN:
    print("DRY RUN MODE: No changes will be made")
```

---

## Configuration Examples by Project Type

### Static Site (Hugo/Jekyll)

```python
# validate-docs.py
REQUIRED_DOCS = ['README.md', 'content/']
IGNORE_PATHS = ['public/', 'resources/']
```

### Mobile App Documentation

```python
REQUIRED_DOCS = [
    'README.md',
    'docs/API.md',
    'docs/ARCHITECTURE.md',
    'docs/DEPLOYMENT.md'
]
```

### Library/Package

```python
REQUIRED_DOCS = [
    'README.md',
    'API.md',
    'CHANGELOG.md',
    'CONTRIBUTING.md',
    'examples/README.md'
]
```

---

## Tips

1. **Start Conservative**: Use relaxed rules initially
2. **Iterate**: Tighten rules based on team feedback
3. **Document Changes**: Keep configuration notes
4. **Version Control**: Track configuration changes in git
5. **Team Input**: Get feedback before strict enforcement

---

**Last Updated**: 2025-11-24
