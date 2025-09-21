"""
Setup script for Tunisia Intelligence RSS Scraper.
"""
import os
import shutil
from pathlib import Path

def setup_project():
    """Set up the project for first-time use."""
    print("🚀 Setting up Tunisia Intelligence RSS Scraper...")
    
    # Create .env file from template if it doesn't exist
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if not env_file.exists() and env_template.exists():
        shutil.copy(env_template, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual configuration values")
    elif env_file.exists():
        print("ℹ️  .env file already exists")
    else:
        print("❌ .env.template not found")
    
    # Create necessary directories
    directories = [
        "logs",
        "data",
        "backups",
        "htmlcov"  # For test coverage reports
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
    
    # Set up git ignore for sensitive files
    gitignore_content = """
# Environment variables
.env
secrets.enc
secret.key

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backup files
backups/
*.bak
"""
    
    gitignore_file = Path(".gitignore")
    if not gitignore_file.exists():
        with open(gitignore_file, "w") as f:
            f.write(gitignore_content.strip())
        print("✅ Created .gitignore file")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run tests: pytest")
    print("4. Check database schema: python check_schema.py")
    print("5. Start scraping: python rss_loader.py")

if __name__ == "__main__":
    setup_project()
