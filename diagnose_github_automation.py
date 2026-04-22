#!/usr/bin/env python3
"""
GitHub Automation - Diagnostic Script
Troubleshoots common issues with repository automation.

Usage:
    python3 diagnose_github_automation.py
"""

import os
import sys
import subprocess
from pathlib import Path

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

def run_command(cmd, capture=False):
    """Run command and return result."""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

class Diagnostics:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.suggestions = []

    def check_environment(self):
        """Check environment setup."""
        print_header("1. Environment Check")
        
        # Check Python version
        print_info("Checking Python version...")
        print_info(f"  Python: {sys.version}")
        if sys.version_info < (3, 7):
            print_error("Python 3.7+ required")
            self.issues.append("Python version too old")
        else:
            print_success("Python version OK")
        
        # Check git installed
        print_info("Checking Git installation...")
        success, stdout, _ = run_command("git --version", capture=True)
        if success:
            print_success(f"Git installed: {stdout}")
        else:
            print_error("Git not installed")
            self.issues.append("Git not installed")
            self.suggestions.append("Install Git from https://git-scm.com/")
        
        # Check pip
        print_info("Checking pip...")
        success, _, _ = run_command("pip --version", capture=True)
        if success:
            print_success("pip is available")
        else:
            print_error("pip not found")
            self.issues.append("pip not available")

    def check_dependencies(self):
        """Check Python dependencies."""
        print_header("2. Python Dependencies")
        
        required_packages = {
            "dotenv": "python-dotenv",
            "requests": "requests"
        }
        
        for module, package in required_packages.items():
            print_info(f"Checking {module}...")
            try:
                __import__(module)
                print_success(f"{package} is installed")
            except ImportError:
                print_warning(f"{package} is NOT installed")
                self.warnings.append(f"Missing {package}")
                self.suggestions.append(f"Install with: pip install {package}")

    def check_configuration(self):
        """Check configuration files."""
        print_header("3. Configuration Files")
        
        # Check .env
        print_info("Checking .env file...")
        env_path = Path(".env")
        if env_path.exists():
            print_success(".env file exists")
            
            # Check content
            content = env_path.read_text()
            if "GITHUB_TOKEN" in content:
                token_set = "GITHUB_TOKEN=" in content and len(content.split("GITHUB_TOKEN=")[1].split("\n")[0]) > 0
                if token_set:
                    print_success("GITHUB_TOKEN is configured")
                else:
                    print_warning("GITHUB_TOKEN appears empty")
                    self.warnings.append("GITHUB_TOKEN not set")
            else:
                print_warning("GITHUB_TOKEN not in .env")
                self.warnings.append("GITHUB_TOKEN not configured")
            
            if "CODEBASE_REPO_URL" in content or "DATASET_REPO_URL" in content:
                print_success("Repository URLs configured")
            else:
                print_warning("No repository URLs found")
                self.warnings.append("Repository URLs not configured")
        else:
            print_error(".env file not found")
            self.issues.append(".env file missing")
            if Path(".env.example").exists():
                print_info("  Run: cp .env.example .env")
                print_info("  Then edit .env with your credentials")
                self.suggestions.append("Copy .env.example to .env and configure it")

    def check_git_setup(self):
        """Check git configuration."""
        print_header("4. Git Configuration")
        
        # Check git initialized
        print_info("Checking git repository...")
        git_dir = Path(".git")
        if git_dir.exists():
            print_success("Git repository initialized")
        else:
            print_warning("Git repository not initialized")
            self.warnings.append("Repository not initialized")
            self.suggestions.append("Run: git init")
        
        # Check git config
        print_info("Checking git user config...")
        success, name, _ = run_command("git config user.name", capture=True)
        if success and name:
            print_success(f"Git user name: {name}")
        else:
            print_warning("Git user name not set")
            self.suggestions.append("Run: git config user.name 'Your Name'")
        
        success, email, _ = run_command("git config user.email", capture=True)
        if success and email:
            print_success(f"Git user email: {email}")
        else:
            print_warning("Git user email not set")
            self.suggestions.append("Run: git config user.email 'your@email.com'")
        
        # Check remote
        print_info("Checking git remote...")
        success, remotes, _ = run_command("git remote -v", capture=True)
        if success and remotes:
            print_success("Git remote configured:")
            for line in remotes.split("\n")[:2]:
                print_info(f"  {line}")
        else:
            print_warning("No git remote configured")
            self.warnings.append("Git remote not set")

    def check_connectivity(self):
        """Check GitHub connectivity."""
        print_header("5. GitHub Connectivity")
        
        print_info("Checking GitHub API access...")
        success, _, _ = run_command("curl -s https://api.github.com/rate_limit", capture=True)
        if success:
            print_success("Can reach GitHub API")
        else:
            print_warning("Cannot reach GitHub API")
            self.warnings.append("GitHub API unreachable")
            self.suggestions.append("Check internet connection")
        
        print_info("Checking git remote connectivity...")
        success, _, error = run_command("git ls-remote origin HEAD", capture=True)
        if success:
            print_success("Can connect to remote")
        else:
            if "Could not resolve" in error:
                print_error("Cannot resolve remote URL")
                self.issues.append("Remote URL invalid")
            elif "Permission denied" in error:
                print_error("Authentication failed")
                self.issues.append("Authentication error - check token")
                self.suggestions.append("Verify GITHUB_TOKEN in .env")
            else:
                print_warning(f"Remote connectivity issue: {error[:50]}")
                self.warnings.append("Cannot connect to remote")

    def check_files(self):
        """Check important files."""
        print_header("6. Important Files")
        
        files_to_check = [
            ("upload_to_github.py", "Upload script"),
            ("sync_dataset.py", "Dataset sync script"),
            ("setup_github_automation.py", "Setup wizard"),
            (".gitignore", "Git ignore file"),
            (".gitattributes", "Git attributes (LFS)"),
            (".github/workflows/auto-commit.yml", "GitHub Actions workflow"),
        ]
        
        for filename, description in files_to_check:
            path = Path(filename)
            if path.exists():
                print_success(f"{description}: ✓ {filename}")
            else:
                print_warning(f"{description}: ✗ NOT FOUND - {filename}")
                self.warnings.append(f"Missing {filename}")

    def check_large_files(self):
        """Check for problematic large files."""
        print_header("7. Large Files Check")
        
        print_info("Scanning for files >100MB...")
        
        max_size_mb = 100
        large_files = []
        
        for root, dirs, files in os.walk("."):
            # Skip .git and .venv
            if ".git" in dirs:
                dirs.remove(".git")
            if ".venv" in dirs:
                dirs.remove(".venv")
            if "venv" in dirs:
                dirs.remove("venv")
            
            for file in files:
                try:
                    file_path = Path(root) / file
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > max_size_mb:
                        large_files.append((str(file_path), size_mb))
                except:
                    pass
        
        if large_files:
            print_warning(f"Found {len(large_files)} files >100MB:")
            for path, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:5]:
                print_warning(f"  {path}: {size:.1f}MB")
            self.suggestions.append("Use Git LFS for large files or move to dataset repo")
        else:
            print_success("No problematic large files")

    def check_permissions(self):
        """Check file permissions."""
        print_header("8. File Permissions")
        
        important_files = [
            ".env",
            "upload_to_github.py",
            "sync_dataset.py",
        ]
        
        for filename in important_files:
            path = Path(filename)
            if path.exists():
                # Check if readable
                if os.access(path, os.R_OK):
                    print_success(f"{filename}: readable ✓")
                else:
                    print_error(f"{filename}: NOT readable")
                    self.issues.append(f"{filename} not readable")
                
                # Check if writable (for non-.env)
                if filename != ".env" and os.access(path, os.W_OK):
                    print_success(f"{filename}: writable ✓")

    def generate_report(self):
        """Generate diagnostic report."""
        print_header("Diagnostic Summary")
        
        if not self.issues and not self.warnings:
            print_success("Everything looks good! ✓")
            print_info("Your GitHub automation setup is ready to use.")
            return True
        
        if self.issues:
            print_error(f"\n{len(self.issues)} Issues Found:")
            for issue in self.issues:
                print_error(f"  - {issue}")
        
        if self.warnings:
            print_warning(f"\n{len(self.warnings)} Warnings:")
            for warning in self.warnings:
                print_warning(f"  - {warning}")
        
        if self.suggestions:
            print_info(f"\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                print_info(f"  {i}. {suggestion}")
        
        return len(self.issues) == 0

    def run_diagnostics(self):
        """Run all diagnostics."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}GitHub Automation Diagnostic Tool{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        self.check_environment()
        self.check_dependencies()
        self.check_configuration()
        self.check_git_setup()
        self.check_connectivity()
        self.check_files()
        self.check_large_files()
        self.check_permissions()
        
        success = self.generate_report()
        
        return success

def main():
    diagnostics = Diagnostics()
    success = diagnostics.run_diagnostics()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    if success:
        print_success("Diagnostics passed! Ready to use.")
        sys.exit(0)
    else:
        print_error("Some issues need attention. See suggestions above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
