# GitHub Automation - Quick Start (5 Minutes)

Complete your setup in 5 minutes with these exact steps.

## Step 1: Create GitHub Repositories (2 min)

### Create Codebase Repo
1. Go to https://github.com/new
2. Name: `model-repo` (or your choice)
3. Click "Create repository"
4. Copy URL: `https://github.com/yourname/model-repo.git`

### Create Dataset Repo
1. Go to https://github.com/new
2. Name: `dataset-repo` (or your choice)
3. Click "Create repository"
4. Copy URL: `https://github.com/yourname/dataset-repo.git`

## Step 2: Get GitHub Token (1 min)

1. Go to https://github.com/settings/tokens/new
2. Name: `GitHub Automation`
3. Select scope: `repo` (check the box)
4. Click "Generate token"
5. **Copy the token** (shown only once!)

## Step 3: Run Setup Wizard (2 min)

```bash
python setup_github_automation.py
```

When prompted, paste:
- GitHub token
- Codebase repo URL (from Step 1)
- Dataset repo URL (from Step 1)

The script creates `.env` automatically.

## Step 4: Verify Setup (Optional but recommended)

```bash
python upload_to_github.py --check-only
```

Should show green checkmarks ✓

## Step 5: Upload Everything

```bash
python upload_to_github.py --mode all
```

**Done!** Your project is now on GitHub with both repos.

---

## Regular Usage

### Upload after making changes:
```bash
python upload_to_github.py --mode all
```

### Update dataset from dataset repo:
```bash
python sync_dataset.py --method pull
```

### Manual GitHub Actions trigger:
1. Go to your repo → Actions tab
2. Select "Auto Commit and Push"
3. Click "Run workflow"

---

## Troubleshooting

### "Token not found" error
- Check `.env` file exists
- Check you pasted token correctly
- Make sure no extra spaces

### "Repository not found" error
- Copy URL from GitHub (not typed)
- URL must end with `.git`
- Check you have access to repo

### "No changes to commit" message
- This is OK! Repo is up-to-date
- Make file changes, then upload again

### Large files warning
```bash
# Either:
# 1. Ignore the warning and continue
# 2. Use Git LFS (see full guide)
# 3. Move files to dataset repo
```

---

## See Also

- **Full Guide:** [GITHUB_AUTOMATION_GUIDE.md](GITHUB_AUTOMATION_GUIDE.md)
- **Security Tips:** See full guide for token safety
- **Scheduled Uploads:** Full guide has GitHub Actions setup

---

That's it! You're ready to use GitHub automation.
