#!/usr/bin/env python3
"""
Setup script for reCAPTCHA Automation Framework
Automates the initial setup process.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is 3.9+."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("✗ Python 3.9 or higher is required")
        return False
    
    print("✓ Python version is compatible")
    return True


def create_virtual_environment():
    """Create Python virtual environment."""
    print_header("Creating Virtual Environment")
    
    if Path("venv").exists():
        print("Virtual environment already exists")
        return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating virtual environment"
    )


def get_pip_command():
    """Get the pip command based on OS."""
    if platform.system() == "Windows":
        return "venv\\Scripts\\pip"
    else:
        return "venv/bin/pip"


def install_dependencies():
    """Install Python dependencies."""
    print_header("Installing Dependencies")
    
    pip_cmd = get_pip_command()
    
    # Upgrade pip
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
        return False
    
    return True


def install_playwright():
    """Install Playwright browsers."""
    print_header("Installing Playwright Browsers")
    
    return run_command(
        "playwright install chromium",
        "Installing Chromium browser"
    )


def setup_environment():
    """Setup environment file."""
    print_header("Setting Up Environment")
    
    if Path(".env").exists():
        print(".env file already exists")
        return True
    
    if Path(".env.example").exists():
        try:
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Created .env from .env.example")
            print("  → Edit .env to configure your settings")
            return True
        except Exception as e:
            print(f"✗ Failed to create .env: {e}")
            return False
    else:
        print("✗ .env.example not found")
        return False


def create_directories():
    """Create necessary directories."""
    print_header("Creating Directories")
    
    directories = [
        "data/logs",
        "data/results",
        "data/output"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}")
    
    return True


def run_tests():
    """Run basic tests to verify setup."""
    print_header("Running Tests")
    
    return run_command(
        "pytest tests/ -v --tb=short",
        "Running test suite"
    )


def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete! 🎉")
    
    print("Next steps:")
    print()
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print()
    print("2. Configure your settings:")
    print("   Edit .env file with your configuration")
    print()
    print("3. Run a quick test:")
    print("   python -m src.task1_automation.automation --runs 5")
    print()
    print("4. Start the API server:")
    print("   uvicorn src.task2_api.app:app --reload")
    print()
    print("5. Read the documentation:")
    print("   - README.md")
    print("   - QUICKSTART.md")
    print("   - docs/architecture.md")
    print()
    print("For more information, visit:")
    print("https://github.com/yourusername/recaptcha-automation")
    print()


def main():
    """Main setup function."""
    print_header("reCAPTCHA Automation Framework - Setup")
    print("This script will set up your development environment")
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Installing Playwright", install_playwright),
        ("Setting up environment", setup_environment),
        ("Creating directories", create_directories),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n✗ Setup failed at: {step_name}")
            print("Please fix the error and run setup again")
            sys.exit(1)
    
    # Optional: Run tests
    print("\nWould you like to run tests to verify the setup? (y/n): ", end="")
    if input().lower() == 'y':
        run_tests()
    
    print_next_steps()


if __name__ == "__main__":
    main()
