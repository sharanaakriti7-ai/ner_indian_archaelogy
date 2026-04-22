# GitHub Automation - Cheat Sheet

One-page reference for all commands and configurations.

---

## 🚀 Setup (Do This First)

```bash
# 1. Interactive setup (recommended)
python setup_github_automation.py

# 2. Or manual setup
cp .env.example .env
# Edit .env with your GitHub token and repo URLs

# 3. Verify everything
python diagnose_github_automation.py
```

## 📤 Upload Commands

```bash
# Upload everything
python upload_to_github.py --mode all

# Upload specific repo
python upload_to_github.py --mode codebase
python upload_to_github.py --mode dataset

# With custom message
python upload_to_github.py --mode all --msg "v1.0: Release"

# Check without uploading
python upload_to_github.py --check-only
```

## 📥 Dataset Commands

```bash
# Clone dataset (first time)
python sync_dataset.py --method clone

# Update dataset (exists locally)
python sync_dataset.py --method pull

# Download from release
python sync_dataset.py --method download --release v1.0
```

## 🔧 Configuration

### Create `.env` File

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CODEBASE_REPO_URL=https://github.com/yourname/model-repo.git
DATASET_REPO_URL=https://github.com/yourname/dataset-repo.git

GIT_USER_NAME=Your Name
GIT_USER_EMAIL=your@email.com

ENABLE_GIT_LFS=true
MAX_FILE_SIZE_MB=100
```

### Get GitHub Token

1. Go to https://github.com/settings/tokens/new
2. Name: "GitHub Automation"
3. Select scope: `repo` ✓
4. Click "Generate token"
5. Copy token (shown only once!)

### Create Repositories

1. https://github.com/new
   - Name: `model-repo` (codebase)
2. https://github.com/new
   - Name: `dataset-repo` (dataset)
3. Copy URLs ending in `.git`

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Token error | Check `.env` has valid token |
| Repo not found | Verify URL ends with `.git` |
| Auth failed | Regenerate token at https://github.com/settings/tokens |
| Git not found | Install from https://git-scm.com |
| Large files | Use `--check-only` to see warnings |
| Python error | `pip install python-dotenv requests` |

## 🔑 Important Files

| File | Purpose |
|------|---------|
| `.env` | Your config (DO NOT commit) |
| `.env.example` | Template (safe to commit) |
| `upload_to_github.py` | Main upload script |
| `sync_dataset.py` | Dataset management |
| `setup_github_automation.py` | Setup wizard |
| `diagnose_github_automation.py` | Troubleshoot issues |
| `.github/workflows/auto-commit.yml` | GitHub Actions |

## 📅 GitHub Actions

### Trigger Manually
1. GitHub → Actions tab
2. Select "Auto Commit and Push"
3. Click "Run workflow"

### Change Schedule
Edit `.github/workflows/auto-commit.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 * * * *'  # Every hour
  # - cron: '0 9 * * *'  # Daily 9 AM
```

## ⚡ Common Workflows

### Daily Development
```bash
python sync_dataset.py --method pull
# ... make changes ...
python upload_to_github.py --mode all
```

### Model Training
```bash
python train.py
python upload_to_github.py --mode codebase --msg "Model v2.0"
```

### Data Updates
```bash
# ... update data files ...
python upload_to_github.py --mode dataset --msg "Added 500 samples"
```

## 🔒 Security

- ✓ Generate token: https://github.com/settings/tokens/new
- ✓ Store in `.env` (not tracked by git)
- ✓ Rotate token every 90 days
- ✓ Only use `repo` scope
- ✗ Never commit `.env`
- ✗ Never share your token

## 📊 Command Options

```bash
# Check configuration
python upload_to_github.py --help
python upload_to_github.py --check-only

# Upload modes
--mode all          # Both repos
--mode codebase     # Code repo only
--mode dataset      # Data repo only

# Custom commit message
--msg "Your message"

# Dataset sync methods
--method clone      # Download full repo
--method pull       # Update existing
--method download   # Get release
```

## 🎯 First Time in 5 Minutes

```bash
# 1. Setup (2 min)
python setup_github_automation.py

# 2. Verify (1 min)
python diagnose_github_automation.py

# 3. Upload (2 min)
python upload_to_github.py --mode all

# Done! 🎉
```

## 📞 Quick Fixes

```bash
# Verify setup
python diagnose_github_automation.py

# Reset configuration
rm .env
python setup_github_automation.py

# Check git status
git status

# View recent commits
git log --oneline -5

# Test git connectivity
git ls-remote origin HEAD
```

## 📚 Documentation

- **Quick Start:** `QUICK_START_GITHUB.md` (5 min)
- **Full Guide:** `GITHUB_AUTOMATION_GUIDE.md` (30 min)
- **Reference:** `AUTOMATION_REFERENCE.md` (comprehensive)
- **Cheat Sheet:** This file

---

**Key Concept:** 
- **Codebase Repo** = ML code, models, scripts
- **Dataset Repo** = Data files (separate for easier management)
- **GitHub Actions** = Automatic uploads on schedule or manual trigger
- **Git LFS** = For files larger than 100MB

---

**Most Used Commands:**

```bash
# First time
python setup_github_automation.py

# Every time you make changes
python upload_to_github.py --mode all

# Update dataset
python sync_dataset.py --method pull

# Fix issues
python diagnose_github_automation.py
```

---

Print this page or bookmark it! 📌
