from datetime import datetime, date
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
    def __init__(self, user_id, workout_content=None, status='generated',
                 trainer_feedback=None, id=None, created_date=None, 
                 completion_date=None, scheduled_date=None,
                 workout_type='daily', exercises_completed=0, total_exercises=0,
                 skipped_exercises=0):
        self.id = id
        self.user_id = user_id
        self.workout_content = workout_content or {}
        self.status = status
        self.trainer_feedback = trainer_feedback
        self.created_date = created_date
        self.completion_date = completion_date
        self.scheduled_date = scheduled_date
        self.workout_type = workout_type
        self.exercises_completed = exercises_completed
        self.total_exercises = total_exercises
        self.skipped_exercises = skipped_exercises

    def save(self):
        """Save workout to database"""
        try:
            # Handle completion_date properly
            completion_date = self.completion_date
            if isinstance(completion_date, datetime):
                completion_date = completion_date.isoformat()
            elif isinstance(completion_date, date):
                completion_date = completion_date.isoformat()
            
            # Handle scheduled_date properly
            scheduled_date = self.scheduled_date
            if isinstance(scheduled_date, datetime):
                scheduled_date = scheduled_date.isoformat()
            elif isinstance(scheduled_date, date):
                scheduled_date = scheduled_date.isoformat()
            
            workout_data = {
                'user_id': self.user_id,
                'workout_content': self.workout_content,
                'status': self.status,
                'trainer_feedback': self.trainer_feedback,
                'completion_date': completion_date,
                'scheduled_date': scheduled_date,
                'workout_type': self.workout_type,
                'exercises_completed': self.exercises_completed,
                'total_exercises': self.total_exercises,
                'skipped_exercises': self.skipped_exercises,
            }
                        
            if self.id:
                result = supabase_client.client.table('workouts').update(workout_data).eq('id', self.id).execute()
            else:
                result = supabase_client.client.table('workouts').insert(workout_data).execute()
            
            if result.data:
                self.id = result.data[0]['id']
                logger.info(f"Saved workout {self.id} for user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving workout for user {self.user_id}: {e}", exc_info=True)
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
                    completion_date=data['completion_date'],
                    scheduled_date=data.get('scheduled_date'),
                    workout_type=data.get('workout_type', 'daily'),
                    exercises_completed=data.get('exercises_completed', 0),
                    total_exercises=data.get('total_exercises', 0),
                    skipped_exercises=data.get('skipped_exercises', 0)
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
    
    def get_completion_percentage(self) -> float:
        if not self.total_exercises or self.total_exercises == 0:
            return 0.0
        return round((self.exercises_completed / self.total_exercises) * 100, 1)

    def mark_exercise_completed(self, exercise_index: int) -> bool:
        """Mark one exercise as completed. If all are done, mark workout complete."""
        try:
            self.exercises_completed += 1
            if self.exercises_completed >= self.total_exercises:
                self.status = "completed"
                self.completion_date = datetime.utcnow()
            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to update workout {self.id} after exercise completion: {e}")
            return False

    @staticmethod
    def get_today_workout(user_id: int):
        try:
            today = datetime.now().date().isoformat()
            result = supabase_client.client.table('workouts').select('*') \
                .eq('user_id', user_id).eq('scheduled_date', today).limit(1).execute()
            if result.data:
                data = result.data[0]
                return Workout(
                    id=data['id'],
                    user_id=data['user_id'],
                    workout_content=data['workout_content'],
                    status=data['status'],
                    trainer_feedback=data.get('trainer_feedback'),
                    created_date=data['created_date'],
                    completion_date=data['completion_date']
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching today's workout: {e}")
            return None

    @staticmethod
    def create_scheduled_workout(user_id: int, workout_content: Dict, scheduled_date: str):
        try:
            workout = Workout(
                user_id=user_id,
                workout_content=workout_content,
                status="scheduled",
            )
            workout.scheduled_date = scheduled_date
            workout.total_exercises = len(workout_content.get('exercises', []))
            return workout.save()
        except Exception as e:
            logger.error(f"Failed to create scheduled workout: {e}")
            return None

    @staticmethod
    def get_completed_exercises_count(workout_id: int) -> int:
        """Get the current count of completed exercises for a workout"""
        try:
            result = supabase_client.client.table('exercise_completions') \
                .select('id', count='exact') \
                .eq('workout_id', workout_id) \
                .execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting completed exercises count: {e}")
            return 0

    def refresh_completion_count(self):
        """Refresh the exercises_completed and skipped_exercises counts from the database"""
        try:
            completions = ExerciseCompletion.get_workout_completions(self.id)
            self.exercises_completed = len([c for c in completions if c.get('status') == 'completed'])
            self.skipped_exercises = len([c for c in completions if c.get('status') == 'skipped'])
            
            # Update workout status based on completion/skip counts
            if self.exercises_completed + self.skipped_exercises >= self.total_exercises:
                # Only mark as skipped if ALL exercises are skipped
                if self.skipped_exercises == self.total_exercises and self.exercises_completed == 0:
                    self.status = "skipped"
                # Mark as completed if at least one exercise is completed
                elif self.exercises_completed > 0:
                    self.status = "completed"
                self.completion_date = datetime.utcnow()
            
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error refreshing completion count: {e}")
            return False

class DietPlan:
    def __init__(self, user_id: int, diet_content: Dict[str, Any], scheduled_date: str, 
                 status: str = 'scheduled', id: Optional[int] = None, created_date: Optional[str] = None, 
                 completion_date: Optional[str] = None):
        self.id = id
        self.user_id = user_id
        self.diet_content = diet_content
        self.scheduled_date = scheduled_date
        self.status = status
        self.created_date = created_date
        self.completion_date = completion_date

    def _serialize_dates(self, obj):
        """Recursively convert date objects to ISO format strings"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_dates(item) for item in obj]
        return obj

    def save(self):
        """Save or update the diet plan"""
        try:
            scheduled_date = self.scheduled_date
            if isinstance(scheduled_date, datetime):
                scheduled_date = scheduled_date.isoformat()
            elif scheduled_date is None:
                scheduled_date = None
            
            serialized_diet_content = self._serialize_dates(self.diet_content)
            
            data = {
                'user_id': self.user_id,
                'diet_content': serialized_diet_content,
                'scheduled_date': scheduled_date,
                'status': self.status,
                'completion_date': self.completion_date,
            }
            
            if self.id:
                result = supabase_client.client.table('diet_plans').update(data).eq('id', self.id).execute()
            else:
                result = supabase_client.client.table('diet_plans').insert(data).execute()
            
            if result.data and len(result.data) > 0:
                self.id = result.data[0]['id']
                logger.info(f"Successfully saved diet plan with ID {self.id} for user {self.user_id}")
                return result.data[0]
            
            logger.error(f"No data returned after saving diet plan for user {self.user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error saving diet plan for user {self.user_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def get_today_diet(user_id: int):
        """Get today's diet plan"""
        try:
            today = datetime.now().date().isoformat()
            result = supabase_client.client.table('diet_plans').select('*').eq('user_id', user_id).eq('scheduled_date', today).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching today's diet for user {user_id}: {e}")
            return None

    @staticmethod
    def get_user_diets(user_id: int, limit: int = 10):
        """Get past diet plans"""
        try:
            result = supabase_client.client.table('diet_plans').select('*').eq('user_id', user_id).order('scheduled_date', desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting diet history: {e}")
            return []

class ExerciseCompletion:
    def __init__(self, workout_id: int, exercise_name: str, exercise_index: int, status: str = 'completed'):
        self.workout_id = workout_id
        self.exercise_name = exercise_name
        self.exercise_index = exercise_index
        self.status = status

    @staticmethod
    def create(workout_id: int, exercise_name: str, exercise_index: int, status: str = 'completed'):
        try:
            data = {
                'workout_id': workout_id,
                'exercise_name': exercise_name,
                'exercise_index': exercise_index,
                'status': status,
                'completed_at': datetime.utcnow().isoformat()
            }
            return supabase_client.client.table('exercise_completions').insert(data).execute()
        except Exception as e:
            logger.error(f"Failed to mark exercise {status}: {e}")
            return None

    @staticmethod
    def exists(workout_id: int, exercise_index: int) -> bool:
        try:
            result = supabase_client.client.table('exercise_completions') \
                .select('id') \
                .eq('workout_id', workout_id) \
                .eq('exercise_index', exercise_index).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error checking exercise completion: {e}")
            return False

    @staticmethod
    def get_workout_completions(workout_id: int) -> list:
        """Get all completed/skipped exercises for a workout"""
        try:
            result = supabase_client.client.table('exercise_completions') \
                .select('*') \
                .eq('workout_id', workout_id) \
                .order('exercise_index') \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting workout completions: {e}")
            return []

    @staticmethod
    def get_user_completions(user_id: int) -> list:
        """Get all exercise completions/skips for a user across all workouts"""
        try:
            workouts = Workout.get_user_workouts(user_id)
            workout_ids = [w.id for w in workouts if w.id]
            
            if not workout_ids:
                return []
            
            result = supabase_client.client.table('exercise_completions') \
                .select('*') \
                .in_('workout_id', workout_ids) \
                .order('completed_at', desc=True) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user completions: {e}")
            return []

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