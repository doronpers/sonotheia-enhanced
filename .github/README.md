# Automated Documentation System

This directory contains automated tools for maintaining and generating documentation.

## 🤖 Automated Workflows

### 1. Documentation Review (`documentation-review.yml`)

**Runs:** Weekly (Monday 9 AM UTC), on push to docs, on PRs modifying docs

**What it does:**
- ✓ Validates required documents exist
- ✓ Checks for broken internal links
- ✓ Checks external links (with retries)
- ✓ Detects outdated dates (>90 days old)
- ✓ Verifies documentation completeness
- ✓ Runs spell checking
- ✓ Lints markdown files
- ✓ Creates GitHub issue if problems found (weekly run)
- ✓ Comments on PRs with review results

### 2. Auto-Generate Documentation (`auto-generate-docs.yml`)

**Runs:** On code changes (backend/frontend), manual trigger

**What it does:**
- 🔧 Generates API documentation from FastAPI routes
- 🧩 Generates component documentation from docstrings
- 📝 Updates CHANGELOG.md from recent commits
- 🔄 Creates pull requests with generated docs
- ✅ Allows review before merging

## 📁 Scripts

### Validation Scripts

#### `validate-docs.py`
Validates documentation structure and completeness.

**Usage:**
```bash
python .github/scripts/validate-docs.py
```

**Checks:**
- Required documents present (README, API, CONTRIBUTING, etc.)
- Required sections in each document
- Broken internal links
- Valid markdown structure

#### `check-links.py`
Checks all external links in documentation.

**Usage:**
```bash
python .github/scripts/check-links.py
```

**Features:**
- Concurrent link checking (fast)
- Retries for transient failures
- Skips localhost URLs
- Reports broken links with locations

#### `check-dates.py`
Finds potentially outdated dates in documentation.

**Usage:**
```bash
python .github/scripts/check-dates.py
```

**Detects:**
- Dates older than 90 days
- "Last Updated" fields
- Version dates
- Quarterly year references

#### `check-completeness.py`
Verifies documentation completeness.

**Usage:**
```bash
python .github/scripts/check-completeness.py
```

**Checks:**
- Component README files
- API endpoint documentation
- Configuration documentation

### Generation Scripts

#### `generate-api-docs.py`
Auto-generates API documentation from code.

**Usage:**
```bash
python .github/scripts/generate-api-docs.py
```

**Generates:**
- `docs/api-reference.md` from FastAPI routes
- Endpoint methods, paths, and descriptions
- Parameter documentation

#### `generate-component-docs.py`
Auto-generates component documentation.

**Usage:**
```bash
python .github/scripts/generate-component-docs.py
```

**Generates:**
- `docs/components.md` from React components
- Python class documentation
- Props and parameters

#### `update-changelog.py`
Updates CHANGELOG.md from git commits.

**Usage:**
```bash
python .github/scripts/update-changelog.py
```

**Generates:**
- Categorized changelog entries (Added, Changed, Fixed, etc.)
- Includes commit hashes
- Based on last 7 days of commits

#### `generate-report.py`
Generates documentation review report.

**Usage:**
```bash
python .github/scripts/generate-report.py
```

## 🚀 Quick Start

### Run All Validations Locally

```bash
# Validate documentation structure
python .github/scripts/validate-docs.py

# Check for broken links
python .github/scripts/check-links.py

# Check for outdated dates
python .github/scripts/check-dates.py

# Check completeness
python .github/scripts/check-completeness.py
```

### Generate Documentation Locally

```bash
# Generate API docs
python .github/scripts/generate-api-docs.py

# Generate component docs
python .github/scripts/generate-component-docs.py

# Update changelog
python .github/scripts/update-changelog.py
```

### Trigger Workflows Manually

1. Go to **Actions** tab in GitHub
2. Select workflow (Documentation Review or Auto-Generate Documentation)
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## 📅 Schedule

| Workflow | Frequency | Purpose |
|----------|-----------|---------|
| Documentation Review | Weekly (Mon 9 AM UTC) | Detect issues proactively |
| Documentation Review | On push (docs) | Validate changes immediately |
| Documentation Review | On PR | Review before merge |
| Auto-Generate Docs | On code changes | Keep docs in sync with code |
| Auto-Generate Docs | Manual | Generate on demand |

## 🔧 Configuration

### Spell Check Dictionary

Edit `.github/cspell.json` to add project-specific words:

```json
{
  "words": [
    "Sonotheia",
    "deepfake",
    "YourNewTerm"
  ]
}
```

### Markdown Linting Rules

Edit `.markdownlint.json` to customize linting rules:

```json
{
  "MD013": {
    "line_length": 120
  }
}
```

## 📊 Outputs

### GitHub Issues

Weekly documentation reviews create issues with:
- Summary of validation results
- List of problems found
- Recommendations for fixes
- Labels: `documentation`, `automated-review`

### Pull Requests

Auto-generation creates PRs with:
- Generated documentation updates
- Clear description of changes
- Labels: `documentation`, `automated`
- Requires review before merge

### Artifacts

Workflow runs upload artifacts:
- `documentation-review-report` - Full review report
- Available for 90 days

## 🎯 Best Practices

### For Documentation Writers

1. **Write Good Docstrings**: Auto-generation relies on them
   ```python
   def my_function(param: str) -> dict:
       """
       Brief description of function.
       
       Args:
           param: Description of parameter
       
       Returns:
           Description of return value
       """
   ```

2. **Keep Dates Current**: Update "Last Updated" fields regularly

3. **Test Links**: Run `check-links.py` before committing

4. **Follow Structure**: Ensure required sections are present

### For Code Changes

1. **Update Docstrings**: When changing functions/classes

2. **Document New Endpoints**: Add descriptions to FastAPI routes

3. **Review Auto-Generated Docs**: Check PRs from automation

4. **Update CHANGELOG**: Manually review auto-generated entries

### For Maintenance

1. **Weekly Review**: Check automated issues

2. **Quarterly Cleanup**: Update outdated dates in ROADMAP

3. **Release Process**: Update CHANGELOG version numbers

4. **Archive Old Docs**: Move obsolete docs to archive/

## 🆘 Troubleshooting

### Validation Failing

**Problem:** Required section not found
**Solution:** Check section heading matches expected format (case-insensitive)

**Problem:** Broken link detected
**Solution:** Fix the link path or update the target document

**Problem:** External link failing
**Solution:** Check if site is down, update URL, or add to skip list

### Auto-Generation Issues

**Problem:** No endpoints found
**Solution:** Ensure FastAPI decorators are used correctly

**Problem:** No components documented
**Solution:** Add docstrings to components and classes

**Problem:** CHANGELOG not updating
**Solution:** Check commit message format, ensure git history available

### Workflow Not Running

**Problem:** Scheduled workflow didn't run
**Solution:** Check GitHub Actions are enabled for repository

**Problem:** Manual trigger not available
**Solution:** Ensure you have write access to repository

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Markdown Guide](https://www.markdownguide.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 Contributing

To improve the automation system:

1. Test changes locally first
2. Update this README if adding new scripts
3. Add examples for new features
4. Update workflow files carefully (test in fork)

---

**Last Updated:** 2025-11-24  
**Maintained By:** @doronpers
