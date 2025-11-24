# How to Use This Kit in Other Repositories

## 🎯 Quick Start

This `doc-automation-kit` directory is a **portable, standalone package** that can be copied to any repository.

### Option 1: Direct Copy

```bash
# From this repository
cp -r doc-automation-kit /path/to/your-other-repo/

# Go to other repo
cd /path/to/your-other-repo

# Run installer
./doc-automation-kit/install.sh
```

### Option 2: Download as Archive

```bash
# Create distributable ZIP
cd /path/to/this/repo
zip -r doc-automation-kit.zip doc-automation-kit/

# Transfer to other repo
cp doc-automation-kit.zip /path/to/other-repo/
cd /path/to/other-repo/
unzip doc-automation-kit.zip

# Run installer
./doc-automation-kit/install.sh
```

### Option 3: Git Subtree (Advanced)

```bash
# In your other repository
git subtree add --prefix doc-automation-kit \
  https://github.com/yourusername/sonotheia-enhanced.git \
  copilot/consolidate-repo-documentation \
  --squash

# Run installer
./doc-automation-kit/install.sh
```

### Option 4: Git Clone (for development)

```bash
# Clone this repo
git clone https://github.com/yourusername/sonotheia-enhanced.git

# Copy just the kit
cp -r sonotheia-enhanced/doc-automation-kit /path/to/your-repo/

# Or symlink for testing
ln -s $(pwd)/sonotheia-enhanced/doc-automation-kit /path/to/your-repo/
```

## 📦 What You Get

- ✅ **2 GitHub Actions workflows** (automated review & generation)
- ✅ **8 Python scripts** (validation & doc generation)
- ✅ **2 configuration files** (spell check & markdown lint)
- ✅ **3 documentation guides** (system, quick ref, architecture)
- ✅ **2 example guides** (quick start & configuration)
- ✅ **Automatic installer** (one command setup)

## 🚀 After Installation

1. **Customize spell check**: Edit `.github/cspell.json`
2. **Test locally**: `python .github/scripts/validate-docs.py`
3. **Commit changes**: `git add .github/ && git commit -m "Add documentation automation"`
4. **Push**: `git push`

The system is now active and will:
- Run weekly documentation reviews
- Validate on every push and PR
- Generate documentation from code changes
- Create issues and PRs automatically

## 🔧 Customization

See these guides in the kit:
- `examples/QUICK_START_EXAMPLES.md` - 10+ usage examples
- `examples/CONFIGURATION_GUIDE.md` - Complete configuration reference

## 📚 Documentation

After installation, comprehensive documentation is available in your repo:
- `.github/README.md` - Complete system guide
- `.github/QUICK_REFERENCE.md` - Quick command reference
- `.github/ARCHITECTURE.md` - System architecture diagrams

## 🎁 Share with Team

### Create Organization Template

1. Create a new repo: `your-org/doc-automation-kit`
2. Copy this kit there
3. Customize for your organization
4. Teams can clone and use

### Create GitHub Release

```bash
# Tag this version
git tag -a doc-kit-v1.0 -m "Documentation Automation Kit v1.0"
git push origin doc-kit-v1.0

# Create release on GitHub with doc-automation-kit.zip attached
```

### Internal Distribution

```bash
# Create archive
tar -czf doc-automation-kit-v1.0.tar.gz doc-automation-kit/

# Share via:
# - Internal package repository
# - Shared drive
# - Wiki page
# - Confluence
```

## ✅ Verification

Check the kit is complete:

```bash
cd doc-automation-kit

# Should show 21 files
find . -type f | wc -l

# Check installer is executable
ls -la install.sh

# Check all scripts are executable
ls -la scripts/*.py
```

## 🔄 Update Process

To update repos with a new version of the kit:

```bash
# In each repo with the kit installed
cd your-repo

# Backup old kit
mv doc-automation-kit doc-automation-kit.old

# Copy new kit
cp -r /path/to/new/doc-automation-kit .

# Re-run installer (backs up existing files)
./doc-automation-kit/install.sh

# Remove old kit
rm -rf doc-automation-kit.old
```

## 🌟 Success Stories

After installing, you should see:
- ✅ Green check marks on PRs with valid docs
- ✅ Weekly issues if documentation needs attention
- ✅ Automated PRs when code changes
- ✅ Broken links caught before merge
- ✅ Team confidence in documentation quality

## 🆘 Troubleshooting

### "Permission denied" on install.sh

```bash
chmod +x doc-automation-kit/install.sh
```

### "Python not found"

```bash
# Install Python 3.11+
# Then re-run installer
```

### "Workflows not running"

```bash
# Check GitHub Actions are enabled
# Repository Settings → Actions → General → Allow all actions
```

### Need Help?

1. Check `doc-automation-kit/README.md`
2. Review `doc-automation-kit/examples/`
3. Test locally: `python .github/scripts/validate-docs.py`
4. Check GitHub Actions logs

## 💡 Pro Tips

1. **Start simple**: Install with defaults, customize later
2. **Test first**: Try in a test repo before production
3. **Team training**: Share documentation links
4. **Iterate**: Adjust based on feedback
5. **Monitor**: Check weekly automation issues

## 📊 Metrics

Track adoption across your organization:
- Number of repos using the kit
- Documentation quality improvements
- Time saved on manual reviews
- Issues caught before production

## 🎯 Next Steps

1. Copy kit to your repository
2. Run `./doc-automation-kit/install.sh`
3. Customize `.github/cspell.json`
4. Test: `python .github/scripts/validate-docs.py`
5. Commit and push
6. Enjoy automated documentation maintenance!

---

**Questions?** Check `doc-automation-kit/README.md` for complete documentation.

**Updates?** Re-run `install.sh` - it backs up existing files automatically.

**Removal?** Run `./doc-automation-kit/uninstall.sh`
