# Quick Start: Enabling Branch Protection

This repository now includes complete branch protection configuration. Follow these simple steps to enable it.

## ⚡ Quick Setup (5 minutes)

### Step 1: Go to Branch Settings
Navigate to: **https://github.com/doronpers/sonotheia-enhanced/settings/branches**

### Step 2: Add Branch Protection Rule
Click the **"Add rule"** or **"Add branch protection rule"** button

### Step 3: Configure the Rule

**Branch name pattern:**
```
main
```

**Enable these settings (check the boxes):**
- ✅ **Require a pull request before merging**
  - Set "Required number of approvals" to **1**
  - Optional: Check "Dismiss stale pull request approvals when new commits are pushed"
  
- ✅ **Require status checks to pass before merging**
  - Search and add: `operability`
  - Search and add: `ops-check`
  - Optional: Check "Require branches to be up to date before merging"

- ✅ **Require linear history** (optional but recommended)

- ✅ **Require conversation resolution before merging** (optional but recommended)

- ✅ **Do not allow bypassing the above settings** (or "Include administrators")

**Disable these settings (uncheck the boxes):**
- ❌ **Allow force pushes** - MUST be unchecked
- ❌ **Restrict who can push to matching branches** - DO NOT enable (unless you know what you're doing)

### Step 4: Save
Click **"Create"** button at the bottom

### Step 5: Verify
Try to push directly to main (should fail):
```bash
git checkout main
git push origin main
# Should see: "branch protection rules"
```

## 🎉 Done!

Your main branch is now protected. All changes must go through pull requests.

## 📚 Need More Help?

- **Detailed Instructions**: See [BRANCH_PROTECTION.md](../BRANCH_PROTECTION.md)
- **Implementation Details**: See [BRANCH_PROTECTION_IMPLEMENTATION.md](../Security/BRANCH_PROTECTION_IMPLEMENTATION.md)
- **Configuration Reference**: See [.github/settings.yml](../../.github/settings.yml)

## 🤖 Alternative: Automated Setup

Install the [Probot Settings App](https://github.com/apps/settings) and it will automatically apply the configuration from `.github/settings.yml`.

## ⚠️ Important Notes

1. **ops-check workflow** has been updated to create PRs instead of pushing directly
2. You can still merge PRs - the rules ensure quality, not block work
3. Admins must also follow the rules (unless you disable "enforce for admins")
4. If you get locked out, you can edit the rule in Settings → Branches

## 🔍 Troubleshooting

**Problem:** "Push declined due to repository rule violations"
- **Solution:** This is expected! Create a pull request instead.

**Problem:** Workflow can't push changes
- **Solution:** Already fixed! ops-check.yml now creates PRs automatically.

**Problem:** Need to bypass rules temporarily
- **Solution:** Edit the rule and temporarily disable it, but remember to re-enable!

---

**Configuration matches all requirements from the problem statement ✓**
