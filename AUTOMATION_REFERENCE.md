# GitHub Automation - Complete Reference

Your complete GitHub automation system for ML projects with separate codebase and dataset repositories.

---

## 📦 What You Have

### Scripts
- **`upload_to_github.py`** - Main upload script (400+ lines, production-ready)
- **`sync_dataset.py`** - Dataset management script (400+ lines)
- **`setup_github_automation.py`** - Interactive setup wizard (300+ lines)
- **`diagnose_github_automation.py`** - Diagnostic troubleshooting tool (300+ lines)

### Configuration
- **`.env.example`** - Configuration template (safe to commit)
- **`.env`** - Your actual credentials (DO NOT commit, auto-created)
- **`.gitignore`** - Auto-created with sensible defaults
- **`.gitattributes`** - Git LFS configuration

### GitHub Actions
- **`.github/workflows/auto-commit.yml`** - Auto-commit on schedule
- **`.github/workflows/dataset-check.yml`** - Dataset validation
- **`.github/workflows/cross-repo-sync.yml`** - Cross-repo synchronization

### Documentation
- **`GITHUB_AUTOMATION_GUIDE.md`** - Complete detailed guide
- **`QUICK_START_GITHUB.md`** - 5-minute setup
- **`AUTOMATION_REFERENCE.md`** - This file

---

## 🚀 Quick Start (Choose One)

### Option A: Fastest Setup (3 minutes)
```bash
python setup_github_automation.py
python upload_to_github.py --mode all
```

### Option B: Manual Setup
```bash
# 1. Copy template
cp .env.example .env

# 2. Edit with your credentials
# - GITHUB_TOKEN: from https://github.com/settings/tokens
# - Repo URLs: from your GitHub repos

# 3. Verify
python diagnose_github_automation.py

# 4. Upload
python upload_to_github.py --mode all
```

### Option C: Check-First Approach
```bash
python upload_to_github.py --check-only
# Review any warnings/errors

# When ready:
python upload_to_github.py --mode all
```

---

## 📋 File Structure After Setup

```
your-project/
├── .env                                    # ← DO NOT COMMIT (auto-created)
├── .env.example                            # ← Safe to commit (template)
├── .gitignore                              # ← Auto-created
├── .gitattributes                          # ← Git LFS config
│
├── .github/workflows/
│   ├── auto-commit.yml                     # Scheduled auto-commit
│   ├── dataset-check.yml                   # Dataset validation
│   └── cross-repo-sync.yml                 # Cross-repo sync
│
├── upload_to_github.py                     # Main upload script
├── sync_dataset.py                         # Dataset sync script
├── setup_github_automation.py              # Setup wizard
├── diagnose_github_automation.py           # Troubleshooting
├── requirements-automation.txt             # Dependencies
│
├── GITHUB_AUTOMATION_GUIDE.md              # Detailed guide
├── QUICK_START_GITHUB.md                   # Quick reference
├── AUTOMATION_REFERENCE.md                 # This file
│
└── data/                                   # Dataset directory
    ├── train.conll
    ├── test.conll
    └── ...
```

---

## 🎯 Common Tasks

### Upload Both Repos
```bash
python upload_to_github.py --mode all
```

### Upload Only Codebase
```bash
python upload_to_github.py --mode codebase
```

### Upload Only Dataset
```bash
python upload_to_github.py --mode dataset
```

### With Custom Message
```bash
python upload_to_github.py --mode all --msg "v1.0: Release notes"
```

### Clone Dataset
```bash
python sync_dataset.py --method clone
```

### Update Dataset
```bash
python sync_dataset.py --method pull
```

### Download Dataset Release
```bash
python sync_dataset.py --method download --release v1.0
```

### Check Everything
```bash
python diagnose_github_automation.py
```

### Verify Before Upload
```bash
python upload_to_github.py --check-only
```

---

## 🔑 Key Features

### 1. Dual Repository Support
- Upload codebase and dataset separately
- Independent control of each repo
- Can update either one at any time

### 2. Safe Large File Handling
- Detects files >100MB automatically
- Recommends Git LFS when needed
- Prevents accidental large file commits

### 3. Flexible Syncing
- **Clone**: Download full dataset repo
- **Pull**: Update existing clone
- **Download**: Get release ZIP (for CI/CD)

### 4. GitHub Actions Integration
- Automatic scheduled commits (every 6 hours)
- Manual trigger via GitHub UI
- Dataset validation workflows
- Cross-repo synchronization

### 5. Security First
- Token stored locally in `.env` (not committed)
- `.env.example` provides template
- Token validation before operations
- Clear error messages on auth failures

### 6. Production Ready
- Color-coded output (✓ success, ✗ error, ⚠ warning)
- Comprehensive error handling
- Detailed logging and reporting
- Extensive documentation

