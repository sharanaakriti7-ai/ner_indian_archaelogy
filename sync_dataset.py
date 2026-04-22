#!/usr/bin/env python3
"""
Dataset Auto-Sync Script
Downloads/syncs dataset from a separate dataset repository.

Usage:
    python3 sync_dataset.py --method clone     # Clone dataset repo
    python3 sync_dataset.py --method pull      # Pull latest from dataset repo
    python3 sync_dataset.py --method download  # Download release zip
"""

import os
import sys
import subprocess
import argparse
import urllib.request
import zipfile
from pathlib import Path
from dotenv import load_dotenv
import json

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

class DatasetSync:
    def __init__(self, dataset_repo_url, dataset_path="./data"):
        self.dataset_repo_url = dataset_repo_url
        self.dataset_path = Path(dataset_path).resolve()
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.git_user_name = os.getenv("GIT_USER_NAME", "Dataset Sync")
        self.git_user_email = os.getenv("GIT_USER_EMAIL", "sync@github.com")

    def run_command(self, cmd, cwd=None, capture=False):
        """Execute shell command."""
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
                result = subprocess.run(cmd, cwd=cwd, shell=True)
                return result.returncode, "", ""
        except Exception as e:
            return 1, "", str(e)

    def clone_dataset(self):
        """Clone dataset repository."""
        print_header("Cloning Dataset Repository")
        
        if self.dataset_path.exists():
            print_warning(f"Dataset path already exists: {self.dataset_path}")
            response = input("Overwrite? (y/n): ").lower()
            if response != 'y':
                print_info("Clone cancelled")
                return False
            
            import shutil
            shutil.rmtree(self.dataset_path)
        
        # Prepare URL with authentication
        repo_url = self.dataset_repo_url
        if self.github_token:
            repo_url = repo_url.replace(
                "https://",
                f"https://{self.github_token}@"
            )
        
        print_info(f"Cloning from: {self.dataset_repo_url}")
        returncode, stdout, stderr = self.run_command(
            f'git clone "{repo_url}" "{self.dataset_path}"',
            capture=True
        )
        
        if returncode != 0:
            print_error(f"Clone failed: {stderr}")
            return False
        
        print_success(f"Dataset cloned to: {self.dataset_path}")
        
        # Show dataset info
        self.show_dataset_info()
        return True

    def pull_dataset(self):
        """Pull latest dataset from repository."""
        print_header("Pulling Latest Dataset")
        
        if not self.dataset_path.exists():
            print_error(f"Dataset path does not exist: {self.dataset_path}")
            print_info("Run 'python sync_dataset.py --method clone' first")
            return False
        
        git_dir = self.dataset_path / ".git"
        if not git_dir.exists():
            print_error("Not a git repository")
            return False
        
        print_info("Configuring git...")
        self.run_command(f'git config user.name "{self.git_user_name}"')
        self.run_command(f'git config user.email "{self.git_user_email}"')
        
        print_info("Pulling latest changes...")
        returncode, stdout, stderr = self.run_command(
            "git pull origin main || git pull origin master",
            cwd=self.dataset_path,
            capture=True
        )
        
        if returncode != 0:
            print_warning(f"Pull completed with warnings: {stderr}")
        else:
            print_success("Dataset updated successfully")
        
        self.show_dataset_info()
        return True

    def download_release_zip(self, owner, repo, release_tag="latest"):
        """Download dataset from GitHub release."""
        print_header("Downloading Dataset from Release")
        
        print_info(f"Repository: {owner}/{repo}")
        print_info(f"Release: {release_tag}")
        
        # Construct download URL
        if release_tag == "latest":
            url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            try:
                import json
                import urllib.request
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    
                    if "assets" not in data or len(data["assets"]) == 0:
                        print_error("No assets found in latest release")
                        return False
                    
                    # Find zip file
                    zip_url = None
                    for asset in data["assets"]:
                        if asset["name"].endswith(".zip"):
                            zip_url = asset["browser_download_url"]
                            break
                    
                    if not zip_url:
                        print_error("No ZIP file found in release assets")
                        return False
                    
                    print_info(f"Downloading: {data['tag_name']}")
                    return self._download_and_extract(zip_url)
                    
            except Exception as e:
                print_error(f"Failed to fetch release info: {e}")
                return False
        else:
            url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{release_tag}.zip"
            return self._download_and_extract(url)

    def _download_and_extract(self, url):
        """Download and extract ZIP file."""
        try:
            print_info("Downloading...")
            zip_path = Path("dataset_temp.zip")
            
            urllib.request.urlretrieve(url, zip_path)
            print_success("Download completed")
            
            print_info("Extracting...")
            
            if self.dataset_path.exists():
                import shutil
                shutil.rmtree(self.dataset_path)
            
            self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.dataset_path.parent)
            
            # Clean up
            zip_path.unlink()
            
            print_success(f"Dataset extracted to: {self.dataset_path}")
            self.show_dataset_info()
            return True
            
        except Exception as e:
            print_error(f"Download/extraction failed: {e}")
            return False

    def show_dataset_info(self):
        """Display dataset information."""
        if not self.dataset_path.exists():
            return
        
        print_info("Dataset contents:")
        
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.dataset_path):
            # Skip .git
            if ".git" in dirs:
                dirs.remove(".git")
            
            for file in files:
                file_path = Path(root) / file
                try:
                    total_files += 1
                    total_size += file_path.stat().st_size
                except:
                    pass
        
        total_size_mb = total_size / (1024 * 1024)
        print_info(f"  Files: {total_files}")
        print_info(f"  Total size: {total_size_mb:.2f} MB")
        
        # List main files
        main_files = list(self.dataset_path.glob("*"))
        for f in main_files[:5]:
            if f.name != ".git":
                print_info(f"  - {f.name}")
        
        if len(main_files) > 5:
            print_info(f"  ... and {len(main_files) - 5} more items")

    def sync(self, method="clone"):
        """Main sync method."""
        if method == "clone":
            return self.clone_dataset()
        elif method == "pull":
            return self.pull_dataset()
        elif method == "download":
            # Parse owner/repo from URL
            # Example: https://github.com/owner/repo
            if "github.com" in self.dataset_repo_url:
                parts = self.dataset_repo_url.rstrip("/").split("/")
                repo = parts[-1].replace(".git", "")
                owner = parts[-2]
                return self.download_release_zip(owner, repo)
            else:
                print_error("Only GitHub repositories supported for download method")
                return False
        else:
            print_error(f"Unknown sync method: {method}")
            return False


