#!/usr/bin/env python3
"""
Sunny AI Setup Script
Verifies installation and configures the environment.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\nChecking dependencies...")
    
    required = [
        "playwright",
        "whisper",
        "ollama",
        "reportlab",
        "fastapi",
        "structlog",
        "sounddevice",
        "aiosqlite"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    return len(missing) == 0


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print("\nChecking Playwright browsers...")
    try:
        result = subprocess.run(
            ["playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True
        )
        if "chromium" in result.stdout.lower() or result.returncode == 0:
            print("  ✅ Chromium browser available")
            return True
    except Exception:
        pass
    
    print("  ❌ Chromium not installed. Run: playwright install chromium")
    return False


def check_ollama():
    """Check if Ollama is running."""
    print("\nChecking Ollama...")
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"  ✅ Ollama is running")
            if models:
                print(f"  📦 Available models: {', '.join(m['name'] for m in models)}")
            else:
                print("  ⚠️  No models installed. Run: ollama pull llama3")
            return True
    except Exception:
        pass
    
    print("  ❌ Ollama not running. Start with: ollama serve")
    return False


def check_environment():
    """Check environment variables."""
    print("\nChecking environment variables...")
    
    gmail = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if gmail:
        print(f"  ✅ GMAIL_ADDRESS: {gmail[:3]}***@***")
    else:
        print("  ⚠️  GMAIL_ADDRESS not set (email delivery will fail)")
    
    if password:
        print(f"  ✅ GMAIL_APP_PASSWORD: ****")
    else:
        print("  ⚠️  GMAIL_APP_PASSWORD not set (email delivery will fail)")
    
    return bool(gmail and password)


def create_directories():
    """Create required directories."""
    print("\nCreating directories...")
    
    dirs = ["outputs", "temp", "logs", "data"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"  ✅ {d}/")


def main():
    print("="*60)
    print("☀️  SUNNY AI - Setup Verification")
    print("="*60)
    
    results = {
        "Python": check_python_version(),
        "Dependencies": check_dependencies(),
        "Playwright": check_playwright_browsers(),
        "Ollama": check_ollama(),
        "Environment": check_environment()
    }
    
    create_directories()
    
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "-"*60)
    
    if all_passed:
        print("✅ All checks passed! Sunny AI is ready to use.")
        print("\nRun: python main.py --help")
    else:
        print("⚠️  Some checks failed. Please resolve the issues above.")
        print("\nFor installation help, see README.md")
    
    print("="*60)


if __name__ == "__main__":
    main()