---

## ⚙️ Configuration

### Create `.env` File

**Option 1: Automatic (Recommended)**
```bash
python setup_github_automation.py
```

**Option 2: Manual**
```bash
cp .env.example .env
# Edit .env with your values
```

### Required Settings

```env
# GitHub token from https://github.com/settings/tokens/new
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Your repository URLs
CODEBASE_REPO_URL=https://github.com/yourname/model-repo.git
DATASET_REPO_URL=https://github.com/yourname/dataset-repo.git

# Git user (for commits)
GIT_USER_NAME=Your Name
GIT_USER_EMAIL=your@email.com
```

### Optional Settings

```env
# Paths (defaults shown)
CODEBASE_PATH=.
DATASET_PATH=./data

# Safety options
ENABLE_GIT_LFS=true
MAX_FILE_SIZE_MB=100
AUTO_PUSH=true
```

---

## 🔒 Security Checklist

- [ ] GitHub token created with `repo` scope only
- [ ] `.env` file in `.gitignore` (should be automatic)
- [ ] `.env` file is NOT committed to git
- [ ] `.env.example` has placeholder values only
- [ ] Token has appropriate expiration (90 days recommended)
- [ ] You have tested with `--check-only` flag
- [ ] Only necessary scopes enabled on token

---

## 🚨 Troubleshooting Guide

### Authentication Failed
```bash
# 1. Verify token in .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(len(os.getenv('GITHUB_TOKEN', '')))"

# 2. Check token has 'repo' scope
# Go to https://github.com/settings/tokens

# 3. If expired, create new token:
# https://github.com/settings/tokens/new

# 4. Update .env and retry
```

### Repository Not Found
```bash
# 1. Check URL format (must end with .git)
# https://github.com/yourname/repo-name.git ✓
# https://github.com/yourname/repo-name ✗

# 2. Verify repo exists on GitHub

# 3. Test URL manually:
git ls-remote https://github.com/yourname/repo-name.git
```

### Large Files Warning
```bash
# Option 1: Use Git LFS
git lfs install
git add .gitattributes
git commit -m "Enable Git LFS"
git lfs migrate import --include="*.pth,*.pt"

# Option 2: Increase threshold
# Edit .env: MAX_FILE_SIZE_MB=500

# Option 3: Move to dataset repo
mv large_file.zip data/
git add .gitignore
git commit -m "Moved large file to dataset repo"
```

### Git Not Found
```bash
# Check git is installed
git --version

# If not found, install from:
# https://git-scm.com/download

# On Windows: Use Git Bash or add to PATH
```

### No Changes to Commit
```bash
# This is normal if repository is up-to-date
# Make changes to files, then retry

# Force commit with custom message:
python upload_to_github.py --mode all --msg "Update"
```

### Python Dependencies Missing
```bash
# Install all dependencies:
pip install -r requirements-automation.txt

# Or install individually:
pip install python-dotenv requests
```

---

## 📊 Workflow Examples

### Daily Development Workflow
```bash
# Morning: Pull latest dataset
python sync_dataset.py --method pull

# During day: Make changes
# ... edit files ...

# Evening: Upload changes
python upload_to_github.py --mode all --msg "Daily update"
```

### Training Model Workflow
```bash
# 1. Train model
python train.py

# 2. Evaluate
python evaluate.py

# 3. Upload updated model
python upload_to_github.py --mode codebase --msg "Model v2.0: 95% accuracy"

# 4. Upload new data if generated
python upload_to_github.py --mode dataset --msg "Added 500 new samples"
```

### Dataset Release Workflow
```bash
# 1. Prepare dataset in data/ directory
# ... add/modify files ...

# 2. Commit to dataset repo
python upload_to_github.py --mode dataset --msg "Dataset v1.0 release"

# 3. Create GitHub release tag (manual on GitHub)

# 4. Sync to codebase for deployment
python sync_dataset.py --method download --release v1.0
```

### CI/CD Integration
```bash
# In your .github/workflows/train.yml:
- name: Upload results
  if: success()
  run: |
    python upload_to_github.py --mode codebase \
      --msg "Build #${{ github.run_number }} - Training complete"
```

---

## 📈 Advanced Usage

### Selective Commit Messages
```bash
# Automatic timestamp (default)
python upload_to_github.py --mode all

# Custom message
python upload_to_github.py --mode all --msg "Custom message"

# Include version
python upload_to_github.py --mode all --msg "v1.2.3: New features"

# Include timestamp and details
python upload_to_github.py --mode all --msg "Update: Model improved, accuracy 95%"
```

### Scheduled GitHub Actions
```yaml
# Edit .github/workflows/auto-commit.yml to change schedule:

# Every hour
schedule:
  - cron: '0 * * * *'

# Every 6 hours (current)
schedule:
  - cron: '0 */6 * * *'

# Daily at 9 AM UTC
schedule:
  - cron: '0 9 * * *'

# Weekdays only
schedule:
  - cron: '0 9 * * MON-FRI'
```

