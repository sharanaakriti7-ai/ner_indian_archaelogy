# GitHub Automation - Complete System Architecture

Visual guide showing how all components work together.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR LOCAL MACHINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           PYTHON AUTOMATION SCRIPTS                      │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  1. setup_github_automation.py                           │   │
│  │     ↓                                                     │   │
│  │     Creates: .env (configuration)                        │   │
│  │                                                          │   │
│  │  2. upload_to_github.py                                  │   │
│  │     ↓                                                     │   │
│  │     Stages files → Commits → Pushes                      │   │
│  │     Works on: Code Repo, Data Repo, or Both              │   │
│  │                                                          │   │
│  │  3. sync_dataset.py                                      │   │
│  │     ↓                                                     │   │
│  │     Clone / Pull / Download Dataset                      │   │
│  │                                                          │   │
│  │  4. diagnose_github_automation.py                        │   │
│  │     ↓                                                     │   │
│  │     Checks: Setup, Config, Git, Connectivity            │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                    ↓                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           CONFIGURATION (.env)                           │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  • GITHUB_TOKEN (your authentication)                    │   │
│  │  • CODEBASE_REPO_URL (code repository)                   │   │
│  │  • DATASET_REPO_URL (data repository)                    │   │
│  │  • GIT_USER_NAME / EMAIL                                 │   │
│  │  • Git LFS settings                                      │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                    ↓                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           GIT OPERATIONS                                 │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  git add . → git commit "message" → git push             │   │
│  │                                                          │   │
│  │  ✓ Handles large files (Git LFS ready)                   │   │
│  │  ✓ Validates authentication                              │   │
│  │  ✓ Checks connectivity                                   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                    ↓                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           GITHUB ACTIONS                                 │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  .github/workflows/auto-commit.yml                        │   │
│  │  └─ Runs every 6 hours (or manual trigger)               │   │
│  │  └─ Auto-commits changes                                 │   │
│  │  └─ Auto-pushes to GitHub                                │   │
│  │                                                          │   │
│  │  .github/workflows/dataset-check.yml                      │   │
│  │  └─ Validates dataset integrity                          │   │
│  │  └─ Checks file sizes                                    │   │
│  │                                                          │   │
│  │  .github/workflows/cross-repo-sync.yml                    │   │
│  │  └─ Syncs changes between repos                          │   │
│  │  └─ Weekly cross-repo validation                         │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                    ↓                             │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
        ┌───────────────────────────────────────────────────┐
        │            GITHUB (Cloud)                         │
        ├───────────────────────────────────────────────────┤
        │                                                   │
        │  ┌──────────────────┐  ┌──────────────────┐      │
        │  │  CODE REPO       │  │  DATASET REPO    │      │
        │  │  (model-repo)    │  │  (dataset-repo)  │      │
        │  ├──────────────────┤  ├──────────────────┤      │
        │  │ • train.py       │  │ • train.conll    │      │
        │  │ • model.py       │  │ • test.conll     │      │
        │  │ • evaluate.py    │  │ • dev.conll      │      │
        │  │ • .github/       │  │ • README.md      │      │
        │  │ • requirements   │  │ (data files only)│      │
        │  │                  │  │                  │      │
        │  │ NO DATA FILES    │  │ NO CODE FILES    │      │
        │  └──────────────────┘  └──────────────────┘      │
        │           ↑                      ↑                │
        │           │                      │                │
        │           └──────────────────────┘                │
        │              GitHub Actions                       │
        │           (automated workflows)                   │
        │                                                   │
        └───────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
DEVELOPMENT CYCLE:

┌─────────────────────────────────────────────────────────────────┐
│                    YOU MAKE CHANGES                             │
│  (edit code, train model, add data, etc.)                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│           RUN: python upload_to_github.py --mode all            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ↓                              ↓
┌──────────────────┐      ┌──────────────────┐
│ Stage All Files  │      │ Validate Large   │
│ (git add .)      │      │ Files (>100MB)   │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         └────────────┬────────────┘
                      ↓
        ┌─────────────────────────┐
        │ Create Git Commit       │
        │ (with timestamp/message)│
        └────────────┬────────────┘
                     ↓
        ┌─────────────────────────┐
        │ Push to GitHub          │
        │ (2 separate repos)      │
        └────────────┬────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│              GITHUB RECEIVES CHANGES                            │
│                                                                 │
│  ✓ Code Repo Updated    ✓ Dataset Repo Updated                 │
│  ✓ GitHub Actions Run   ✓ Workflows Triggered                  │
│  ✓ History Preserved    ✓ Commits Visible                      │
└─────────────────────────────────────────────────────────────────┘

AUTOMATIC (Optional, with GitHub Actions):

