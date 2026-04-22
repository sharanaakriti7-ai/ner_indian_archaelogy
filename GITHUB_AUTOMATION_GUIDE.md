# GitHub Repository Automation Guide

Complete guide to automate uploading your ML project and dataset to separate GitHub repositories.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [GitHub Actions](#github-actions)
7. [Dataset Sync](#dataset-sync)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Options](#advanced-options)

---

## 🎯 Overview

This automation system provides:

- **`upload_to_github.py`** - Automated upload script for both repositories
- **`sync_dataset.py`** - Pull/clone/download dataset from separate repo
- **`setup_github_automation.py`** - Interactive setup wizard
- **GitHub Actions workflow** - Automatic commits on schedule or manual trigger
- **Git LFS support** - Handle large files safely
- **Environment configuration** - Secure token management via `.env`

### Repository Structure

```
YOUR PROJECT
├── .github/
│   └── workflows/
│       └── auto-commit.yml       # GitHub Actions workflow
├── upload_to_github.py           # Main upload script
├── sync_dataset.py               # Dataset sync script
├── setup_github_automation.py    # Setup wizard
├── .env                          # Configuration (DO NOT commit)
├── .env.example                  # Configuration template
├── .gitignore                    # Exclude sensitive files
├── .gitattributes                # Git LFS configuration
└── data/                         # Separate dataset repo
    ├── train.conll
    ├── test.conll
    └── ...
```

---

## 📦 Prerequisites

### Required
- Git installed and configured locally
- GitHub account with two repositories:
  - **Codebase repo** - For ML code/models
  - **Dataset repo** - For data files
- Python 3.7+
- GitHub Personal Access Token (PAT)

### Optional
- Git LFS (for files >100MB)
- GitHub Actions enabled (on both repos)

### Creating GitHub Repositories

**Codebase Repository:**
1. Go to https://github.com/new
2. Repository name: `model-repo` (or your choice)
3. Description: "ML Model and Training Code"
4. Make it **Public** or **Private** (your choice)
5. Click "Create repository"

**Dataset Repository:**
1. Go to https://github.com/new
2. Repository name: `dataset-repo` (or your choice)
3. Description: "Dataset for ML Project"
4. Make it **Public** or **Private** (your choice)
5. Click "Create repository"

### Creating GitHub Personal Access Token

1. Go to https://github.com/settings/tokens/new
2. Set token name: `GitHub Automation`
3. Set expiration: 90 days or custom
4. Select scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (GitHub Actions)
5. Click "Generate token"
6. **Copy and save** the token (shown only once!)

---

## 🚀 Initial Setup

### Step 1: Run Setup Wizard

```bash
python setup_github_automation.py
```

This interactive script will:
- Ask for GitHub token
- Configure repository URLs
- Set git user information
- Enable Git LFS (optional)
- Create `.env` file
- Install dependencies

### Step 2: Verify Configuration

```bash
python upload_to_github.py --check-only
```

This checks:
- `.env` file is valid
- Repositories are accessible
- No problematic large files
- Git configuration

### Step 3: First Upload

```bash
# Upload both repositories
python upload_to_github.py --mode all

# Or upload only codebase
python upload_to_github.py --mode codebase

# Or upload only dataset
python upload_to_github.py --mode dataset
```

---

## 💻 Usage

### Upload Script Commands

#### Upload Everything
```bash
python upload_to_github.py --mode all
```

#### Upload Only Codebase
```bash
python upload_to_github.py --mode codebase
```

#### Upload Only Dataset
```bash
python upload_to_github.py --mode dataset
```

#### Custom Commit Message
```bash
python upload_to_github.py --mode all --msg "v1.0: Release with improved model"
```

#### Check Without Uploading
```bash
python upload_to_github.py --mode all --check-only
```

#### Show Help
```bash
python upload_to_github.py --help
```

### Script Output Example

```
════════════════════════════════════════════════════════════════
                  GITHUB REPOSITORY AUTO-UPLOAD
════════════════════════════════════════════════════════════════

ℹ Mode: all
ℹ Working with path: /path/to/codebase

════════════════════════════════════════════════════════════════
                        UPLOADING CODEBASE
════════════════════════════════════════════════════════════════

✓ Loaded configuration from .env
✓ Working with path: /path/to/codebase
ℹ Repository already initialized
ℹ Configuring git for codebase...
✓ Repository initialized
✓ .gitignore created
ℹ Scanning for large files...
✓ No problematic large files found
ℹ Staging files...
✓ Staged files for commit
ℹ Committing changes with message: 'Auto-commit: 2026-04-22 15:30:45'
✓ Changes committed
ℹ Pushing changes to remote repository...
✓ Changes pushed to remote repository
✓ CODEBASE upload completed successfully!
ℹ Total commits: 5
ℹ Last commit: a1b2c3d - Auto-commit: 2026-04-22 15:30:45

════════════════════════════════════════════════════════════════
                       UPLOAD SUMMARY
════════════════════════════════════════════════════════════════

✓ codebase: ✓ Uploaded successfully
✓ dataset: ✓ Uploaded successfully
```

---

## ⚙️ Configuration

### .env File

Create `.env` in your project root (use `.env.example` as template):

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CODEBASE_REPO_URL=https://github.com/yourusername/model-repo.git
DATASET_REPO_URL=https://github.com/yourusername/dataset-repo.git

# Repository Configuration
CODEBASE_PATH=.
DATASET_PATH=./data

# Git Configuration
GIT_USER_NAME=Your Name
GIT_USER_EMAIL=your.email@example.com

# Script Options
ENABLE_GIT_LFS=true
MAX_FILE_SIZE_MB=100
AUTO_PUSH=true
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_...` |
| `CODEBASE_REPO_URL` | Codebase repository URL | `https://github.com/user/model-repo.git` |
| `DATASET_REPO_URL` | Dataset repository URL | `https://github.com/user/dataset-repo.git` |
| `CODEBASE_PATH` | Path to codebase (usually `.`) | `.` |
| `DATASET_PATH` | Path to dataset directory | `./data` |
| `GIT_USER_NAME` | Name for commits | `Your Name` |
| `GIT_USER_EMAIL` | Email for commits | `your@email.com` |
| `ENABLE_GIT_LFS` | Enable Git LFS | `true` or `false` |
| `MAX_FILE_SIZE_MB` | Max file size threshold | `100` |
| `AUTO_PUSH` | Auto-push changes | `true` or `false` |

### .gitignore Configuration

Both `.gitignore` files are automatically created with sensible defaults:

```gitignore
# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Python
__pycache__/
*.py[cod]
*.egg-info/

# Models & Data (optional)
*.pth
*.pt
*.pkl

# OS
.DS_Store
Thumbs.db
```

### Git LFS Configuration (.gitattributes)

For large files, uncomment patterns in `.gitattributes`:

```gitattributes
# Model files
*.pth filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text

# Data files
*.csv filter=lfs diff=lfs merge=lfs -text

# Archives
*.zip filter=lfs diff=lfs merge=lfs -text
```

To enable Git LFS:

```bash
git lfs install
# Then uncomment patterns in .gitattributes
git add .gitattributes
git commit -m "Enable Git LFS for large files"
```

---

## 🤖 GitHub Actions

### Automatic Workflow

The `.github/workflows/auto-commit.yml` workflow automatically:

1. **Runs on every push** - Commits any new changes
2. **Scheduled runs** - Every 6 hours (configurable)
3. **Manual trigger** - Via GitHub Actions UI

### Workflow File Location

```
.github/
└── workflows/
    └── auto-commit.yml
```

### Trigger Workflow Manually

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Auto Commit and Push" workflow
4. Click "Run workflow"
5. (Optional) Enter custom commit message
6. Click "Run workflow"

### Modify Schedule

Edit `.github/workflows/auto-commit.yml`:

```yaml
schedule:
  # Run every 6 hours (current)
  - cron: '0 */6 * * *'
  
  # Examples:
  # Every hour:     - cron: '0 * * * *'
  # Daily at 9 AM:  - cron: '0 9 * * *'
  # Weekly Monday:  - cron: '0 9 * * MON'
```

### Workflow Permissions

The workflow needs write access to your repository. This is automatic for public repos, but for private repos:

1. Go to Settings → Actions → General
2. Under "Workflow permissions"
3. Select "Read and write permissions"
4. Click "Save"

---

## 📥 Dataset Sync

### Sync Methods

#### 1. Clone (Full Copy)
Downloads entire dataset repository locally:

```bash
python sync_dataset.py --method clone
```

**Use when:**
- First-time setup
- Need complete dataset
- Working offline

#### 2. Pull (Update)
Updates existing clone with latest changes:

```bash
python sync_dataset.py --method pull
```

**Use when:**
- Dataset already cloned locally
- Want latest changes from remote
- Regular updates

#### 3. Download (Release)
Downloads dataset from GitHub release:

```bash
python sync_dataset.py --method download
```

**Use when:**
- Large dataset in separate repo
- Want specific release version
- Don't need version history

### Usage Examples

```bash
# Clone dataset for first time
python sync_dataset.py --method clone

# Update local dataset
python sync_dataset.py --method pull

# Download specific release
python sync_dataset.py --method download --release v1.0

# Download to custom path
python sync_dataset.py --method clone --path ./datasets/my-data

# Use custom repository
python sync_dataset.py --method clone --repo https://github.com/user/dataset-repo.git
```

### Dataset Workflow

**First Time:**
```bash
python sync_dataset.py --method clone
```

**Regular Updates:**
```bash
# In main repo
python sync_dataset.py --method pull

# Or sync automatically in script
import subprocess
subprocess.run(["python", "sync_dataset.py", "--method", "pull"])
```

**In CI/CD:**
```bash
# Download specific release for reproducibility
python sync_dataset.py --method download --release v1.0
```

---

## 🔧 Troubleshooting

### Authentication Failed

**Error:** `fatal: could not read Password for 'https://github.com'`

**Solution:**
1. Verify GitHub token is correct in `.env`
2. Check token hasn't expired (refresh if needed)
3. Ensure token has `repo` scope
4. Try regenerating token:
   - Go to https://github.com/settings/tokens
   - Delete old token
   - Create new token with proper scopes
   - Update `.env`

```bash
# Verify token is set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token length:', len(os.getenv('GITHUB_TOKEN', '')))"
```

### Repository Not Found

**Error:** `fatal: repository not found`

**Solution:**
1. Verify repository URL in `.env`:
   ```bash
   # Should be (with .git at end):
   CODEBASE_REPO_URL=https://github.com/yourusername/model-repo.git
   ```
2. Check repository exists on GitHub
3. Verify you have access to repository
4. Test URL in browser (should show repo or 404)

### Large Files Warning

**Error:** `Found N files larger than 100MB`

**Solution - Option 1:** Use Git LFS

```bash
# Enable Git LFS
git lfs install

# Edit .gitattributes to track large files
# Then:
git add .gitattributes
git commit -m "Enable Git LFS"

# Add existing large files to LFS
git lfs migrate import --include="*.pth,*.pt,*.zip"
```

**Solution - Option 2:** Increase threshold

Edit `.env`:
```env
MAX_FILE_SIZE_MB=500
```

**Solution - Option 3:** Move files to dataset repo

Move large data files to dataset repository instead.

### No Changes to Commit

**Message:** `No changes to commit`

**Explanation:** This is normal - means repository is up-to-date

**Solution:** 
- Make changes to files
- Then run upload again
- Or use `--msg` to force specific commit message

### SSH Connection Issues

**Error:** `Permission denied (publickey)`

**Solution:** Use HTTPS instead of SSH

```env
# ✓ CORRECT (HTTPS with token)
CODEBASE_REPO_URL=https://github.com/yourusername/model-repo.git

# ✗ NOT SUPPORTED (SSH)
CODEBASE_REPO_URL=git@github.com:yourusername/model-repo.git
```

### Git Not Found

**Error:** `'git' is not recognized`

**Solution:**
- Install Git from https://git-scm.com/download
- Add git to PATH (usually automatic)
- Restart terminal/IDE
- Verify: `git --version`

### Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
pip install python-dotenv requests
```

---

## 🔒 Security Best Practices

### Protect Your GitHub Token

1. **Never commit `.env` file**
   - Already in `.gitignore`, but double-check
   - Use `.env.example` for template only

2. **Rotate tokens regularly**
   - GitHub tokens expire (recommendation: 90 days)
   - Refresh token when it expires
   - Delete old tokens immediately

3. **Limit token scopes**
   - Only enable necessary scopes
   - For uploads: only need `repo` scope
   - Never use personal access tokens in public repos

4. **Monitor token usage**
   - Check https://github.com/settings/tokens for usage
   - Delete unused tokens
   - Review recent activity

### Secure .env Storage

**Development:**
- Keep `.env` local only
- Add to `.gitignore` (done automatically)
- Never share `.env` file

**Shared Machines:**
- Use restricted file permissions:
  ```bash
  chmod 600 .env  # Linux/Mac
  ```

**CI/CD (GitHub Actions):**
- Use GitHub Secrets instead of `.env`:
  1. Go to Settings → Secrets and Variables → Actions
  2. Click "New repository secret"
  3. Name: `GITHUB_TOKEN`
  4. Value: Your PAT
- Reference in workflow:
  ```yaml
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ```

---

## 📊 Advanced Options

### Scheduled Uploads

### Cron Expression Guide

The GitHub Actions workflow uses cron syntax:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Common Schedules:**

| Schedule | Cron | When |
|----------|------|------|
| Every hour | `0 * * * *` | Top of each hour |
| Every 6 hours | `0 */6 * * *` | 12am, 6am, 12pm, 6pm |
| Daily 9 AM | `0 9 * * *` | 9:00 AM UTC daily |
| Weekdays only | `0 9 * * MON-FRI` | 9 AM Monday-Friday |
| Weekly Monday | `0 9 * * MON` | 9 AM every Monday |
| First day of month | `0 0 1 * *` | 12 AM on 1st |

### Custom Upload Script Integration

Integrate with your ML training pipeline:

**In `train.py`:**
```python
import subprocess
import os
from datetime import datetime

def upload_after_training():
    """Upload model after successful training."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Model training completed: {timestamp}"
    
    # Upload with custom message
    subprocess.run([
        "python", "upload_to_github.py",
        "--mode", "codebase",
        "--msg", message
    ])

# In your training script
if __name__ == "__main__":
    train_model()
    evaluate_model()
    upload_after_training()  # Auto-upload after done
```

### Separate Branches

Create dedicated branches for data:

```bash
# Create data branch (in dataset repo)
git checkout -b data-updates
python sync_dataset.py --method pull
git push origin data-updates

# Or use tags for releases
git tag -a v1.0 -m "Dataset version 1.0"
git push origin v1.0
```

### CI/CD Integration

**Example: Upload on successful build**

In `.github/workflows/your-pipeline.yml`:

```yaml
- name: Upload model artifacts
  if: success()
  run: |
    python upload_to_github.py --mode codebase --msg "Build #${{ github.run_number }}"
```

---

## 📝 Quick Reference

### First-Time Commands

```bash
# 1. Interactive setup
python setup_github_automation.py

# 2. Verify configuration
python upload_to_github.py --check-only

# 3. Initial upload
python upload_to_github.py --mode all

# 4. Sync dataset
python sync_dataset.py --method clone
```

### Regular Commands

```bash
# Daily upload
python upload_to_github.py --mode all

# Update dataset
python sync_dataset.py --method pull

# Check before upload
python upload_to_github.py --check-only

# Custom commit message
python upload_to_github.py --mode all --msg "Your message"
```

### Emergency Commands

```bash
# If something breaks, reset authentication:
rm .env
python setup_github_automation.py

# Check git status
git status

# View recent commits
git log --oneline -5

# Test git connectivity
git ls-remote origin
```

---

## 📚 Additional Resources

- **GitHub Documentation:** https://docs.github.com
- **Git Tutorial:** https://git-scm.com/book
- **Personal Access Tokens:** https://github.com/settings/tokens
- **GitHub Actions:** https://docs.github.com/en/actions
- **Git LFS:** https://git-lfs.github.com

---

## 📞 Support

### If Something Goes Wrong

1. Check error messages carefully
2. See **Troubleshooting** section above
3. Verify `.env` configuration
4. Test with `--check-only` flag
5. Check git connectivity: `git ls-remote origin`

### Debug Mode

Check all configuration:
```bash
python upload_to_github.py --check-only
```

View git log:
```bash
git log --oneline -10
```

Check git remote:
```bash
git remote -v
```

---

## 📜 License

These automation scripts are part of your project.

---

**Last Updated:** April 22, 2026

For questions or improvements, refer to your project's issue tracker.
