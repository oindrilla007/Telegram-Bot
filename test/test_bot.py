#!/usr/bin/env python3
"""
Test script to verify bot setup and basic functionality
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config import Config
from src.bot.main import WorkoutBot

async def test_bot_initialization():
    """Test that the bot can be initialized properly"""
    print("🤖 Testing Bot Initialization...")
    
    try:
        # Test configuration
        Config.validate_config()
        print("✅ Configuration validation passed")
        
        # Test bot creation (without starting)
        bot = WorkoutBot()
        print("✅ Bot instance created successfully")
        
        # Test application creation
        from telegram.ext import Application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        print("✅ Telegram application created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

def test_handlers_import():
    """Test that all handlers can be imported"""
    print("\n🔧 Testing Handler Imports...")
    
    try:
        from src.bot.handlers import BotHandlers
        
        # Check that all required methods exist
        required_methods = [
            'start_command',
            'handle_age_collection',
            'handle_height_collection',
            'handle_weight_collection',
            'handle_fitness_level',
            'handle_goals_collection',
            'handle_workout_request',
            'handle_general_message',
            'handle_progress_request',
            'help_command',
            'error_handler'
        ]
        
        for method in required_methods:
            if hasattr(BotHandlers, method):
                print(f"✅ {method}")
            else:
                print(f"❌ Missing method: {method}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Handler import failed: {e}")
        return False

def test_database_integration():
    """Test database integration with bot"""
    print("\n🗄️  Testing Database Integration...")
    
    try:
        from src.database.models import User, UserSession, Workout
        
        # Test that models are working
        test_user_id = 99999
        
        # Test user creation
        user = User(user_id=test_user_id, age=25)
        result = user.save()
        if result:
            print("✅ User model integration working")
        else:
            print("❌ User model integration failed")
            return False
        
        # Test session creation
        session = UserSession(user_id=test_user_id, conversation_state="TEST")
        result = session.save()
        if result:
            print("✅ Session model integration working")
        else:
            print("❌ Session model integration failed")
            return False
        
        # Cleanup
        from src.database.supabase_client import supabase_client
        supabase_client.client.table('user_sessions').delete().eq('user_id', test_user_id).execute()
        supabase_client.client.table('users').delete().eq('user_id', test_user_id).execute()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Bot Testing Suite")
    print("=" * 30)
    
    # Run all tests
    bot_init_ok = await test_bot_initialization()
    handlers_ok = test_handlers_import()
    db_ok = test_database_integration()
    
    print("\n" + "=" * 30)
    
    if bot_init_ok and handlers_ok and db_ok:
        print("🎉 All tests passed!")
        print("✅ Phase 2 Complete - Core Bot Structure ready")
        print("\n🚀 Your bot is ready to run!")
        print("\nTo start your bot:")
        print("python run_bot.py")
        print("\nThen go to Telegram and search for your bot to test it!")
        return True
    else:
        print("❌ Some tests failed")
        print("Please fix the issues before proceeding")
        return False

if __name__ == "__main__":
    asyncio.run(main())