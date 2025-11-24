# Documentation Automation - Quick Reference

## 🎯 One-Line Commands

### Validate All Documentation
```bash
python .github/scripts/validate-docs.py && \
python .github/scripts/check-links.py && \
python .github/scripts/check-dates.py && \
python .github/scripts/check-completeness.py
```

### Generate All Documentation
```bash
python .github/scripts/generate-api-docs.py && \
python .github/scripts/generate-component-docs.py && \
python .github/scripts/update-changelog.py
```

### Full Documentation Maintenance
```bash
# Validate → Generate → Validate again
python .github/scripts/validate-docs.py && \
python .github/scripts/generate-api-docs.py && \
python .github/scripts/generate-component-docs.py && \
python .github/scripts/validate-docs.py
```

## 📋 Common Tasks

### Before Committing Documentation Changes
```bash
# Quick validation
python .github/scripts/validate-docs.py
python .github/scripts/check-links.py
```

### Before Releasing New Version
```bash
# Update changelog
python .github/scripts/update-changelog.py

# Generate all docs
python .github/scripts/generate-api-docs.py
python .github/scripts/generate-component-docs.py

# Validate everything
python .github/scripts/validate-docs.py
```

### Weekly Maintenance
```bash
# Check for outdated content
python .github/scripts/check-dates.py

# Verify completeness
python .github/scripts/check-completeness.py

# Update ROADMAP.md dates if needed
```

### After Adding New API Endpoint
```bash
# Regenerate API docs
python .github/scripts/generate-api-docs.py

# Review generated docs
cat docs/api-reference.md
```

### After Adding New Component
```bash
# Regenerate component docs
python .github/scripts/generate-component-docs.py

# Review generated docs
cat docs/components.md
```

## 🤖 Automated Actions

| Event | Action | Result |
|-------|--------|--------|
| **Every Monday 9 AM** | Full doc review | GitHub issue if problems |
| **Push to main (code)** | Generate docs | PR with updates |
| **Push to main (docs)** | Validate docs | Check results in Actions |
| **Open PR (docs)** | Review docs | Comment on PR |

## 📊 Interpreting Results

### Exit Codes
- `0` = Success, no issues
- `1` = Issues found, needs attention

### Validation Output
```
✅ All validation checks passed!
```
**Action:** None needed

```
❌ ERRORS (3):
  - Missing required documents: CONTRIBUTING.md
  - README.md: Broken link to invalid.md file
```
**Action:** Fix errors listed

```
⚠️  WARNINGS (2):
  - API.md: Missing sections: Examples
```
**Action:** Consider addressing warnings

### Link Checker Output
```
✓ All 15 links are working!
```
**Action:** None needed

```
❌ Found 2 broken links:
  https://example.com/dead-link
    Error: HTTP 404
    Found in: README.md
```
**Action:** Fix or remove broken links

### Date Checker Output
```
⚠️  Found potentially outdated dates:
  ROADMAP.md:
    Line 5: Last Updated - Date 2024-05-15 is 193 days old
```
**Action:** Update outdated dates

## 🔍 Debugging

### Script Fails to Run
```bash
# Check Python version (need 3.11+)
python --version

# Install dependencies if needed
pip install pyyaml requests markdown beautifulsoup4
```

### No API Routes Found
```bash
# Verify FastAPI files exist
ls backend/api/*.py

# Check decorator format
grep -r "@router\." backend/api/
```

### Links Always Fail
```bash
# Test network connectivity
curl -I https://github.com

# Check proxy settings
echo $HTTP_PROXY

# Increase timeout in script if needed
```

### CHANGELOG Not Updating
```bash
# Check git history
git log --oneline -10

# Verify recent commits
python -c "import subprocess; print(subprocess.run(['git', 'log', '--since=7.days.ago', '--oneline'], capture_output=True, text=True).stdout)"
```

## 📝 Tips

### Writing Good Docstrings

**Python Functions:**
```python
def authenticate(user_id: str, factors: dict) -> dict:
    """
    Authenticate user with multi-factor authentication.
    
    Args:
        user_id: Unique user identifier
        factors: Dictionary of authentication factors
    
    Returns:
        Authentication result with decision and confidence
    """
```

**React Components:**
```jsx
/**
 * WaveformDashboard displays audio waveform with analysis results.
 * 
 * Shows interactive waveform visualization using Plotly.js with
 * segment overlays indicating genuine vs synthetic regions.
 */
function WaveformDashboard({ waveformData, segments }) {
```

### Linking Between Documents

**Relative links:**
```markdown
See [API Documentation](../API.md) for details.
See [Contributing Guide](../CONTRIBUTING.md) for code standards.
```

**Anchor links:**
```markdown
Jump to [Architecture section](#architecture).
```

### Updating Dates

**In ROADMAP.md:**
```markdown
**Last Updated**: 2025-11-24  <!-- Update quarterly -->
```

**In CHANGELOG.md:**
```markdown
## [2.1.0] - 2025-11-24  <!-- Update with each release -->
```

## 🎓 Learning Resources

- **GitHub Actions**: https://docs.github.com/en/actions
- **Python AST**: https://docs.python.org/3/library/ast.html
- **Markdown**: https://www.markdownguide.org/
- **FastAPI**: https://fastapi.tiangolo.com/

## 🆘 Getting Help

1. Check `.github/README.md` for detailed documentation
2. Review workflow logs in GitHub Actions
3. Test scripts locally with verbose output
4. Create GitHub issue with `documentation` label

---

**Quick Help:** For most issues, run validation locally before committing:
```bash
python .github/scripts/validate-docs.py
```
