# Branch Protection Configuration Guide

## Overview

This document provides instructions for configuring branch protection rules for the `main` branch of the sonotheia-enhanced repository. These rules help maintain code quality, prevent accidental changes, and enforce a proper review process.

## Quick Reference

A configuration file is available at `.github/settings.yml` that can be:
- Used with the [Probot Settings App](https://probot.github.io/apps/settings/) for automated configuration
- Used as a reference for manual configuration via GitHub's web interface
- Applied programmatically using the GitHub API

## Manual Configuration via GitHub Web Interface

### Step-by-Step Instructions

1. **Navigate to Branch Protection Settings**
   - Go to your repository: https://github.com/doronpers/sonotheia-enhanced
   - Click on **Settings** (top menu)
   - In the left sidebar, click on **Branches**
   - Under "Branch protection rules", click **Add rule** (or **Add branch protection rule**)

2. **Configure Branch Name Pattern**
   - In the "Branch name pattern" field, enter: `main`
   - This will apply the rules specifically to the main branch

3. **Enable Required Settings**

   ✅ **Require a pull request before merging**
   - Check this box to block direct pushes to main
   - This ensures all changes go through pull requests
   - Set "Required number of approvals before merging" to at least 1
   - Optional: Check "Dismiss stale pull request approvals when new commits are pushed"

   ✅ **Require status checks to pass before merging**
   - Check this box to ensure CI/CD checks pass
   - Search and select required status checks:
     - `operability` (from operability.yml workflow)
     - `ops-check` (from ops-check.yml workflow)
   - Optional: Check "Require branches to be up to date before merging"

   ✅ **Require linear history** (Optional but Recommended)
   - Check this box to prevent merge commits
   - Enforces a clean, linear git history
   - Requires using rebase or squash merging

   ✅ **Do not allow bypassing the above settings**
   - Check "Do not allow bypassing the above settings"
   - Or check "Require approval of the most recent reviewable push"
   
   ✅ **Require conversation resolution before merging**
   - Check this box to ensure all review comments are addressed
   
4. **Disable Force Pushes**
   
   ❌ **Allow force pushes**
   - Keep this UNCHECKED to prevent force pushes
   - Protects against rewriting history on the main branch

5. **Configure Admin Enforcement** (Optional but Recommended)
   
   ✅ **Include administrators**
   - Check this box to enforce rules even for repository administrators
   - Ensures consistent process for all contributors
   - You can still merge with required approvals

6. **Restrictions** (Use with Caution)
   
   ⚠️ **Restrict who can push to matching branches**
   - DO NOT check this unless you want to explicitly limit who can push
   - If enabled, you must specify users/teams who can push
   - This is different from requiring PRs (which is already configured above)
   - **Warning**: Enabling this without proper configuration can lock you out!

7. **Save Changes**
   - Click **Create** (or **Save changes** if editing)
   - The rules are now active for the main branch

## Impact on Existing Workflows

### ops-check.yml Workflow

The `ops-check.yml` workflow currently pushes changes directly to the main branch (module status updates). With branch protection enabled, this workflow will need modifications:

**Option 1: Use GitHub App Token (Recommended)**
```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}  # Use PAT or GitHub App token with bypass permissions
```

**Option 2: Create Pull Requests Instead**
Modify the workflow to create a pull request instead of pushing directly:
```yaml
- name: Create Pull Request
  uses: peter-evans/create-pull-request@v5
  with:
    commit-message: "chore: update module status tables"
    branch: auto-update-module-status
    title: "chore: update module status tables"
    body: "Automated update of module status tables"
```

**Option 3: Use [skip ci] and Auto-merge**
Use GitHub's auto-merge feature with the `[skip ci]` tag already in place.

### Required Status Checks

The configuration requires these checks to pass:
- `operability` - Tests from operability.yml
- `ops-check` - Module status checks from ops-check.yml

If these checks fail, merging will be blocked until they pass.

## Using the Probot Settings App

For automated configuration management:

1. Install the [Probot Settings App](https://probot.github.io/apps/settings/) on your repository
2. The app will automatically apply settings from `.github/settings.yml`
3. Any changes to the YAML file will trigger an update to repository settings
4. This ensures settings are version-controlled and reproducible

## Verification

After configuring branch protection, verify the setup:

1. Try to push directly to main (should be blocked):
   ```bash
   git checkout main
   echo "test" >> test.txt
   git add test.txt
   git commit -m "test direct push"
   git push origin main  # Should fail with protection error
   ```

2. Verify via GitHub API:
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/repos/doronpers/sonotheia-enhanced/branches/main/protection
   ```

3. Check in GitHub UI:
   - Go to Settings → Branches
   - You should see the protection rules listed under the main branch

## Troubleshooting

### "Push declined due to repository rule violations"

This means branch protection is working! Create a pull request instead:
```bash
git checkout -b feature/my-change
git push origin feature/my-change
# Then create a PR in GitHub UI
```

### Workflow fails to push changes

If GitHub Actions workflows need to push to main:
1. Use a Personal Access Token (PAT) with appropriate permissions
2. Store it as a repository secret
3. Use it in the workflow checkout step

### Accidentally locked out

If you configured "Restrict who can push" and locked yourself out:
1. Go to Settings → Branches → Edit rule
2. Add your username to the allowed users list
3. Or remove the restriction entirely

## Best Practices

1. **Start with minimal protection**: Enable PR requirement and linear history
2. **Add status checks gradually**: Add required checks as you build them
3. **Test the workflow**: Verify CI/CD works before enforcing
4. **Document exceptions**: If you need to bypass rules, document why
5. **Review regularly**: Revisit protection rules as the project evolves

## Configuration Summary

Based on the problem statement, the recommended configuration is:

| Setting | Value | Why |
|---------|-------|-----|
| Branch name pattern | `main` | Protect the main branch |
| Require pull request | ✅ Enabled | Blocks direct pushes, enforces review |
| Require linear history | ✅ Enabled (optional) | Clean git history |
| Restrict who can push | ❌ Disabled | Avoid lockout; PR requirement is sufficient |
| Allow force pushes | ❌ Disabled | Prevents history rewriting |
| Enforce for admins | ✅ Enabled (optional) | Consistent process for all |

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Branch Protection API](https://docs.github.com/en/rest/branches/branch-protection)
- [Probot Settings App](https://probot.github.io/apps/settings/)

## Questions or Issues?

If you encounter issues with branch protection:
1. Check the troubleshooting section above
2. Review GitHub's official documentation
3. Consider starting with less restrictive rules and adding more over time
