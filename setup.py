#!/usr/bin/env python3
"""
SWHA Backend Setup Script
This script helps you set up the environment configuration for the SWHA Backend.
"""

import os
import secrets
import shutil
from pathlib import Path

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file from template."""
    template_file = Path("env.template")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("❌ env.template file not found!")
        return False
    
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Keeping existing .env file.")
            return True
    
    # Copy template to .env
    shutil.copy(template_file, env_file)
    
    # Read the content
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate a new secret key
    new_secret_key = generate_secret_key()
    
    # Replace the placeholder secret key
    content = content.replace(
        'SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars',
        f'SECRET_KEY={new_secret_key}'
    )
    
    # Write back the content
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created .env file with generated secret key!")
    return True

def check_python_version():
    """Check Python version compatibility."""
    import sys
    
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3:
        print("❌ Python 3 is required!")
        return False
    
    if version.minor < 8:
        print("❌ Python 3.8 or higher is required!")
        return False
    
    if version.minor >= 13:
        print("⚠️  Python 3.13 detected. You may encounter issues with PyTorch.")
        print("   Consider using Python 3.11 or 3.12 for better compatibility.")
    
    return True

def create_directories():
    """Create necessary directories."""
    directories = [
        "app/static/uploads",
        "app/static/uploads/videos",
        "app/static/uploads/images", 
        "app/static/uploads/thumbnails",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("🎉 Setup completed! Next steps:")
    print("="*60)
    print()
    print("1. 📝 Edit .env file with your configuration:")
    print("   - Update DATABASE_URL with your PostgreSQL credentials")
    print("   - Configure CORS_ORIGINS for your frontend")
    print("   - Set up email settings if needed")
    print()
    print("2. 📦 Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("3. 🗄️  Set up database:")
    print("   # Create PostgreSQL database first")
    print("   alembic revision --autogenerate -m 'Initial migration'")
    print("   alembic upgrade head")
    print()
    print("4. 🚀 Run the application:")
    print("   python main.py")
    print()
    print("5. 📚 Check API documentation:")
    print("   http://localhost:8000/docs")
    print()
    print("💡 Tips:")
    print("   - Use PostgreSQL for production")
    print("   - For development, you can use SQLite (already configured)")
    print("   - Make sure to backup your .env file")
    print("   - Check README.md for detailed instructions")

def main():
    """Main setup function."""
    print("🚀 SWHA Backend Setup")
    print("="*30)
    print()
    
    # Check Python version
    if not check_python_version():
        return
    
    print()
    
    # Create .env file
    if not create_env_file():
        return
    
    print()
    
    # Create directories
    print("📁 Creating directories...")
    create_directories()
    
    print()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main() 