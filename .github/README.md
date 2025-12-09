# GitHub Configuration Files

This directory contains GitHub-specific configuration files for the repository.

## Files Overview

### `settings.yml`
**Purpose:** Repository and branch protection configuration

This file defines the repository settings and branch protection rules that should be applied to the repository. It can be:
- Used with the [Probot Settings App](https://probot.github.io/apps/settings/) for automated configuration
- Used as a reference for manual configuration via GitHub's web interface
- Applied programmatically using the GitHub API

**Key sections:**
- `repository`: Repository metadata and default settings
- `branches`: Branch protection rules for the main branch

**Configured protection for `main` branch:**
- ✅ Require pull request reviews before merging
- ✅ Require linear history (clean git history)
- ✅ Require status checks to pass (operability, ops-check)
- ✅ Enforce for administrators
- ❌ Prevent force pushes
- ❌ No push restrictions (to avoid lockout)

### Workflows

#### `workflows/branch-protection-check.yml`
Validates the branch protection configuration in `settings.yml`:
- Checks YAML syntax
- Validates that required settings are configured
- Reports configuration summary
- Attempts to check current GitHub branch protection status

Runs on:
- Pull requests that modify `settings.yml`
- Manual workflow dispatch

#### `workflows/ops-check.yml`
**Modified to work with branch protection:**
- Changed from direct push to creating pull requests
- Uses `peter-evans/create-pull-request` action
- Automatically creates PRs for module status updates
- Compatible with branch protection rules

#### `workflows/operability.yml`
Tests repository operability and functionality.

### Instructions and Snippets

See `instructions/README.md` for documentation on Copilot instruction files.

## Setting Up Branch Protection

### Quick Start (Manual Configuration)

1. Go to **Repository Settings → Branches → Add rule**
2. Set branch name pattern: `main`
3. Configure settings per `settings.yml`
4. Save the rule

### Detailed Instructions

See [Documentation/BRANCH_PROTECTION.md](../Documentation/BRANCH_PROTECTION.md) for:
- Step-by-step setup instructions
- Configuration options explained
- Impact on existing workflows
- Troubleshooting guide
- Best practices

### Using Probot Settings App

1. Install [Probot Settings App](https://github.com/apps/settings) on your repository
2. The app will automatically read and apply `settings.yml`
3. Changes to `settings.yml` will trigger automatic updates
4. Settings become version-controlled and reproducible

### Using GitHub API

You can apply settings programmatically using the GitHub API:

```bash
# Get current branch protection
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/doronpers/sonotheia-enhanced/branches/main/protection

# Update branch protection (requires admin permissions)
curl -X PUT \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/doronpers/sonotheia-enhanced/branches/main/protection \
  -d @branch-protection-payload.json
```

## Validating Configuration

Run the validation workflow:

```bash
# Via GitHub CLI
gh workflow run branch-protection-check.yml

# Check status
gh run list --workflow=branch-protection-check.yml
```

Or trigger manually:
1. Go to **Actions** tab
2. Select **Validate Branch Protection** workflow
3. Click **Run workflow**

## Maintenance

When updating branch protection configuration:

1. **Update `settings.yml`**: Make changes to the configuration file
2. **Update documentation**: Update `Documentation/BRANCH_PROTECTION.md` if needed
3. **Validate**: Run the validation workflow to check syntax
4. **Test workflows**: Ensure CI/CD workflows work with the new rules
5. **Apply**: Either use Probot app or manually configure via GitHub UI

## References

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Branch Protection API](https://docs.github.com/en/rest/branches/branch-protection)
- [Probot Settings App](https://probot.github.io/apps/settings/)
- [Repository Settings Schema](https://github.com/probot/settings#usage)
