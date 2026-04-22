# GitHub Automation - Practical Examples

Real-world examples you can copy and paste!

---

## 🎯 Example 1: First-Time Setup

### Terminal Commands

```bash
# Step 1: Interactive setup (2 minutes)
python setup_github_automation.py

# When prompted, enter:
# - GitHub token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# - Codebase repo: https://github.com/yourusername/model-repo.git
# - Dataset repo: https://github.com/yourusername/dataset-repo.git
# - Git name: Your Name
# - Git email: your.email@example.com

# Step 2: Verify setup (1 minute)
python diagnose_github_automation.py

# Look for: All ✓ marks (green checkmarks)
# If errors appear, fix them before continuing

# Step 3: Initial upload (2 minutes)
python upload_to_github.py --mode all

# Should show:
# ✓ Files staged
# ✓ Changes committed
# ✓ Changes pushed
# ✓ Upload completed successfully
```

### What Gets Created

```
✓ .env file (your config, DO NOT commit!)
✓ .gitignore entry (protects .env)
✓ Git initialized (if needed)
✓ Remote added (if needed)
✓ Files pushed to GitHub
```

### Result

- Your code files → `model-repo` on GitHub
- Your data files → `dataset-repo` on GitHub
- Version history preserved
- Ready for team collaboration

---

## 🎯 Example 2: Daily Development Workflow

### After Training a Model

```bash
# 1. You trained a new model
python train.py
# ... model saved to ./model/best_model.pth

# 2. You updated the code
# ... edited train.py with improvements

# 3. Upload everything
python upload_to_github.py --mode all --msg "Model v2.0: Improved accuracy"

# 4. Check on GitHub (should see files immediately)
# https://github.com/yourusername/model-repo
# → Commit: "Model v2.0: Improved accuracy"
```

### Terminal Output

```
════════════════════════════════════════════════════════════════
                  GITHUB REPOSITORY AUTO-UPLOAD
════════════════════════════════════════════════════════════════

ℹ Mode: all
ℹ Custom commit message: Model v2.0: Improved accuracy

════════════════════════════════════════════════════════════════
                        UPLOADING CODEBASE
════════════════════════════════════════════════════════════════

✓ Working with path: /your/project
ℹ Repository already initialized
ℹ Configuring git for codebase...
ℹ Staging files...
✓ Staged 5 files for commit
ℹ Committing changes with message: 'Model v2.0: Improved accuracy'
✓ Changes committed
ℹ Pushing changes to remote repository...
✓ Changes pushed to remote repository
✓ CODEBASE upload completed successfully!
ℹ Total commits: 42
ℹ Last commit: a1b2c3d - Model v2.0: Improved accuracy

════════════════════════════════════════════════════════════════
                        UPLOADING DATASET
════════════════════════════════════════════════════════════════

✓ Working with path: /your/project/data
ℹ Repository already initialized
ℹ Configuring git for dataset...
ℹ Staging files...
ℹ No changes to commit
ℹ Nothing to do for dataset repo
✓ DATASET upload skipped (no changes)

════════════════════════════════════════════════════════════════
                       UPLOAD SUMMARY
════════════════════════════════════════════════════════════════

✓ codebase: ✓ Uploaded successfully
✓ dataset: ✓ No changes (skipped)
```

---

## 🎯 Example 3: Large Dataset Update

### Adding 500 New Training Samples

```bash
# 1. You added new data files
# data/additional_samples/ (500 new files)

# 2. Upload dataset only
python upload_to_github.py --mode dataset --msg "Added 500 new samples"

# 3. Other developers pull the update
# (in their dataset sync)
python sync_dataset.py --method pull

# They now have the new data!
```

### File Structure

```
data/
├── train.conll (updated with new data)
├── dev.conll (rebalanced)
├── test.conll (fresh test set)
└── additional_samples/ (500 new files)
    ├── sample_001.txt
    ├── sample_002.txt
    └── ...
```

---

## 🎯 Example 4: Checking Before Upload

### Verify Without Pushing

```bash
# Check what would happen
python upload_to_github.py --check-only

# Output:
# ✓ Configuration valid
# ✓ Repository accessible
# ✓ Git connectivity OK
# ✓ No problematic large files
# Ready to upload!
```

### When It Shows Issues

```bash
# If large files detected:
⚠ Found 2 files larger than 100MB:
  - models/large_model.pth (523.4MB)
  - data/archive.zip (250.1MB)

# Solutions:
# 1. Use Git LFS (recommended for models)
# 2. Move to dataset repo (for data)
# 3. Increase threshold (not recommended)
```

---

## 🎯 Example 5: Syncing Dataset from Another Repo

### First-Time Dataset Setup