### Branching Strategy
```bash
# Create feature branch
git checkout -b feature/new-model

# Make changes
python upload_to_github.py --mode codebase --msg "Feature: Add new model"

# Create pull request on GitHub (manual)
# Review and merge

# Back to main
git checkout main
python upload_to_github.py --mode all
```

### Multiple Dataset Versions
```bash
# Version 1.0
python sync_dataset.py --method download --release v1.0

# Version 2.0
python sync_dataset.py --method download --release v2.0

# Latest
python sync_dataset.py --method download --release latest
```

---

## 🔧 Maintenance

### Regular Tasks

**Weekly:**
- Review GitHub Actions runs (Actions tab)
- Check for large files: `python diagnose_github_automation.py`

**Monthly:**
- Verify token hasn't expired
- Check storage usage on GitHub
- Review git log: `git log --oneline -20`

**Quarterly:**
- Refresh GitHub token (before expiration)
- Archive old releases
- Clean up old branches

### Rotating GitHub Token
```bash
# 1. Create new token
# https://github.com/settings/tokens/new

# 2. Update .env
GITHUB_TOKEN=ghp_new_token_here

# 3. Test new token
python diagnose_github_automation.py

# 4. Delete old token
# https://github.com/settings/tokens
```

### Cleanup
```bash
# View git history
git log --oneline

# Remove sensitive data (if accidentally committed)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Verify and force push (caution!)
git push -f origin main
```

---

## 📞 Quick Reference Card

### Setup Commands
```bash
python setup_github_automation.py          # Interactive setup
python diagnose_github_automation.py       # Check configuration
cp .env.example .env                       # Manual setup start
```

### Upload Commands
```bash
python upload_to_github.py --mode all                    # Upload both
python upload_to_github.py --mode codebase               # Code only
python upload_to_github.py --mode dataset                # Data only
python upload_to_github.py --check-only                  # Verify only
python upload_to_github.py --msg "Custom message"        # Custom message
```

### Dataset Commands
```bash
python sync_dataset.py --method clone                    # Download
python sync_dataset.py --method pull                     # Update
python sync_dataset.py --method download --release v1.0  # Release
```

### Git Commands
```bash
git status                                 # Check status
git log --oneline -5                       # Recent commits
git remote -v                              # Show remote URLs
git ls-remote origin HEAD                  # Test connectivity
```

---

## 📚 Documentation Map

- **Start Here:** `QUICK_START_GITHUB.md` (5 min read)
- **Detailed Guide:** `GITHUB_AUTOMATION_GUIDE.md` (30 min read)
- **This Reference:** `AUTOMATION_REFERENCE.md` (current file)
- **Full Setup:** Run `python setup_github_automation.py`
- **Diagnostics:** Run `python diagnose_github_automation.py`

---

## ✅ Verification Checklist

After setup, verify:
- [ ] `.env` file exists and contains valid token
- [ ] `.env` is in `.gitignore` (not tracked by git)
- [ ] `python diagnose_github_automation.py` shows all ✓
- [ ] `python upload_to_github.py --check-only` succeeds
- [ ] First upload with `python upload_to_github.py --mode all` works
- [ ] Files appear on GitHub in correct repos
- [ ] GitHub Actions workflows are visible
- [ ] Git LFS is setup if needed

---

## 🎓 Learning Resources

- **GitHub Docs:** https://docs.github.com
- **Git Tutorial:** https://git-scm.com/book
- **Git LFS:** https://git-lfs.github.com
- **GitHub Actions:** https://docs.github.com/en/actions
- **Personal Access Tokens:** https://github.com/settings/tokens

---

## 📝 Notes

### For Windows Users
- Use PowerShell (recommended)
- Or use Git Bash
- All Python scripts are cross-platform

### For Mac/Linux Users
- Open Terminal
- Make scripts executable: `chmod +x *.py`
- Everything should work as-is

### For Team Usage
- Share `.env.example` (safe, has placeholders)
- Each team member creates their own `.env`
- Use GitHub organization settings for permissions
- Consider using GitHub Teams for access control

---

## 🎯 Next Steps

1. **Right Now:** `python setup_github_automation.py`
2. **In 1 minute:** Check `.env` file is created
3. **In 2 minutes:** Run `python diagnose_github_automation.py`
4. **In 3 minutes:** Run `python upload_to_github.py --check-only`
5. **In 5 minutes:** Run `python upload_to_github.py --mode all`
6. **Done:** Your repos are on GitHub!

---

**Last Updated:** April 22, 2026

For issues or improvements, refer to this guide or run diagnostic tool.