┌─────────────────────────────────────────────────────────────────┐
│              SCHEDULED AUTO-COMMIT (every 6 hours)              │
│                                                                 │
│  • GitHub Actions detects changes                              │
│  • Auto-commits with timestamp                                 │
│  • Auto-pushes to repository                                   │
│  • No manual action needed!                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Comparison

### Manual Upload (Current Default)
```
1. Make changes locally
   ↓
2. Run: python upload_to_github.py --mode all
   ↓
3. Files on GitHub immediately
   ↓
4. Repeat every time you make changes
```

### Automated with GitHub Actions
```
1. Make changes locally
   ↓
2. Commit locally: git commit -m "message"
   ↓
3. Push locally: git push
   ↓
4. GitHub Actions auto-commits & pushes
   ↓
5. Everything happens automatically!
```

---

## 📁 Complete File Structure

```
your-project/
│
├── .env                              ← Your credentials (SECRET! Not committed)
├── .env.example                      ← Template (Safe to commit)
├── .gitignore                        ← What to exclude
├── .gitattributes                    ← Git LFS configuration
│
├── .github/
│   └── workflows/
│       ├── auto-commit.yml           ← Auto-upload every 6 hours
│       ├── dataset-check.yml         ← Validate dataset
│       └── cross-repo-sync.yml       ← Sync between repos
│
├── AUTOMATION SCRIPTS:
│   ├── upload_to_github.py           ← Main upload script ⭐
│   ├── sync_dataset.py               ← Manage dataset
│   ├── setup_github_automation.py    ← Initial setup
│   └── diagnose_github_automation.py ← Troubleshooting
│
├── DOCUMENTATION:
│   ├── SETUP_PACKAGE_README.md       ← Start here!
│   ├── QUICK_START_GITHUB.md         ← 5 minute setup
│   ├── CHEATSHEET.md                 ← Command reference
│   ├── GITHUB_AUTOMATION_GUIDE.md    ← Complete guide
│   └── AUTOMATION_REFERENCE.md       ← Full reference
│
├── REQUIREMENTS:
│   └── requirements-automation.txt   ← Python dependencies
│
├── (Your existing project files)
│   ├── train.py
│   ├── model.py
│   ├── evaluate.py
│   ├── config.py
│   └── ...
│
└── data/                             ← Synced from dataset repo
    ├── train.conll
    ├── test.conll
    ├── dev.conll
    └── ...
```

---

## 🚀 Deployment Sequence

```
STEP 1: ONE-TIME SETUP
┌─────────────────────────────────────────┐
│ python setup_github_automation.py       │
│ Creates: .env file with your config     │
└──────────────────┬──────────────────────┘
                   │
STEP 2: VERIFY SETUP
┌──────────────────────────────────────────┐
│ python diagnose_github_automation.py     │
│ Shows: ✓ All systems ready               │
└──────────────────┬───────────────────────┘
                   │
STEP 3: INITIAL UPLOAD
┌──────────────────────────────────────────┐
│ python upload_to_github.py --mode all    │
│ Pushes: All files to GitHub              │
└──────────────────┬───────────────────────┘
                   │
STEP 4: REGULAR USAGE
┌──────────────────────────────────────────┐
│ Make changes → Run upload → GitHub ready │
│ (repeat as needed)                       │
└──────────────────────────────────────────┘

OPTIONAL: SETUP AUTOMATION
┌──────────────────────────────────────────┐
│ Enable GitHub Actions                    │
│ Auto-uploads every 6 hours               │
│ No manual work needed!                   │
└──────────────────────────────────────────┘
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│         GITHUB TOKEN (Secret)           │
├─────────────────────────────────────────┤
│ Location: .env file (local only)        │
│ Scope: repo (minimal permissions)       │
│ Not committed to git                    │
│ Expires: 90 days (rotate regularly)     │
│ Used by: Python scripts for auth        │
└─────────────────────────────────────────┘
                   ↓
        ┌──────────────────────┐
        │  .env (Local file)   │
        │ DO NOT COMMIT THIS!  │
        │ .gitignore protects  │
        └──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ Python Scripts       │
        │ Read token from .env │
        │ Use for GitHub auth  │
        └──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ GitHub API           │
        │ Validates token      │
        │ Authenticates request│
        └──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ Files Uploaded       │
        │ Securely pushed      │
        │ History preserved    │
        └──────────────────────┘
```

---

