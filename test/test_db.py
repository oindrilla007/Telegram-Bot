#!/usr/bin/env python3
"""
Test script to verify database models and Supabase integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.models import User, Workout, UserSession
from config.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_operations():
    """Test User model operations"""
    print("👤 Testing User Operations...")
    
    # Test user creation
    test_user_id = 12345
    
    try:
        # Create a test user
        user = User(
            user_id=test_user_id,
            age=25,
            height=175.5,
            weight=70.0,
            fitness_level="intermediate",
            goals="Build muscle and lose fat"
        )
        
        # Save user
        result = user.save()
        if result:
            print("✅ User creation successful")
        else:
            print("❌ User creation failed")
            return False
        
        # Retrieve user
        retrieved_user = User.get_by_user_id(test_user_id)
        if retrieved_user and retrieved_user.age == 25:
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            return False
        
        # Test profile completeness
        if retrieved_user.is_complete_profile():
            print("✅ Profile completeness check passed")
        else:
            print("❌ Profile completeness check failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ User operations error: {e}")
        return False

def test_workout_operations():
    """Test Workout model operations"""
    print("\n💪 Testing Workout Operations...")
    
    test_user_id = 12345
    
    try:
        # Create a test workout
        workout_content = {
            "exercises": [
                {"name": "Push-ups", "sets": 3, "reps": 15},
                {"name": "Squats", "sets": 3, "reps": 20}
            ],
            "duration": "30 minutes"
        }
        
        workout = Workout(
            user_id=test_user_id,
            workout_content=workout_content,
            status="generated"
        )
        
        # Save workout
        result = workout.save()
        if result:
            print("✅ Workout creation successful")
        else:
            print("❌ Workout creation failed")
            return False
        
        # Retrieve user workouts
        workouts = Workout.get_user_workouts(test_user_id)
        if workouts and len(workouts) > 0:
            print("✅ Workout retrieval successful")
        else:
            print("❌ Workout retrieval failed")
            return False
        
        # Mark workout as completed
        if workouts[0].mark_completed():
            print("✅ Workout completion successful")
        else:
            print("❌ Workout completion failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Workout operations error: {e}")
        return False

def test_session_operations():
    """Test UserSession model operations"""
    print("\n💬 Testing Session Operations...")
    
    test_user_id = 12345
    
    try:
        # Create a test session
        session = UserSession(
            user_id=test_user_id,
            conversation_state="COLLECTING_AGE",
            temp_data={"last_message": "What's your age?"}
        )
        
        # Save session
        result = session.save()
        if result:
            print("✅ Session creation successful")
        else:
            print("❌ Session creation failed")
            return False
        
        # Retrieve session
        retrieved_session = UserSession.get_by_user_id(test_user_id)
        if retrieved_session and retrieved_session.conversation_state == "COLLECTING_AGE":
            print("✅ Session retrieval successful")
        else:
            print("❌ Session retrieval failed")
            return False
        
        # Update session state
        if retrieved_session.update_state("ACTIVE", {"profile_completed": True}):
            print("✅ Session update successful")
        else:
            print("❌ Session update failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Session operations error: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    test_user_id = 12345
    
    try:
        from src.database.supabase_client import supabase_client
        
        # Delete test records
        supabase_client.client.table('workouts').delete().eq('user_id', test_user_id).execute()
        supabase_client.client.table('user_sessions').delete().eq('user_id', test_user_id).execute()
        supabase_client.client.table('users').delete().eq('user_id', test_user_id).execute()
        
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    print("🗄️  Database Models Test")
    print("=" * 30)
    
    # Test all operations
    user_ok = test_user_operations()
    workout_ok = test_workout_operations()
    session_ok = test_session_operations()
    
    # Clean up
    cleanup_test_data()
    
    if user_ok and workout_ok and session_ok:
        print("\n🎉 All database tests passed!")
        print("✅ Phase 1.2 Complete - Database setup successful")
        print("\nReady to proceed to Phase 2: Core Bot Structure")
    else:
        print("\n❌ Some database tests failed")
        print("Please check your Supabase setup and table creation")
    
    return user_ok and workout_ok and session_ok

if __name__ == "__main__":
    main()