```bash
# Clone the dataset repository
python sync_dataset.py --method clone

# Output:
# ℹ Cloning from: https://github.com/org/dataset-repo.git
# ... (downloading files)
# ✓ Dataset cloned to: ./data
# ℹ Dataset contents:
#   Files: 1,245
#   Total size: 5.2 GB
#   - train.conll (2.1 GB)
#   - test.conll (1.5 GB)
#   - additional_data/ (1.6 GB)

# Now you have all the data!
```

### Updating Existing Dataset

```bash
# Someone else pushed new data
# Pull the latest version
python sync_dataset.py --method pull

# Output:
# ℹ Pulling latest changes...
# Already up to date! (or shows what changed)
# ✓ Dataset updated successfully
```

### Download Specific Release

```bash
# Need a specific version
python sync_dataset.py --method download --release v1.0

# Useful for:
# - Reproducibility
# - CI/CD pipelines
# - Specific model training
# - Deployment
```

---

## 🎯 Example 6: Custom Commit Messages

### Pattern 1: Version Number

```bash
python upload_to_github.py --mode all --msg "v1.2.3: Release"
# Shows on GitHub as commit: "v1.2.3: Release"
```

### Pattern 2: Feature Description

```bash
python upload_to_github.py --mode codebase --msg "Add BERT tokenizer support"
# Useful for: Understanding what changed
```

### Pattern 3: Model Metrics

```bash
python upload_to_github.py --mode codebase \
  --msg "Model update: F1=0.89, Precision=0.92, Recall=0.86"
# Useful for: Tracking performance improvements
```

### Pattern 4: Bug Fixes

```bash
python upload_to_github.py --mode all --msg "Fix: GPU memory leak in evaluation.py"
# Useful for: Issue tracking
```

### Pattern 5: Default (Automatic)

```bash
python upload_to_github.py --mode all
# Auto-creates: "Auto-commit: 2026-04-22 15:30:45"
```

---

## 🎯 Example 7: Separate Code and Data Uploads

### Upload Only Code

```bash
# After improving model:
python upload_to_github.py --mode codebase

# Only model-repo is updated
# dataset-repo is untouched
```

### Upload Only Data

```bash
# After collecting new samples:
python upload_to_github.py --mode dataset

# Only dataset-repo is updated
# model-repo is untouched
```

### Upload Both

```bash
# After both training and data collection:
python upload_to_github.py --mode all

# Both repositories are updated
# Parallel uploads (fast!)
```

---

## 🎯 Example 8: Troubleshooting

### Scenario 1: Token Expired

```bash
# Error: Authentication failed

# Fix:
# 1. Create new token at https://github.com/settings/tokens/new
# 2. Edit .env: GITHUB_TOKEN=ghp_new_token_here
# 3. Test: python diagnose_github_automation.py
# 4. Retry: python upload_to_github.py --mode all
```

### Scenario 2: Repository Not Found

```bash
# Error: Repository not found

# Fix:
# 1. Check repo exists on GitHub
# 2. Check URL ends with .git
# 3. Check you have access
# 4. Verify in .env:
#    CODEBASE_REPO_URL=https://github.com/yourname/model-repo.git
```

### Scenario 3: Large Files Warning

```bash
# Warning: Found 3 files larger than 100MB

# Option A: Enable Git LFS
git lfs install
git add .gitattributes
git commit -m "Enable Git LFS"

# Option B: Move to dataset repo
mv large_file.pth data/

# Option C: Increase threshold (not recommended)
# Edit .env: MAX_FILE_SIZE_MB=500
```

### Scenario 4: Git Not Initialized

```bash
# Error: Not a git repository

# Fix:
python upload_to_github.py --mode all
# Script auto-initializes git if needed

# Or manual:
git init
git remote add origin <url>
```

---

## 🎯 Example 9: GitHub Actions Manual Trigger

### Via Web UI

```
1. Go to: https://github.com/yourusername/model-repo
2. Click: Actions tab
3. Select: "Auto Commit and Push" workflow
4. Click: "Run workflow" button
5. (Optional) Enter custom commit message
6. Click: "Run workflow"

Result: Auto-commit runs immediately on GitHub's servers
```

### Change Schedule

```yaml
# Edit .github/workflows/auto-commit.yml

schedule:
  - cron: '0 */6 * * *'  # Every 6 hours (current)
  # - cron: '0 * * * *'  # Every hour
  # - cron: '0 9 * * *'  # Daily 9 AM UTC
  # - cron: '0 9 * * MON'  # Every Monday 9 AM
```

---

## 🎯 Example 10: Team Collaboration Workflow

### Scenario: Team of 3 Data Scientists

```
PERSON A (You):
  python setup_github_automation.py
  python upload_to_github.py --mode all
  # Code uploaded to model-repo
  # Data uploaded to dataset-repo

PERSON B (Colleague):
  python sync_dataset.py --method pull
  # Downloads latest data
  python train.py
  # Uses your data
  python upload_to_github.py --mode codebase --msg "Improved hyperparameters"
  # Uploads their improvements

PERSON C (Another colleague):
  git pull origin main
  # Gets latest code from Person B
  python sync_dataset.py --method pull
  # Gets latest data from Person A
  python evaluate.py
  # Evaluates combined model
  # Everyone has same environment!
```

