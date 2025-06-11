from datetime import datetime
from typing import Optional, Dict, Any
import json
import logging
from src.database.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class User:
    def __init__(self, user_id: int, age: Optional[int] = None, height: Optional[float] = None, 
                 weight: Optional[float] = None, fitness_level: Optional[str] = None, 
                 goals: Optional[str] = None, id: Optional[int] = None, 
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.age = age
        self.height = height
        self.weight = weight
        self.fitness_level = fitness_level
        self.goals = goals
        self.created_at = created_at
        self.updated_at = updated_at
    
    def save(self):
        """Save user to database"""
        try:
            user_data = {
                'user_id': self.user_id,
                'age': self.age,
                'height': self.height,
                'weight': self.weight,
                'fitness_level': self.fitness_level,
                'goals': self.goals,
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if user already exists
            existing = supabase_client.client.table('users').select('*').eq('user_id', self.user_id).execute()
            
            if existing.data:
                # Update existing user
                result = supabase_client.client.table('users').update(user_data).eq('user_id', self.user_id).execute()
                logger.info(f"Updated user {self.user_id}")
            else:
                # Create new user
                result = supabase_client.client.table('users').insert(user_data).execute()
                logger.info(f"Created new user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving user {self.user_id}: {e}")
            return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int):
        """Get user by Telegram user ID"""
        try:
            result = supabase_client.client.table('users').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                data = result.data[0]
                return cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    age=data['age'],
                    height=data['height'],
                    weight=data['weight'],
                    fitness_level=data['fitness_level'],
                    goals=data['goals'],
                    created_at=data['created_at'],
                    updated_at=data['updated_at']
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def is_complete_profile(self) -> bool:
        """Check if user has completed their profile"""
        required_fields = [self.age, self.height, self.weight, self.fitness_level, self.goals]
        return all(field is not None for field in required_fields)

class Workout:
    def __init__(self, user_id: int, workout_content: Optional[Dict] = None, 
                 status: str = 'generated', trainer_feedback: Optional[str] = None,
                 id: Optional[int] = None, created_date: Optional[datetime] = None, 
                 completion_date: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.workout_content = workout_content or {}
        self.status = status  # 'generated', 'trainer_verified', 'completed'
        self.trainer_feedback = trainer_feedback
        self.created_date = created_date
        self.completion_date = completion_date
    
    def save(self):
        """Save workout to database"""
        try:
            workout_data = {
                'user_id': self.user_id,
                'workout_content': self.workout_content,
                'status': self.status,
                'trainer_feedback': self.trainer_feedback,
                'completion_date': self.completion_date.isoformat() if self.completion_date else None
            }
            
            if self.id:
                # Update existing workout
                result = supabase_client.client.table('workouts').update(workout_data).eq('id', self.id).execute()
            else:
                # Create new workout
                result = supabase_client.client.table('workouts').insert(workout_data).execute()
            
            if result.data:
                self.id = result.data[0]['id']
                logger.info(f"Saved workout {self.id} for user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving workout for user {self.user_id}: {e}")
            return None
    
    @classmethod
    def get_user_workouts(cls, user_id: int, limit: int = 10):
        """Get recent workouts for a user"""
        try:
            result = supabase_client.client.table('workouts').select('*').eq('user_id', user_id).order('created_date', desc=True).limit(limit).execute()
            
            workouts = []
            for data in result.data:
                workout = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    workout_content=data['workout_content'],
                    status=data['status'],
                    trainer_feedback=data['trainer_feedback'],
                    created_date=data['created_date'],
                    completion_date=data['completion_date']
                )
                workouts.append(workout)
            
            return workouts
            
        except Exception as e:
            logger.error(f"Error getting workouts for user {user_id}: {e}")
            return []
    
    def mark_completed(self):
        """Mark workout as completed"""
        self.status = 'completed'
        self.completion_date = datetime.now()
        return self.save()

class UserSession:
    def __init__(self, user_id: int, conversation_state: str = 'NEW_USER', 
                 temp_data: Optional[Dict] = None, id: Optional[int] = None, 
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.conversation_state = conversation_state
        self.temp_data = temp_data or {}
        self.updated_at = updated_at
    
    def save(self):
        """Save user session to database"""
        try:
            session_data = {
                'user_id': self.user_id,
                'conversation_state': self.conversation_state,
                'temp_data': self.temp_data,
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if session already exists
            existing = supabase_client.client.table('user_sessions').select('*').eq('user_id', self.user_id).execute()
            
            if existing.data:
                # Update existing session
                result = supabase_client.client.table('user_sessions').update(session_data).eq('user_id', self.user_id).execute()
            else:
                # Create new session
                result = supabase_client.client.table('user_sessions').insert(session_data).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving session for user {self.user_id}: {e}")
            return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int):
        """Get user session by Telegram user ID"""
        try:
            result = supabase_client.client.table('user_sessions').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                data = result.data[0]
                return cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    conversation_state=data['conversation_state'],
                    temp_data=data['temp_data'],
                    updated_at=data['updated_at']
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting session for user {user_id}: {e}")
            return None
    
    def update_state(self, new_state: str, temp_data: Optional[Dict] = None):
        """Update conversation state"""
        self.conversation_state = new_state
        if temp_data is not None:
            self.temp_data.update(temp_data)
        return self.save()