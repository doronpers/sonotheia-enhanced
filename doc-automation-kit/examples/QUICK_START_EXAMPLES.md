# Quick Start Examples

## Example 1: Install in New Repository

```bash
# 1. Clone your repository
git clone https://github.com/yourusername/your-repo.git
cd your-repo

# 2. Copy the kit
cp -r /path/to/doc-automation-kit .

# 3. Run installer
./doc-automation-kit/install.sh

# 4. Customize spell check
nano .github/cspell.json
# Add your project-specific terms

# 5. Test locally
python .github/scripts/validate-docs.py

# 6. Commit and push
git add .github/ .markdownlint.json
git commit -m "Add documentation automation system"
git push
```

Done! The system is now active.

## Example 2: Python API Project

For a Python project with FastAPI:

```bash
# Install kit (works out of the box)
./doc-automation-kit/install.sh

# Your API endpoints will be auto-documented
# Just ensure you have docstrings:

@router.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """
    Create a new user account.
    
    Args:
        user: User creation data
        
    Returns:
        Created user information
    """
    pass
```

The system will automatically generate `docs/api-reference.md` from your routes.

## Example 3: React/JavaScript Project

For React/Next.js projects:

```bash
# Install kit
./doc-automation-kit/install.sh

# Customize component documentation
nano .github/scripts/generate-component-docs.py
```

Update the script to parse your component structure:

```python
# Add JSDoc/TypeScript support
def extract_react_component_info(file_path: Path):
    # Parse .jsx/.tsx files
    # Extract component props
    # Return documentation
```

## Example 4: Documentation-Only Repository

For repos with just documentation (no code):

```bash
# Install kit
./doc-automation-kit/install.sh

# Disable code generation workflows
rm .github/workflows/auto-generate-docs.yml

# Keep validation active
python .github/scripts/validate-docs.py
```

Now you have automated validation without code generation.

## Example 5: Multi-Repository Setup

Automate installation across multiple repos:

```bash
#!/bin/bash
# install-all.sh

REPOS=(
    "/path/to/repo1"
    "/path/to/repo2"
    "/path/to/repo3"
)

KIT_PATH="/path/to/doc-automation-kit"

for repo in "${REPOS[@]}"; do
    echo "Installing in $repo..."
    cd "$repo"
    
    # Copy kit
    cp -r "$KIT_PATH" .
    
    # Run installer
    ./doc-automation-kit/install.sh
    
    # Commit
    git add .github/ .markdownlint.json
    git commit -m "Add documentation automation"
    git push
    
    echo "✓ Done: $repo"
    echo ""
done
```

## Example 6: Customize for Your Organization

Create an organization-specific version:

```bash
# 1. Fork/copy the kit
cp -r doc-automation-kit my-org-doc-kit

# 2. Customize spell check for your org
nano my-org-doc-kit/config/cspell.json
# Add common terms: product names, tech stack, etc.

# 3. Customize required docs
nano my-org-doc-kit/scripts/validate-docs.py
REQUIRED_DOCS = [
    'README.md',
    'SECURITY.md',        # Add org requirements
    'CODE_OF_CONDUCT.md', # Add org requirements
    'CONTRIBUTING.md'
]

# 4. Update workflows with org defaults
nano my-org-doc-kit/workflows/documentation-review.yml
# Set org-wide labels, reviewers, etc.

# 5. Distribute to teams
# Teams can now use: ./my-org-doc-kit/install.sh
```

## Example 7: Custom Validation Rules

Add organization-specific validation:

```python
# In .github/scripts/validate-docs.py

def check_org_standards(file_path: Path) -> List[str]:
    """Check organization documentation standards."""
    issues = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Require copyright notice
    if 'Copyright' not in content:
        issues.append("Missing copyright notice")
    
    # Require license section
    if '## License' not in content and file_path.name == 'README.md':
        issues.append("README missing License section")
    
    # Check for proprietary warnings
    if 'proprietary' in content.lower():
        if 'CONFIDENTIAL' not in content:
            issues.append("Proprietary content not marked CONFIDENTIAL")
    
    return issues
```

Then call it from the main validation function.

## Example 8: Integration with Existing CI/CD

Add to your existing GitHub Actions workflow:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    # ... your existing tests
  
  docs:
    name: Validate Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pyyaml requests markdown beautifulsoup4
      - name: Validate docs
        run: python .github/scripts/validate-docs.py
      - name: Check links
        run: python .github/scripts/check-links.py
```

## Example 9: Pre-commit Hook

Validate docs before every commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "🔍 Validating documentation..."

python .github/scripts/validate-docs.py
RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "❌ Documentation validation failed!"
    echo "Fix the issues above or use 'git commit --no-verify' to skip."
    exit 1
fi

echo "✅ Documentation validation passed"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Example 10: Language-Specific Customization

### Go Projects

```python
# Update generate-api-docs.py for Go
def extract_go_route_info(file_path: Path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse Go HTTP handlers
    # Look for patterns like: r.HandleFunc("/api/...", handler)
    # Extract godoc comments
    return routes
```

### Rust Projects

```python
# Update generate-api-docs.py for Rust
def extract_rust_route_info(file_path: Path):
    # Parse Rust actix-web or rocket routes
    # Extract doc comments (///)
    return routes
```

## Tips for Success

1. **Start Simple**: Install with defaults, customize later
2. **Test Locally**: Always run scripts locally before pushing
3. **Gradual Rollout**: Install in one repo, refine, then expand
4. **Team Training**: Share documentation links with team
5. **Monitor Issues**: Check weekly automation issues
6. **Iterate**: Adjust based on team feedback

## Common Customizations

### Change Schedule
```yaml
# Weekly on different day
cron: '0 9 * * 3'  # Wednesday

# More frequent
cron: '0 9 * * 1,4'  # Monday and Thursday
```

### Different Issue Labels
```yaml
labels: ['documentation', 'automated', 'priority-low']
```

### Custom Notifications
```yaml
# Add Slack notification
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

## Troubleshooting

### Installation fails
```bash
# Check you're in repo root
pwd
ls .git

# Check permissions
chmod +x doc-automation-kit/install.sh
```

### Scripts don't run
```bash
# Make them executable
chmod +x .github/scripts/*.py

# Check Python version
python3 --version  # Need 3.11+
```

### Workflows don't trigger
```bash
# Check workflow files are valid
yamllint .github/workflows/*.yml

# Check GitHub Actions are enabled
# Repository Settings → Actions → General
```
