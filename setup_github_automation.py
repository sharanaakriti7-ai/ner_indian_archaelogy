#!/usr/bin/env python3
"""
GitHub Repository Automation - Setup Script
Sets up all configuration and dependencies for automated uploads.

Usage:
    python3 setup_github_automation.py
"""

import os
import sys
import subprocess
from pathlib import Path
import getpass

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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def run_command(cmd):
    """Run shell command."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def setup_github_automation():
    """Main setup function."""
    
    print_header("GitHub Repository Automation Setup")
    
    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        print_warning(".env file already exists")
        response = input("Overwrite existing .env? (y/n): ").lower()
        if response != 'y':
            print_info("Setup cancelled")
            return False
    
    # Collect GitHub information
    print_info("Let's configure your GitHub automation setup")
    print_info("(You can find instructions at: https://github.com/settings/tokens)\n")
    
    # GitHub Token
    print("1. GitHub Token Configuration")
    print("-" * 50)
    print_info("Create a Personal Access Token at:")
    print_info("  https://github.com/settings/tokens/new")
    print_info("Scopes needed: repo (full control of private repositories)")
    print_info("Then paste the token below (input will be hidden):\n")
    
    github_token = getpass.getpass("Enter your GitHub token: ").strip()
    
    if not github_token or len(github_token) < 20:
        print_error("Invalid GitHub token")
        return False
    
    print_success("GitHub token configured")
    
    # Codebase Repository
    print("\n2. Codebase Repository Configuration")
    print("-" * 50)
    print_info("Example: https://github.com/yourusername/model-repo.git\n")
    
    codebase_repo = input("Enter codebase repository URL (or press Enter to skip): ").strip()
    if codebase_repo and not codebase_repo.startswith("https://"):
        print_error("Repository URL must start with https://")
        return False
    
    # Dataset Repository
    print("\n3. Dataset Repository Configuration")
    print("-" * 50)
    print_info("Example: https://github.com/yourusername/dataset-repo.git\n")
    
    dataset_repo = input("Enter dataset repository URL (or press Enter to skip): ").strip()
    if dataset_repo and not dataset_repo.startswith("https://"):
        print_error("Repository URL must start with https://")
        return False
    
    # Git Configuration
    print("\n4. Git Configuration")
    print("-" * 50)
    
    git_name = input("Enter git user name (default: GitHub Automation): ").strip()
    if not git_name:
        git_name = "GitHub Automation"
    
    git_email = input("Enter git user email (default: automation@github.com): ").strip()
    if not git_email:
        git_email = "automation@github.com"
    
    print_success("Git configuration collected")
    
    # Additional options
    print("\n5. Additional Options")
    print("-" * 50)
    
    enable_lfs = input("Enable Git LFS for large files? (y/n, default: y): ").lower()
    enable_lfs = enable_lfs != 'n'
    
    max_file_size = input("Maximum file size allowed (MB, default: 100): ").strip()
    if not max_file_size:
        max_file_size = "100"
    
    try:
        int(max_file_size)
    except ValueError:
        print_error("Invalid file size")
        return False
    
    # Create .env file
    print("\n6. Creating .env file...")
    print("-" * 50)
    
    env_content = f"""# GitHub Configuration
GITHUB_TOKEN={github_token}
CODEBASE_REPO_URL={codebase_repo}
DATASET_REPO_URL={dataset_repo}

# Repository Configuration
CODEBASE_PATH=.
DATASET_PATH=./data

# Git Configuration
GIT_USER_NAME={git_name}
GIT_USER_EMAIL={git_email}

# Script Options
ENABLE_GIT_LFS={str(enable_lfs).lower()}
MAX_FILE_SIZE_MB={max_file_size}
AUTO_PUSH=true
"""
    
    env_path.write_text(env_content)
    print_success(".env file created")
    
    # Setup Git LFS (optional)
    if enable_lfs:
        print("\n7. Setting up Git LFS...")
        print("-" * 50)
        
        success, stdout, stderr = run_command("git lfs --version")
        if success:
            print_success("Git LFS is installed")
            
            success, _, _ = run_command("git lfs install")
            if success:
                print_success("Git LFS initialized")
            else:
                print_warning("Could not initialize Git LFS")
        else:
            print_warning("Git LFS not installed")
            print_info("Install with: git lfs install")
    
    # Install Python dependencies
    print("\n8. Installing Python dependencies...")
    print("-" * 50)
    
    success, stdout, stderr = run_command("pip install python-dotenv requests")
    if success:
        print_success("Dependencies installed")
    else:
        print_warning("Could not install dependencies automatically")
        print_info("Install manually with: pip install python-dotenv requests")
    
    # Create .gitignore if needed
    print("\n9. Configuring .gitignore...")
    print("-" * 50)
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print_info("Creating .gitignore...")
        gitignore_content = """# Environment
.env
.env.local
*.venv
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg
*.egg-info/
dist/
build/

# OS
.DS_Store
Thumbs.db

# Model/Data (if not in separate repo)
*.pth
*.pt
*.pickle
*.pkl
"""
        gitignore_path.write_text(gitignore_content)
        print_success(".gitignore created")
    else:
        print_info(".gitignore already exists")
    
    # Summary
    print_header("Setup Complete!")
    print_success("GitHub automation is configured")
    
    print("\nNext steps:")
    print("1. Review .env file for accuracy")
    print("2. Test the upload script:")
    print("   python upload_to_github.py --check-only")
    print("3. Initial upload:")
    print("   python upload_to_github.py --mode all")
    print("\nFor dataset sync:")
    print("   python sync_dataset.py --method clone")
    
    print("\nFor automated uploads, push this to GitHub:")
    print("   git add upload_to_github.py sync_dataset.py .env.example")
    print("   git commit -m 'Add GitHub automation scripts'")
    print("   git push origin main")
    
    return True

def main():
    try:
        if setup_github_automation():
            print_success("\nSetup completed successfully!")
            sys.exit(0)
        else:
            print_error("Setup failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print_warning("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
