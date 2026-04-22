#!/usr/bin/env python3
"""
GitHub Repository Auto-Upload Script
Automates git operations for both codebase and dataset repositories.

Usage:
    python3 upload_to_github.py --mode all           # Upload both repos
    python3 upload_to_github.py --mode codebase      # Upload only codebase
    python3 upload_to_github.py --mode dataset       # Upload only dataset
    python3 upload_to_github.py --help               # Show help
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

class GitUploader:
    def __init__(self, repo_path, repo_url, repo_name="repo"):
        self.repo_path = Path(repo_path).resolve()
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.git_user_name = os.getenv("GIT_USER_NAME", "GitHub Automation")
        self.git_user_email = os.getenv("GIT_USER_EMAIL", "automation@github.com")
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
        self.enable_git_lfs = os.getenv("ENABLE_GIT_LFS", "true").lower() == "true"
        
    def run_command(self, cmd, cwd=None, capture=False):
        """Execute shell command and handle errors."""
        if cwd is None:
            cwd = self.repo_path
            
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                return result.returncode, result.stdout.strip(), result.stderr.strip()
            else:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    shell=True
                )
                return result.returncode, "", ""
        except Exception as e:
            return 1, "", str(e)

    def check_repo_exists(self):
        """Check if .git directory exists."""
        git_dir = self.repo_path / ".git"
        return git_dir.exists()

    def setup_git_config(self):
        """Configure git user if not already configured."""
        print_info(f"Configuring git for {self.repo_name}...")
        
        # Set local git config
        self.run_command(f'git config user.name "{self.git_user_name}"')
        self.run_command(f'git config user.email "{self.git_user_email}"')
        
        if self.github_token:
            # Setup authentication with token
            repo_url_with_token = self.repo_url.replace(
                "https://",
                f"https://{self.github_token}@"
            )
        else:
            repo_url_with_token = self.repo_url
            
        return repo_url_with_token

    def initialize_repo(self):
        """Initialize git repository if not already initialized."""
        if self.check_repo_exists():
            print_info(f"Repository already initialized at {self.repo_path}")
            return True
            
        print_info(f"Initializing git repository in {self.repo_path}...")
        returncode, _, stderr = self.run_command("git init", capture=True)
        
        if returncode != 0:
            print_error(f"Failed to initialize repo: {stderr}")
            return False
            
        print_success("Repository initialized")
        return True

    def check_large_files(self):
        """Scan for files larger than threshold."""
        print_info("Scanning for large files...")
        
        large_files = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip git directory
            if ".git" in dirs:
                dirs.remove(".git")
            
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if file_size_mb > self.max_file_size_mb:
                        large_files.append({
                            "path": str(file_path.relative_to(self.repo_path)),
                            "size_mb": round(file_size_mb, 2)
                        })
                except OSError:
                    pass
        
        if large_files:
            print_warning(f"Found {len(large_files)} files larger than {self.max_file_size_mb}MB:")
            for f in large_files[:10]:  # Show first 10
                print_warning(f"  - {f['path']} ({f['size_mb']}MB)")
            if len(large_files) > 10:
                print_warning(f"  ... and {len(large_files) - 10} more")
            
            if self.enable_git_lfs:
                print_info("Git LFS is enabled. Consider tracking these files with LFS.")
                return True
            else:
                return False
        
        print_success("No problematic large files found")
        return True

    def setup_gitignore(self):
        """Ensure .gitignore exists with common patterns."""
        gitignore_path = self.repo_path / ".gitignore"
        
        # Common patterns for both codebase and dataset
        common_patterns = [
            "# Environment",
            ".env",
            ".env.local",
            "*.venv",
            ".venv/",
            "venv/",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            "*.egg",
            "*.egg-info/",
            "dist/",
            "build/",
            "",
            "# Data & Models (if not in separate dataset repo)",
            "*.pth",
            "*.pt",
            "*.pickle",
            "*.pkl",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
        ]
        
        if gitignore_path.exists():
            print_info(f".gitignore already exists at {gitignore_path}")
        else:
            gitignore_path.write_text("\n".join(common_patterns) + "\n")
            print_success(f".gitignore created at {gitignore_path}")

    def add_files(self):
        """Stage all files for commit."""
        print_info("Staging files...")
        returncode, stdout, stderr = self.run_command("git add -A", capture=True)
        
        if returncode != 0:
            print_error(f"Failed to stage files: {stderr}")
            return False
        
        # Check if there are changes
        returncode, stdout, stderr = self.run_command(
            "git status --porcelain",
            capture=True
        )
        
        if not stdout:
            print_warning("No changes to commit")
            return False
        
        print_success(f"Staged files for commit")
        return True

    def commit_changes(self, message=None):
        """Commit staged changes."""
        if message is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto-commit: {timestamp}"
        
        print_info(f"Committing changes with message: '{message}'")
        returncode, _, stderr = self.run_command(
            f'git commit -m "{message}"',
            capture=True
        )
        
        if returncode != 0:
            print_error(f"Commit failed: {stderr}")
            return False
        
        print_success("Changes committed")
        return True

    def set_remote(self, repo_url_with_auth):
        """Set or update remote origin."""
        # Check if remote exists
        returncode, stdout, _ = self.run_command(
            "git remote get-url origin",
            capture=True
        )
        
        if returncode == 0:
            print_info("Remote 'origin' already configured")
        else:
            print_info("Setting remote origin...")
            self.run_command(f'git remote add origin "{repo_url_with_auth}"')
            print_success("Remote origin added")

    def push_changes(self, repo_url_with_auth):
        """Push changes to remote repository."""
        print_info("Pushing changes to remote repository...")
        
        # Set remote with authentication
        self.set_remote(repo_url_with_auth)
        
        # Get current branch
        returncode, branch, _ = self.run_command(
            "git rev-parse --abbrev-ref HEAD",
            capture=True
        )
        
        if returncode != 0:
            branch = "main"
        
        print_info(f"Pushing to {branch} branch...")
        returncode, _, stderr = self.run_command(
            f'git push -u origin {branch}',
            capture=True
        )
        
        if returncode != 0:
            if "fatal: could not read Password" in stderr or "FATAL" in stderr:
                print_error("Authentication failed. Check your GitHub token.")
            else:
                print_error(f"Push failed: {stderr}")
            return False
        
        print_success("Changes pushed to remote repository")
        return True

    def get_commit_count(self):
        """Get number of local commits."""
        returncode, stdout, _ = self.run_command(
            "git rev-list --count HEAD",
            capture=True
        )
        
        if returncode == 0:
            return int(stdout)
        return 0

    def get_last_commit(self):
        """Get last commit hash and message."""
        returncode, stdout, _ = self.run_command(
            "git log -1 --pretty=format:'%h - %s'",
            capture=True
        )
        
        if returncode == 0:
            return stdout
        return "No commits yet"

    def upload(self, commit_message=None):
        """Main upload workflow."""
        print_header(f"Uploading {self.repo_name.upper()}")
        
        # Step 1: Check path exists
        if not self.repo_path.exists():
            print_error(f"Path does not exist: {self.repo_path}")
            return False
        
        print_success(f"Working with path: {self.repo_path}")
        
        # Step 2: Initialize repo if needed
        if not self.initialize_repo():
            return False
        
        # Step 3: Configure git
        repo_url_with_auth = self.setup_git_config()
        
        # Step 4: Setup .gitignore
        self.setup_gitignore()
        
        # Step 5: Check for large files
        if not self.check_large_files():
            print_warning("Large files detected without Git LFS enabled")
            response = input("Continue anyway? (y/n): ").lower()
            if response != 'y':
                print_warning("Upload cancelled")
                return False
        
        # Step 6: Add files
        if not self.add_files():
            print_info("No new changes to commit")
            if self.get_commit_count() == 0:
                print_error("No commits in repository and no changes to add")
                return False
        else:
            # Step 7: Commit changes
            if not self.commit_changes(commit_message):
                return False
        
        # Step 8: Push changes
        if not self.push_changes(repo_url_with_auth):
            return False
        
        print_success(f"{self.repo_name.upper()} upload completed successfully!")
        print_info(f"Total commits: {self.get_commit_count()}")
        print_info(f"Last commit: {self.get_last_commit()}")
        
        return True


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print_success("Loaded configuration from .env")
    else:
        print_warning("No .env file found. Creating from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print_info("Please edit .env with your GitHub credentials")
            print_info("Rerun the script after configuration")
        else:
            print_error("Neither .env nor .env.example found")
        sys.exit(1)

def validate_config():
    """Validate required environment variables."""
    errors = []
    
    if not os.getenv("GITHUB_TOKEN"):
        errors.append("GITHUB_TOKEN not set")
    
    if not os.getenv("CODEBASE_REPO_URL") and not os.getenv("DATASET_REPO_URL"):
        errors.append("Neither CODEBASE_REPO_URL nor DATASET_REPO_URL set")
    
    if errors:
        print_error("Configuration validation failed:")
        for error in errors:
            print_error(f"  - {error}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="GitHub Repository Auto-Upload Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_to_github.py --mode all          Upload both repos
  python upload_to_github.py --mode codebase     Upload only codebase
  python upload_to_github.py --mode dataset      Upload only dataset
  python upload_to_github.py --mode all --msg "Version 1.0"
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["all", "codebase", "dataset"],
        default="all",
        help="Which repository to upload (default: all)"
    )
    
    parser.add_argument(
        "--msg",
        type=str,
        default=None,
        help="Custom commit message (default: timestamp)"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check configuration and large files, don't upload"
    )
    
    args = parser.parse_args()
    
    # Load and validate configuration
    load_env()
    if not validate_config():
        sys.exit(1)
    
    print_header("GitHub Repository Auto-Upload")
    print_info(f"Mode: {args.mode}")
    if args.msg:
        print_info(f"Custom commit message: {args.msg}")
    
    codebase_path = os.getenv("CODEBASE_PATH", ".")
    dataset_path = os.getenv("DATASET_PATH", "./data")
    codebase_repo_url = os.getenv("CODEBASE_REPO_URL", "")
    dataset_repo_url = os.getenv("DATASET_REPO_URL", "")
    
    results = {}
    
    # Upload codebase
    if args.mode in ["all", "codebase"] and codebase_repo_url:
        uploader = GitUploader(codebase_path, codebase_repo_url, "codebase")
        
        if args.check_only:
            print_info("Running in check-only mode...")
            uploader.initialize_repo()
            uploader.setup_git_config()
            uploader.setup_gitignore()
            uploader.check_large_files()
            results["codebase"] = "checked"
        else:
            results["codebase"] = uploader.upload(args.msg)
    
    # Upload dataset
    if args.mode in ["all", "dataset"] and dataset_repo_url:
        uploader = GitUploader(dataset_path, dataset_repo_url, "dataset")
        
        if args.check_only:
            print_info("Running in check-only mode...")
            uploader.initialize_repo()
            uploader.setup_git_config()
            uploader.setup_gitignore()
            uploader.check_large_files()
            results["dataset"] = "checked"
        else:
            results["dataset"] = uploader.upload(args.msg)
    
    # Summary
    print_header("Upload Summary")
    for repo, status in results.items():
        if status == "checked":
            print_info(f"{repo}: ✓ Checked")
        elif status:
            print_success(f"{repo}: ✓ Uploaded successfully")
        else:
            print_error(f"{repo}: ✗ Failed")
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