def load_env():
    """Load environment variables."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print_success("Loaded configuration from .env")
    else:
        print_warning("No .env file found")

def main():
    parser = argparse.ArgumentParser(
        description="Dataset Auto-Sync Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
  clone    - Clone entire dataset repository (full copy)
  pull     - Pull latest changes from existing clone
  download - Download and extract from GitHub release

Examples:
  python sync_dataset.py --method clone
  python sync_dataset.py --method pull
  python sync_dataset.py --method download --repo owner/repo --release v1.0
        """
    )
    
    parser.add_argument(
        "--method",
        choices=["clone", "pull", "download"],
        default="clone",
        help="Sync method to use"
    )
    
    parser.add_argument(
        "--repo",
        type=str,
        help="Dataset repository URL or owner/repo"
    )
    
    parser.add_argument(
        "--path",
        type=str,
        default="./data",
        help="Path to sync dataset to (default: ./data)"
    )
    
    parser.add_argument(
        "--release",
        type=str,
        default="latest",
        help="Release tag to download (default: latest)"
    )
    
    args = parser.parse_args()
    
    load_env()
    
    # Get dataset repo URL
    dataset_repo = args.repo or os.getenv("DATASET_REPO_URL", "")
    
    if not dataset_repo:
        print_error("Dataset repository URL not provided")
        print_info("Set DATASET_REPO_URL in .env or use --repo option")
        sys.exit(1)
    
    print_header("Dataset Sync Tool")
    print_info(f"Method: {args.method}")
    print_info(f"Repository: {dataset_repo}")
    print_info(f"Path: {args.path}")
    
    sync = DatasetSync(dataset_repo, args.path)
    
    if args.method == "download":
        if "/" in dataset_repo:
            parts = dataset_repo.split("/")
            owner = parts[-2]
            repo = parts[-1].replace(".git", "")
            success = sync.download_release_zip(owner, repo, args.release)
        else:
            success = sync.sync(args.method)
    else:
        success = sync.sync(args.method)
    
    if success:
        print_success("Dataset sync completed successfully")
        sys.exit(0)
    else:
        print_error("Dataset sync failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
