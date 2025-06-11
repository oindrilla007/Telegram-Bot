#!/usr/bin/env python3
"""
Test script to verify the basic setup is working correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config import Config

def test_environment_setup():
    """Test that all environment variables are loaded correctly"""
    print("🔧 Testing Environment Setup...")
    
    try:
        # Validate configuration
        Config.validate_config()
        print("✅ Configuration validation passed")
        
        # Test individual components
        print(f"📱 Telegram Bot Token: {'✅ Set' if Config.TELEGRAM_BOT_TOKEN else '❌ Missing'}")
        print(f"🤖 Gemini API Key: {'✅ Set' if Config.GEMINI_API_KEY else '❌ Missing'}")
        print(f"🗄️  Supabase URL: {'✅ Set' if Config.SUPABASE_URL else '❌ Missing'}")
        print(f"🔑 Supabase Key: {'✅ Set' if Config.SUPABASE_KEY else '❌ Missing'}")
        print(f"🐛 Debug Mode: {Config.DEBUG}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are installed"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = [
        'telegram',
        'google.generativeai',
        'supabase',
        'dotenv'
    ]
    
    failed_imports = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            failed_imports.append(dep)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_supabase_connection():
    """Test Supabase connection"""
    print("\n🗄️  Testing Supabase Connection...")
    
    try:
        from src.database.supabase_client import supabase_client
        
        # Test connection
        if supabase_client.test_connection():
            print("✅ Supabase connection successful")
            return True
        else:
            print("❌ Supabase connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

def main():
    print("🚀 Workout Bot Setup Verification (with Supabase)")
    print("=" * 50)
    
    env_ok = test_environment_setup()
    deps_ok = test_dependencies()
    
    if env_ok and deps_ok:
        # Test Supabase connection
        supabase_ok = test_supabase_connection()
        
        if supabase_ok:
            print("\n🎉 Setup Complete! Ready to proceed to Phase 1.2")
            print("\nNext steps:")
            print("1. Make sure all API keys are correctly set in .env")
            print("2. We'll create the database tables in the next phase")
        else:
            print("\n⚠️  Setup mostly complete, but Supabase connection failed")
            print("This is normal if you haven't created the tables yet")
            print("We'll fix this in Phase 1.2")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        return False
    
    return True

if __name__ == "__main__":
    main()