### Benefits

- Everyone uses same data version
- Everyone has latest code
- All changes tracked
- Easy to see who changed what
- Easy to revert if needed

---

## 🎯 Example 11: CI/CD Integration

### Training Pipeline with Auto-Upload

```bash
#!/bin/bash
# train_and_upload.sh

echo "Starting training..."
python train.py

echo "Evaluating model..."
python evaluate.py

echo "Uploading results..."
python upload_to_github.py --mode codebase --msg "Training complete: $(date)"

echo "Done!"
```

### Run It

```bash
chmod +x train_and_upload.sh
./train_and_upload.sh

# Or with Python:
python -c "
import subprocess
subprocess.run(['python', 'train.py'])
subprocess.run(['python', 'evaluate.py'])
subprocess.run([
    'python', 'upload_to_github.py',
    '--mode', 'codebase',
    '--msg', 'Training complete'
])
"
```

---

## 🎯 Example 12: Release Management

### Creating a Model Release

```bash
# 1. Final model trained and saved
python train.py
# → Saved to: models/release_v1.0.pth

# 2. Update version in code
# Edit: config.py → VERSION = "1.0.0"

# 3. Upload release
python upload_to_github.py --mode codebase --msg "Release v1.0.0"

# 4. Create GitHub Release (manual on GitHub)
# Go to: https://github.com/yourname/model-repo/releases/new
# Tag: v1.0.0
# Title: "Model v1.0.0 - Initial Release"
# Description: "First production model"
# Attach: model file (if not in repo)

# 5. Deploy/Use
# Other projects can now reference: v1.0.0
```

---

## 🎯 Example 13: Configuration Options

### Minimal Setup (.env)

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CODEBASE_REPO_URL=https://github.com/yourname/model-repo.git
DATASET_REPO_URL=https://github.com/yourname/dataset-repo.git
```

### Production Setup (.env)

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CODEBASE_REPO_URL=https://github.com/myorg/ml-models.git
DATASET_REPO_URL=https://github.com/myorg/ml-datasets.git

GIT_USER_NAME=ML Pipeline
GIT_USER_EMAIL=ml-pipeline@company.com

CODEBASE_PATH=./src
DATASET_PATH=./data

ENABLE_GIT_LFS=true
MAX_FILE_SIZE_MB=200
AUTO_PUSH=true
```

### Advanced Setup (with Git LFS)

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CODEBASE_REPO_URL=https://github.com/myorg/ml-models.git
DATASET_REPO_URL=https://github.com/myorg/ml-datasets.git

GIT_USER_NAME=ML-Bot
GIT_USER_EMAIL=bot@company.com

CODEBASE_PATH=.
DATASET_PATH=./data

# Git LFS for models
ENABLE_GIT_LFS=true
MAX_FILE_SIZE_MB=500

# Auto-push enabled (for CI/CD)
AUTO_PUSH=true
```

---

## 🎯 Quick Copy-Paste Commands

```bash
# Setup
python setup_github_automation.py
python diagnose_github_automation.py

# Upload
python upload_to_github.py --mode all
python upload_to_github.py --mode codebase
python upload_to_github.py --mode dataset
python upload_to_github.py --mode all --msg "Custom message"

# Check
python upload_to_github.py --check-only
python diagnose_github_automation.py

# Dataset
python sync_dataset.py --method clone
python sync_dataset.py --method pull
python sync_dataset.py --method download --release v1.0

# Git
git status
git log --oneline -5
git remote -v
```

---

## ✅ Verification Checklist

After each upload, verify:

```
✓ No error messages
✓ Files appear on GitHub
✓ Commit message is visible
✓ All files uploaded (not just some)
✓ Timestamps are recent
✓ No conflicts or issues
```

---

## 🎓 Learning by Doing

### Task 1: Basic Upload (15 min)
1. Make a small change to a file
2. Run: `python upload_to_github.py --mode codebase`
3. Check GitHub for the change

### Task 2: Custom Message (10 min)
1. Make another change
2. Run: `python upload_to_github.py --mode codebase --msg "My first custom message"`
3. See custom message on GitHub

### Task 3: Both Repos (10 min)
1. Make code and data changes
2. Run: `python upload_to_github.py --mode all`
3. See both repos updated

### Task 4: Dataset Sync (10 min)
1. Run: `python sync_dataset.py --method pull`
2. Check that data/ folder updated
3. Run: `git status` to see what changed

### Task 5: Check Before Upload (5 min)
1. Run: `python upload_to_github.py --check-only`
2. Review warnings/suggestions
3. Then run without `--check-only` if OK

---

**Now you have real-world examples you can use immediately!**

Copy, paste, run, and adapt to your needs! 🚀