## 📊 Component Interaction

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  User (You)                                                  │
│  │                                                          │
│  └─→ Python Script                                          │
│      │                                                       │
│      ├─→ Read .env file                                     │
│      │                                                       │
│      ├─→ Get GitHub Token & Repo URLs                       │
│      │                                                       │
│      ├─→ Execute Git Commands                               │
│      │   ├─ git add .                                       │
│      │   ├─ git commit -m "message"                         │
│      │   └─ git push                                        │
│      │                                                       │
│      ├─→ Handle Large Files                                 │
│      │   ├─ Detect (>100MB)                                 │
│      │   └─ Suggest Git LFS                                 │
│      │                                                       │
│      ├─→ Report Status                                      │
│      │   ├─ ✓ Success (green)                              │
│      │   ├─ ✗ Error (red)                                  │
│      │   └─ ⚠ Warning (yellow)                             │
│      │                                                       │
│      └─→ GitHub API                                         │
│          │                                                   │
│          ├─→ Authenticate                                   │
│          ├─→ Validate Request                               │
│          ├─→ Store Files                                    │
│          └─→ Update Repository                              │
│                                                              │
│  GitHub Actions (Optional)                                  │
│  │                                                          │
│  ├─→ Scheduled Trigger (every 6 hours)                     │
│  ├─→ Detect Changes                                         │
│  ├─→ Run auto-commit workflow                              │
│  └─→ Push to Repository                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Decision Tree

```
                    ┌─ START HERE ─┐
                    │              │
                    ↓
            Do I have GitHub?
                    ├─ NO  → Create account (github.com)
                    └─ YES → Continue
                           ↓
                    Do I have 2 repos?
                           ├─ NO  → Create:
                           │        1. model-repo
                           │        2. dataset-repo
                           └─ YES → Continue
                           ↓
                    Do I have token?
                           ├─ NO  → Create at
                           │        github.com/settings/tokens
                           └─ YES → Continue
                           ↓
            ┌─ Run: python setup_github_automation.py ─┐
            │                                          │
            ├─→ Creates .env automatically             │
            ├─→ Installs dependencies                  │
            └─→ Validates configuration                │
                           ↓
            ┌─ Run: python diagnose_github_automation.py ─┐
            │                                            │
            ├─→ Shows: ✓ All green checks                │
            └─→ Or: Shows issues to fix                  │
                           ↓
            ┌─ Run: python upload_to_github.py --mode all ┐
            │                                             │
            ├─→ Uploads code to: model-repo               │
            ├─→ Uploads data to: dataset-repo             │
            └─→ Shows: ✓ Upload successful                │
                           ↓
                    ✓ DONE! 🎉
```

---

## 💡 Key Concepts

### What Gets Uploaded Where?

```
CODE REPOSITORY (model-repo):
├─ train.py              ✓ Include
├─ model.py              ✓ Include
├─ evaluate.py           ✓ Include
├─ config.py             ✓ Include
├─ .github/workflows/    ✓ Include
├─ .gitignore            ✓ Include
├─ requirements.txt      ✓ Include
├─ README.md             ✓ Include
│
└─ data/ files           ✗ EXCLUDE (goes to dataset repo)

DATASET REPOSITORY (dataset-repo):
├─ train.conll           ✓ Include
├─ test.conll            ✓ Include
├─ dev.conll             ✓ Include
├─ data files            ✓ Include
│
└─ code files            ✗ EXCLUDE (goes to code repo)
```

---

## 🔄 Sync Patterns

```
PATTERN 1: CODE-DRIVEN (Development)
┌─────────────────────────────────────┐
│ You develop code locally            │
│ Upload code changes                 │
│ Sync dataset when needed            │
│ Update model based on new data      │
└─────────────────────────────────────┘

PATTERN 2: DATA-DRIVEN (Analysis)
┌─────────────────────────────────────┐
│ New data available                  │
│ Upload to dataset-repo              │
│ Sync to codebase                    │
│ Train model on new data             │
│ Upload updated model                │
└─────────────────────────────────────┘

PATTERN 3: CONTINUOUS (CI/CD)
┌─────────────────────────────────────┐
│ GitHub Actions triggers             │
│ Runs training pipeline              │
│ Generates new model                 │
│ Auto-commits model update           │
│ Auto-pushes to repository           │
│ No manual action needed             │
└─────────────────────────────────────┘
```

---

## 📈 Scaling Pattern

```
SINGLE REPO (Start):
Local → GitHub

DUAL REPO (Growth):
Local {Code + Data} → GitHub {Code} + GitHub {Dataset}

MULTIPLE TEAMS (Scale):
Team 1 → Local → GitHub Organization
Team 2 → Local → GitHub Organization
        ↓
    Shared Dataset Repo

ENTERPRISE (Advanced):
Multiple Projects → Multiple Code Repos
    ↓
    Shared Dataset Repo
    ↓
    ML Pipeline Repo
    ↓
    Deployment Repo
```

---

This architecture ensures:
✓ Clean separation of concerns
✓ Scalable structure
✓ Security through token management
✓ Automated workflows
✓ Easy collaboration

---

**For implementation details, see the documentation files mentioned in SETUP_PACKAGE_README.md**
