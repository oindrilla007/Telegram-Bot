import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.models import DietPlan, ExerciseCompletion
from src.gemini.gemini_service import GeminiService
from config.config import Config
import json
from config.config import Config
from src.database.models import User, Workout, DietPlan, UserSession
from datetime import datetime,date
from src.database.models import Workout 
from supabase import create_client



logger = logging.getLogger(__name__)

class BotHandlers:
    
    def __init__(self):
        """Initialize handlers with Gemini service"""
        self.gemini_service = GeminiService()
    
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "there"
        
        logger.info(f"User {user_id} started the bot")
        
        # Check if user already exists
        existing_user = User.get_by_user_id(user_id)
        
        if existing_user and existing_user.is_complete_profile():
            # User already has complete profile
            await update.message.reply_text(
                f"Welcome back, {username}! 💪\n\n"
                "I'm your AI-powered fitness assistant. Here's what I can help you with:\n\n"
                "• 🏋️ Daily workout and diet plans (type 'schedule')\n"
                "• ✅ Track exercise completion and skipping\n"
                "• 📊 View your progress and statistics\n"
                "• 💡 Get fitness and nutrition advice\n"
                "• 🎯 Personalized recommendations\n\n"
                "Quick Actions:\n"
                "• Type 'schedule' for today's workout and diet plan\n"
                "• Type 'progress' to view your fitness journey\n"
                "• Ask me any health or fitness questions\n\n"
                "Ready to crush your fitness goals? Let's go! 💪"
            )
            
            # Set session to ACTIVE
            session = UserSession.get_by_user_id(user_id) or UserSession(user_id=user_id)
            session.update_state(Config.States.ACTIVE)
            
        else:
            # New user or incomplete profile
            await update.message.reply_text(
                f"Hey {username}! 👋 Welcome to your AI-powered Workout & Health Bot! 🤖💪\n\n"
                "I'm here to help you achieve your fitness goals with:\n"
                "• 🎯 AI-generated daily workout and diet plans\n"
                "• ✅ Exercise tracking (complete or skip)\n"
                "• 📊 Smart progress monitoring\n"
                "• 💡 Expert fitness and nutrition advice\n"
                "• 🏆 Adaptive recommendations\n\n"
                "To get started, I'll need to know a bit about you. This helps my AI create the perfect workout plan tailored just for you!\n\n"
                "Let's begin! What's your age? 🎂"
            )
            
            # Create or update session
            session = UserSession.get_by_user_id(user_id) or UserSession(user_id=user_id)
            session.update_state(Config.States.COLLECTING_AGE)
    
    @staticmethod
    async def handle_age_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle age input during onboarding"""
        user_id = update.effective_user.id
        age_text = update.message.text.strip()
        
        try:
            age = int(age_text)
            if age < 13 or age > 100:
                await update.message.reply_text(
                    "Please enter a valid age between 13 and 100 years. 🤔"
                )
                return
            
            # Save age to session temp data
            session = UserSession.get_by_user_id(user_id)
            session.update_state(Config.States.COLLECTING_HEIGHT, {"age": age})
            
            await update.message.reply_text(
                f"Great! You're {age} years old. 👍\n\n"
                "Now, what's your height in centimeters? (e.g., 175) 📏"
            )
            
        except ValueError:
            await update.message.reply_text(
                "Please enter your age as a number (e.g., 25). 🔢"
            )
    
    @staticmethod
    async def handle_height_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle height input during onboarding"""
        user_id = update.effective_user.id
        height_text = update.message.text.strip()
        
        try:
            height = float(height_text)
            if height < 100 or height > 250:
                await update.message.reply_text(
                    "Please enter a valid height between 100 and 250 cm. 📏"
                )
                return
            
            # Save height to session temp data
            session = UserSession.get_by_user_id(user_id)
            temp_data = session.temp_data.copy()
            temp_data["height"] = height
            session.update_state(Config.States.COLLECTING_WEIGHT, temp_data)
            
            await update.message.reply_text(
                f"Perfect! Your height is {height} cm. 📐\n\n"
                "What's your weight in kilograms? (e.g., 70) ⚖️"
            )
            
        except ValueError:
            await update.message.reply_text(
                "Please enter your height as a number (e.g., 175). 🔢"
            )
    
    @staticmethod
    async def handle_weight_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle weight input during onboarding"""
        user_id = update.effective_user.id
        weight_text = update.message.text.strip()
        
        try:
            weight = float(weight_text)
            if weight < 30 or weight > 300:
                await update.message.reply_text(
                    "Please enter a valid weight between 30 and 300 kg. ⚖️"
                )
                return
            
            # Save weight and move to fitness level
            session = UserSession.get_by_user_id(user_id)
            temp_data = session.temp_data.copy()
            temp_data["weight"] = weight
            session.update_state(Config.States.COLLECTING_LEVEL, temp_data)
            
            # Create fitness level keyboard
            keyboard = [
                [InlineKeyboardButton("🟢 Beginner", callback_data="level_beginner")],
                [InlineKeyboardButton("🟡 Intermediate", callback_data="level_intermediate")],
                [InlineKeyboardButton("🔴 Advanced", callback_data="level_advanced")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Excellent! Your weight is {weight} kg. 💪\n\n"
                "What's your current fitness level? Choose the option that best describes you:\n\n"
                "🟢 **Beginner**: New to working out or getting back into fitness\n"
                "🟡 **Intermediate**: Regular exercise, comfortable with basic movements\n"
                "🔴 **Advanced**: Experienced with complex exercises and training",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "Please enter your weight as a number (e.g., 70). 🔢"
            )
    
    @staticmethod
    async def handle_fitness_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle fitness level selection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        level = query.data.split("_")[1]  # Extract level from callback_data
        
        # Save fitness level and move to goals
        session = UserSession.get_by_user_id(user_id)
        temp_data = session.temp_data.copy()
        temp_data["fitness_level"] = level
        session.update_state(Config.States.COLLECTING_GOALS, temp_data)
        
        level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
        
        await query.edit_message_text(
            f"Great choice! You selected {level_emoji[level]} **{level.title()}** level.\n\n"
            "Finally, what are your main fitness goals? Please describe what you want to achieve:\n\n"
            "Examples:\n"
            "• Build muscle and get stronger 💪\n"
            "• Lose weight and tone up 🔥\n" 
            "• Improve endurance and stamina 🏃\n"
            "• General fitness and health 🌟\n"
            "• Prepare for sports/activities 🏐\n\n"
            "Feel free to be specific about what you want to accomplish!",
            parse_mode='Markdown'
        )
    
    @staticmethod
    async def handle_goals_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle goals input and complete onboarding"""
        user_id = update.effective_user.id
        goals = update.message.text.strip()
        
        if len(goals) < 10:
            await update.message.reply_text(
                "Please provide a bit more detail about your goals (at least 10 characters). "
                "This helps my AI create better workout plans for you! 🎯"
            )
            return
        
        # Get session data and create user profile
        session = UserSession.get_by_user_id(user_id)
        temp_data = session.temp_data
        
        # Create or update user with complete profile
        user = User.get_by_user_id(user_id) or User(user_id=user_id)
        user.age = temp_data["age"]
        user.height = temp_data["height"]
        user.weight = temp_data["weight"]
        user.fitness_level = temp_data["fitness_level"]
        user.goals = goals
        
        result = user.save()
        
        if result:
            # Update session to ACTIVE and clear temp data
            session.update_state(Config.States.ACTIVE, {})
            
            await update.message.reply_text(
                "🎉 **Profile Complete!**\n\n"
                f"Here's your fitness profile:\n"
                f"👤 Age: {user.age} years\n"
                f"📏 Height: {user.height} cm\n"
                f"⚖️ Weight: {user.weight} kg\n"
                f"💪 Level: {user.fitness_level.title()}\n"
                f"🎯 Goals: {user.goals}\n\n"
                "Perfect! My AI is now ready to help you achieve your fitness goals! 🤖🚀\n\n"
                "Quick Actions:\n"
                "• Type 'schedule' to get your daily workout and diet plan\n"
                "• Type 'progress' to track your fitness journey\n"
                "• Ask me any fitness or nutrition questions\n\n"
                "You can mark exercises as completed (✅) or skipped (⏭️), and I'll track your progress!\n\n"
                "Ready to start your fitness journey? Type 'schedule' for your first workout! 💪",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your profile. Please try again or contact support."
            )
    
    async def handle_workout_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle workout generation request with AI"""
        user_id = update.effective_user.id
        
        # Check if user has complete profile
        user = User.get_by_user_id(user_id)
        if not user or not user.is_complete_profile():
            await update.message.reply_text(
                "Please complete your profile first by using /start command! 📝"
            )
            return
        
        # Show generating message
        generating_msg = await update.message.reply_text(
            "🤖 AI is analyzing your profile...\n"
            "⚡ Generating your personalized workout plan...\n"
            "📊 This may take a few seconds..."
        )
        
        try:
            # Update session state
            session = UserSession.get_by_user_id(user_id) or UserSession(user_id=user_id)
            session.update_state(Config.States.WORKOUT_GENERATION)
            
            # Prepare user profile for AI
            user_profile = {
                'age': user.age,
                'height': user.height,
                'weight': user.weight,
                'fitness_level': user.fitness_level,
                'goals': user.goals
            }
            
            # Get workout history for context
            recent_workouts = Workout.get_user_workouts(user_id, limit=3)
            workout_history = []
            for workout in recent_workouts:
                if workout.workout_content:
                    workout_history.append({
                        'workout_type': workout.workout_content.get('workout_type', 'General'),
                        'completion_date': workout.completion_date,
                        'status': workout.status
                    })
            
            # Generate workout using AI
            workout_data = self.gemini_service.generate_workout(user_profile, workout_history)
            
            # Save workout to database
            new_workout = Workout(
                user_id=user_id,
                workout_content=workout_data,
                status='generated'
            )
            saved_workout = new_workout.save()
            
            if saved_workout:
                # Delete generating message
                await generating_msg.delete()
                
                # Format and send the workout
                await self.send_formatted_workout(update, workout_data, saved_workout['id'])
                
                # Update session back to ACTIVE
                session.update_state(Config.States.ACTIVE)
                
            else:
                await generating_msg.edit_text(
                    "❌ Sorry, there was an error saving your workout. Please try again."
                )
        
        except Exception as e:
            logger.error(f"Error generating workout for user {user_id}: {e}")
            await generating_msg.edit_text(
                "❌ Sorry, I encountered an error while generating your workout. Please try again in a moment."
            )
            
            # Reset session state
            session = UserSession.get_by_user_id(user_id)
            if session:
                session.update_state(Config.States.ACTIVE)

    async def handle_schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate today's workout and diet, store and send combined plan"""
        user_id = update.effective_user.id
        user = User.get_by_user_id(user_id)

        if not user or not user.is_complete_profile():
            await update.message.reply_text("Please complete your profile first using /start.")
            return

        # Get user session and set to SCHEDULE_GENERATION
        session = UserSession.get_by_user_id(user_id)
        if session:
            session.update_state(Config.States.SCHEDULE_GENERATION)

        # Notify user
        await update.message.reply_text("🧠 Generating today's workout and diet plan...")

        # Build profile
        user_profile = {
            'age': user.age,
            'height': user.height,
            'weight': user.weight,
            'fitness_level': user.fitness_level,
            'goals': user.goals
        }

        # Get workout history
        recent_workouts = Workout.get_user_workouts(user_id, limit=3)
        workout_history = [w.workout_content for w in recent_workouts if w.workout_content]

        # Generate workout
        workout_data = self.gemini_service.generate_workout(user_profile, workout_history)

        # Generate diet
        diet_data = self.gemini_service.generate_diet_plan(user_profile)

        # Save workout
        new_workout = Workout(
            user_id=user_id,
            workout_content=workout_data,
            status='scheduled',
            scheduled_date=date.today(),
            total_exercises=len(workout_data.get('exercises', []))
        )
        saved_workout = new_workout.save()

        if not saved_workout:
            logger.error(f"Failed to save workout for user {user_id}")
            await update.message.reply_text("❌ Error saving workout. Please try again.")
            if session:
                session.update_state(Config.States.ACTIVE)
            return

        # Save diet
        new_diet = DietPlan(
            user_id=user_id,
            diet_content=diet_data,
            scheduled_date=date.today().isoformat(),
            status='scheduled'
        )
        saved_diet = new_diet.save()

        if not saved_diet:
            logger.error(f"Failed to save diet plan for user {user_id}")
            await update.message.reply_text("❌ Error saving diet plan. Please try again.")
            if session:
                session.update_state(Config.States.ACTIVE)
            return

        # Format and send message
        await self.send_formatted_workout(update, workout_data, saved_workout['id'], show_per_exercise_buttons=True)
        
        # Format and send diet plan
        diet_message = "🍽️ **Today's Diet Plan**\n\n"
        
        # Add meals
        if 'meals' in diet_data:
            for meal in diet_data['meals']:
                diet_message += f"**{meal['name']}** ({meal['time']})\n"
                for item in meal['items']:
                    diet_message += f"• {item['name']} - {item['portion']} ({item['calories']} cal)\n"
                diet_message += f"Total: {meal['total_calories']} calories\n\n"
        
        # Add snacks
        if 'snacks' in diet_data and diet_data['snacks']:
            diet_message += "**Snacks**\n"
            for snack in diet_data['snacks']:
                diet_message += f"**{snack['time']}**\n"
                for item in snack['items']:
                    diet_message += f"• {item['name']} - {item['portion']} ({item['calories']} cal)\n"
                diet_message += f"Total: {snack['total_calories']} calories\n\n"
        
        # Add hydration
        if 'hydration' in diet_data:
            diet_message += "**Hydration**\n"
            diet_message += f"• {diet_data['hydration']['water']}\n"
            if diet_data['hydration'].get('other_beverages'):
                for beverage in diet_data['hydration']['other_beverages']:
                    diet_message += f"• {beverage}\n"
            diet_message += "\n"
        
        # Add nutritional summary
        if 'nutritional_summary' in diet_data:
            diet_message += "**Nutritional Summary**\n"
            for nutrient, amount in diet_data['nutritional_summary'].items():
                diet_message += f"• {nutrient.title()}: {amount}\n"
            diet_message += "\n"
        
        # Add notes
        if 'notes' in diet_data:
            diet_message += "**Notes**\n"
            for note in diet_data['notes']:
                diet_message += f"• {note}\n"
        
        # Add total calories
        if 'total_calories' in diet_data:
            diet_message += f"\n**Total Daily Calories: {diet_data['total_calories']}**"
        
        # Create keyboard for diet plan with both complete and skip buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Mark Complete", callback_data=f"diet_complete_{saved_diet['id']}"),
                InlineKeyboardButton("⏭️ Skip Diet", callback_data=f"diet_skip_{saved_diet['id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the formatted diet plan
        await update.message.reply_text(diet_message, parse_mode='Markdown', reply_markup=reply_markup)

        # Reset session state back to ACTIVE
        if session:
            session.update_state(Config.States.ACTIVE)
    
    async def send_formatted_workout(self, update, workout_data, workout_id, show_per_exercise_buttons=False):
        """Send beautifully formatted workout to user"""
        try:
            # Header
            header = f"🤖 AI-Generated Workout Plan\n"
            header += f"💪 {workout_data.get('workout_type', 'Custom')} Workout\n"
            header += f"⏱️ Duration: {workout_data.get('duration_minutes', 30)} minutes\n"
            header += f"📊 Difficulty: {workout_data.get('difficulty', 'Moderate')}\n"
            header += f"🔥 Est. Calories: {workout_data.get('calories_estimate', 'N/A')}\n\n"
            
            # Warm-up section
            warmup_text = "🔥 WARM-UP (5 minutes)\n"
            if 'warmup' in workout_data:
                for i, exercise in enumerate(workout_data['warmup'], 1):
                    warmup_text += f"{i}. {exercise['name']} - {exercise['duration_seconds']}s\n"
                    warmup_text += f"   ▪️ {exercise['instructions']}\n\n"
            
            # Main workout section
            main_text = "💪 MAIN WORKOUT\n"
            exercise_buttons = []

            if 'exercises' in workout_data:
                for i, exercise in enumerate(workout_data['exercises']):
                    idx = i + 1
                    main_text += f"{idx}. **{exercise['name']}** ({exercise.get('type', 'exercise')})\n"
                    main_text += f"   🔢 {exercise.get('sets', 3)} sets × {exercise.get('reps', '10-12')} reps\n"
                    main_text += f"   ⏱️ Rest: {exercise.get('rest_seconds', 60)}s\n"
                    main_text += f"   📝 {exercise.get('instructions', 'Perform exercise')}\n"
                    if exercise.get('modifications'):
                        main_text += f"   💡 Modifications: {exercise['modifications']}\n"
                    main_text += f"\n"

                    # Add exercise completion and skip buttons
                    exercise_buttons.append([
                        InlineKeyboardButton(
                            f"✅ Complete {idx}",
                            callback_data=f"exercise_done_{workout_id}_{i}"
                        ),
                        InlineKeyboardButton(
                            f"⏭️ Skip {idx}",
                            callback_data=f"exercise_skip_{workout_id}_{i}"
                        )
                    ])
            
            # Cool-down section
            cooldown_text = "🧘 COOL-DOWN (5 minutes)\n"
            if 'cooldown' in workout_data:
                for i, exercise in enumerate(workout_data['cooldown'], 1):
                    cooldown_text += f"{i}. {exercise['name']} - {exercise['duration_seconds']}s\n"
                    cooldown_text += f"   ▪️ {exercise['instructions']}\n\n"
            
            # Tips section
            tips_text = "💡 AI TRAINER TIPS\n"
            if 'tips' in workout_data:
                for tip in workout_data['tips']:
                    tips_text += f"• {tip}\n"
            
            # Create keyboard with exercise buttons
            reply_markup = InlineKeyboardMarkup(exercise_buttons)
            
            # Send the formatted workout (split into multiple messages if too long)
            full_message = header + warmup_text + main_text + cooldown_text + tips_text
            
            if len(full_message) > 4096:
                await update.message.reply_text(header + warmup_text, parse_mode='Markdown')
                await update.message.reply_text(main_text, parse_mode='Markdown')
                await update.message.reply_text(cooldown_text + tips_text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await update.message.reply_text(full_message, parse_mode='Markdown', reply_markup=reply_markup)
        
        except Exception as e:
            logger.error(f"Error formatting workout: {e}")
            await update.message.reply_text(
                f"🤖 **Your AI Workout is Ready!**\n\n"
                f"Workout Type: {workout_data.get('workout_type', 'Custom')}\n"
                f"Duration: {workout_data.get('duration_minutes', 30)} minutes\n"
                f"Exercises: {len(workout_data.get('exercises', []))}\n\n"
                "There was an issue formatting the detailed view. The workout has been saved to your history!",
                reply_markup=reply_markup
            )
    
    async def handle_fitness_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle fitness and nutrition related questions"""
        try:
            question = update.message.text
            user_id = update.effective_user.id
            
            # Get user profile for personalized answers
            user = User.get_by_user_id(user_id)
            user_profile = {
                'age': user.age if user else None,
                'height': user.height if user else None,
                'weight': user.weight if user else None,
                'fitness_level': user.fitness_level if user else None,
                'goals': user.goals if user else None
            } if user else None
            
            # Get answer from Gemini
            answer = self.gemini_service.answer_fitness_question(question, user_profile)
            
            # Create keyboard with only Ask Another button
            keyboard = [[InlineKeyboardButton("❓ Ask Another Question", callback_data="ask_question")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(answer, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error answering fitness question: {e}", exc_info=True)
            await update.message.reply_text("❌ Sorry, I couldn't process your question. Please try again.")
    
    @staticmethod
    async def handle_workout_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle workout completion callback"""
        query = update.callback_query
        await query.answer()
        
        workout_id = int(query.data.split("_")[1])
        user_id = query.from_user.id
        
        # Get and update workout
        workouts = Workout.get_user_workouts(user_id, limit=20)
        target_workout = None
        for workout in workouts:
            if workout.id == workout_id:
                target_workout = workout
                break
        
        if target_workout:
            target_workout.mark_completed()
            
            await query.edit_message_text(
                f"🎉 **Workout Completed!** 💪\n\n"
                f"Great job finishing your {target_workout.workout_content.get('workout_type', 'workout')}!\n"
                f"You burned approximately {target_workout.workout_content.get('calories_estimate', 200)} calories.\n\n"
                f"🏆 Keep up the amazing work! Your consistency is building strength and discipline.\n\n"
                f"Ready for your next challenge? Type 'workout' for another AI-generated plan!"
            )
        else:
            await query.edit_message_text("❌ Workout not found. Please try again.")

    async def handle_exercise_completion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle single exercise completion or skip"""
        query = update.callback_query
        await query.answer()
        
        data = query.data  # format: exercise_done_{workoutId}_{index} or exercise_skip_{workoutId}_{index}
        
        try:
            # Parse the callback data correctly
            parts = data.split("_")
            if len(parts) != 4 or parts[0] != "exercise" or parts[1] not in ["done", "skip"]:
                logger.error(f"Invalid callback data format: {data}")
                await query.answer("❌ Invalid exercise completion request.", show_alert=True)
                return
            
            action = parts[1]  # 'done' or 'skip'
            workout_id = int(parts[2])
            index = int(parts[3])
            user_id = query.from_user.id
            
            # Set status based on action
            status = 'completed' if action == 'done' else 'skipped'
            status_emoji = "✅" if status == 'completed' else "⏭️"

            # Get the workout
            workouts = Workout.get_user_workouts(user_id, limit=10)
            workout = next((w for w in workouts if w.id == workout_id), None)
            if not workout or workout.user_id != user_id:
                await query.edit_message_text("❌ Workout not found.")
                return

            # Check if exercise was already completed/skipped
            if ExerciseCompletion.exists(workout_id, index):
                await query.answer(f"⚠️ This exercise was already marked as {status}.", show_alert=True)
                return

            # Get exercise name from workout content
            exercise_name = workout.workout_content['exercises'][index]['name']

            # Record this completion/skip
            completion_result = ExerciseCompletion.create(
                workout_id=workout_id,
                exercise_index=index,
                exercise_name=exercise_name,
                status=status
            )

            if not completion_result:
                await query.answer(f"❌ Error saving exercise {status}.", show_alert=True)
                return

            # Refresh the completion counts from the database
            workout.refresh_completion_count()

            # Update the message to show progress
            message = query.message.text
            lines = message.split('\n')
            
            # Find the exercise line and mark it as completed/skipped
            for i, line in enumerate(lines):
                if line.startswith(f"{index + 1}.") and "**" in line:
                    # Add ✅ or ⏭️ to the exercise name
                    exercise_name = line.split("**")[1]
                    lines[i] = line.replace(exercise_name, f"{exercise_name} {status_emoji}")
                    break

            # Add completion/skip status with detailed progress
            status_text = "completed" if status == 'completed' else "skipped"
            completion_status = f"\n\n{status_emoji} Exercise {index + 1} {status_text}!\n"
            completion_status += f"📊 Progress: {workout.exercises_completed} completed, {workout.skipped_exercises} skipped out of {workout.total_exercises} exercises"
            
            # Add workout status if all exercises are done
            if workout.exercises_completed + workout.skipped_exercises >= workout.total_exercises:
                if workout.status == "skipped":
                    completion_status += "\n⏭️ Workout marked as skipped (all exercises skipped)"
                else:
                    completion_status += f"\n🎉 Workout marked as completed ({workout.exercises_completed} exercises completed)"
            
            # Update the message
            updated_message = '\n'.join(lines) + completion_status
            
            # Create updated keyboard
            keyboard = query.message.reply_markup.inline_keyboard
            # Remove the completed/skipped exercise buttons
            keyboard = [row for row in keyboard if not any(
                btn.callback_data in [f"exercise_done_{workout_id}_{index}", f"exercise_skip_{workout_id}_{index}"] 
                for btn in row
            )]
            
            # If all exercises are done, update the completion button
            if workout.exercises_completed + workout.skipped_exercises >= workout.total_exercises:
                if workout.status == "skipped":
                    keyboard = [[
                        InlineKeyboardButton("⏭️ Workout Skipped", callback_data=f"complete_{workout_id}")
                    ]]
                else:
                    keyboard = [[
                        InlineKeyboardButton(f"🎉 Workout Complete ({workout.exercises_completed}/{workout.total_exercises})", 
                                           callback_data=f"complete_{workout_id}")
                    ]]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Update the message
            await query.edit_message_text(
                text=updated_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in handle_exercise_completion: {e}", exc_info=True)
            await query.answer(f"❌ Error marking exercise as {status}.", show_alert=True)
    
    @staticmethod
    async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle general messages based on user state"""
        user_id = update.effective_user.id
        message_text = update.message.text.lower().strip()

        def is_greeting(msg):
            greetings = ["hi", "hello", "hey", "yo", "good morning", "good evening", "good afternoon"]
            return any(msg == g or msg.startswith(g + " ") for g in greetings)

        def is_direct_workout_request(msg):
            direct_phrases = [
                "workout", "generate workout", "start workout", "give me a workout", "new workout", "workout plan", "exercise plan", "exercise routine"
            ]
            return msg in direct_phrases or any(msg.startswith(phrase + " ") for phrase in direct_phrases)

        # Get user session to determine current state
        session = UserSession.get_by_user_id(user_id)

        if not session:
            # No session exists, treat as new user
            await BotHandlers.start_command(update, context)
            return

        state = session.conversation_state

        # Create handlers instance for AI methods
        handlers = BotHandlers()

        # Handle messages based on current state
        if state == Config.States.COLLECTING_AGE:
            await BotHandlers.handle_age_collection(update, context)
        elif state == Config.States.COLLECTING_HEIGHT:
            await BotHandlers.handle_height_collection(update, context)
        elif state == Config.States.COLLECTING_WEIGHT:
            await BotHandlers.handle_weight_collection(update, context)
        elif state == Config.States.COLLECTING_GOALS:
            await BotHandlers.handle_goals_collection(update, context)
        elif state == Config.States.ACTIVE:
            # User is active, handle various requests
            if "schedule" in message_text or "today" in message_text:
                await handlers.handle_schedule_command(update, context)

            elif any(word in message_text for word in ['progress', 'history', 'stats']):
                await BotHandlers.handle_progress_request(update, context)
            else:
                # For greetings, do not include profile in Q&A prompt
                if is_greeting(message_text):
                    await update.message.reply_text(
                        "👋 Hi! How can I help you with your fitness journey today?\n\nYou can ask me anything about workouts, nutrition, or progress!"
                    )
                else:
                    await handlers.handle_fitness_question(update, context)
        else:
            # Unknown state, reset to start
            await BotHandlers.start_command(update, context)
    
    @staticmethod
    async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle various callback queries"""
        query = update.callback_query
        data = query.data
        
        handlers = BotHandlers()
        
        if data.startswith("level_"):
            await BotHandlers.handle_fitness_level(update, context)
        elif data.startswith("complete_"):
            await BotHandlers.handle_workout_completion(update, context)
        elif data.startswith("diet_complete_"):
            await BotHandlers.handle_diet_completion(update, context)
        elif data == "new_workout":
            await query.answer()
            # Simulate workout request
            await handlers.handle_workout_request(update, context)
        elif data == "show_stats":
            await query.answer()
            try:
                # Get user ID from the callback query
                user_id = query.from_user.id
                
                # Get recent workouts and diet plans
                workouts = Workout.get_user_workouts(user_id, limit=30)
                diet_plans = DietPlan.get_user_diets(user_id, limit=30)
                
                # Get all exercise completions for the user
                all_completions = ExerciseCompletion.get_user_completions(user_id)
                total_completed_exercises = len([c for c in all_completions if c.get('status') == 'completed'])
                total_skipped_exercises = len([c for c in all_completions if c.get('status') == 'skipped'])

                # Calculate overall statistics
                total_workouts = len(workouts)
                completed_workouts = len([w for w in workouts if w.status == "completed"])
                skipped_workouts = len([w for w in workouts if w.status == "skipped"])
                total_exercises = sum(w.total_exercises or 0 for w in workouts)
                total_diets = len(diet_plans)
                completed_diets = len([d for d in diet_plans if d.get('status') == "completed"])
                skipped_diets = len([d for d in diet_plans if d.get('status') == "skipped"])

                # Calculate completion percentages
                workout_completion = ((completed_workouts + skipped_workouts)/total_workouts)*100 if total_workouts else 0
                exercise_completion = ((total_completed_exercises + total_skipped_exercises)/total_exercises)*100 if total_exercises else 0
                diet_completion = ((completed_diets + skipped_diets)/total_diets)*100 if total_diets else 0

                # Build the progress message
                message = "📊 **Your Fitness Progress Report**\n\n"

                # Overall Statistics
                message += "🎯 **Overall Statistics**\n"
                message += f"• Total Workouts: {total_workouts}\n"
                message += f"• Completed Workouts: {completed_workouts} ({workout_completion:.1f}%)\n"
                message += f"• Skipped Workouts: {skipped_workouts}\n"
                message += f"• Total Exercises: {total_exercises}\n"
                message += f"• Completed Exercises: {total_completed_exercises} ({exercise_completion:.1f}%)\n"
                message += f"• Skipped Exercises: {total_skipped_exercises}\n"
                message += f"• Diet Plans Followed: {completed_diets}/{total_diets} ({diet_completion:.1f}%)\n"
                message += f"• Skipped Diet Plans: {skipped_diets}\n\n"

                # Recent Activity
                message += "📅 **Recent Activity (Last 5 Days)**\n"
                recent_workouts = sorted(workouts, 
                                      key=lambda x: x.scheduled_date or x.created_date, 
                                      reverse=True)[:5]
                
                for workout in recent_workouts:
                    date_str = workout.scheduled_date or workout.created_date
                    if isinstance(date_str, str):
                        date_str = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                    elif isinstance(date_str, datetime):
                        date_str = date_str.date()
                    
                    status_emoji = "✅" if workout.status == "completed" else "⏭️" if workout.status == "skipped" else "⏳"
                    workout_type = workout.workout_content.get('workout_type', 'Workout') if workout.workout_content else 'Workout'
                    
                    # Get exercise completion for this workout
                    workout_completions = ExerciseCompletion.get_workout_completions(workout.id)
                    exercises_done = len([c for c in workout_completions if c.get('status') == 'completed'])
                    exercises_skipped = len([c for c in workout_completions if c.get('status') == 'skipped'])
                    total_exercises = workout.total_exercises or 0
                    exercise_status = f"({exercises_done} completed, {exercises_skipped} skipped out of {total_exercises} exercises)"
                    
                    message += f"{status_emoji} {date_str} - {workout_type} {exercise_status}\n"
                    
                    # Add exercise details if workout has any completed/skipped exercises
                    if workout_completions:
                        message += "   └─ Exercises:\n"
                        for ex in workout_completions:
                            status_emoji = "✅" if ex.get('status') == 'completed' else "⏭️"
                            message += f"      {status_emoji} {ex.get('exercise_name', 'Unknown Exercise')}\n"
                    message += "\n"

                # Muscle Group Distribution
                message += "💪 **Muscle Group Distribution**\n"
                muscle_groups = {}
                for workout in workouts:
                    if workout.workout_content and 'workout_type' in workout.workout_content:
                        muscle_group = workout.workout_content['workout_type']
                        muscle_groups[muscle_group] = muscle_groups.get(muscle_group, 0) + 1
                
                for muscle_group, count in sorted(muscle_groups.items(), key=lambda x: x[1], reverse=True):
                    message += f"• {muscle_group}: {count} workouts\n"

                # Send message without any keyboard buttons
                await query.message.reply_text(message, parse_mode='Markdown')

            except Exception as e:
                logger.error(f"Error showing progress stats: {e}", exc_info=True)
                await query.message.reply_text("❌ Sorry, there was an error retrieving your progress. Please try again later.")
        elif data == "ask_question":
            await query.answer()
            await query.message.reply_text(
                "🤖 How can I help you today?\n\n"
                "Here are some things you can do:\n"
                "• Type schedule to get your complete daily plan\n"
                "• Type progress to track your fitness journey\n"
                "• Ask me any health, fitness, or diet questions\n"
                "• Type /help to see all available commands\n\n"
                "What would you like to know? 💪"
            )
        elif data.startswith("notes_"):
            await query.answer()
            await query.message.reply_text("📝 Please send your notes for this workout. (Feature coming soon!)")
        else:
            await query.answer("Unknown action")
    
    @staticmethod
    async def handle_diet_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle diet plan completion or skip"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Log the full callback data for debugging
            logger.info(f"Diet completion callback data: {query.data}")
            
            # Split the callback data and validate format
            parts = query.data.split("_")
            if len(parts) != 3 or parts[0] != "diet" or parts[1] not in ["complete", "skip"]:
                logger.error(f"Invalid callback data format: {query.data}")
                await query.answer("❌ Invalid diet completion request.", show_alert=True)
                return
            
            action = parts[1]  # 'complete' or 'skip'
            status = 'completed' if action == 'complete' else 'skipped'
            
            # Try to parse the diet ID
            try:
                diet_id = int(parts[2])
            except ValueError as e:
                logger.error(f"Invalid diet ID in callback data: {parts[2]}")
                await query.answer("❌ Invalid diet ID.", show_alert=True)
                return
            
            user_id = query.from_user.id
            logger.info(f"Processing diet {action} for user {user_id}, diet {diet_id}")
            
            # Get the diet plan using DietPlan methods
            user_diets = DietPlan.get_user_diets(user_id, limit=10)  # Get recent diets
            diet_data = next((d for d in user_diets if d.get('id') == diet_id), None)
            
            if not diet_data:
                logger.error(f"Diet plan not found: id={diet_id}, user_id={user_id}")
                await query.edit_message_text("❌ Diet plan not found.")
                return
            
            logger.info(f"Found diet plan: {diet_data}")
            
            # Create diet plan object with completion/skip status
            diet = DietPlan(
                user_id=user_id,
                diet_content=diet_data['diet_content'],
                scheduled_date=diet_data['scheduled_date'],
                status=status,
                id=diet_id,
                created_date=diet_data.get('created_date'),
                completion_date=datetime.now().date().isoformat()
            )
            
            # Save the updated diet plan
            saved_result = diet.save()
            if saved_result:
                logger.info(f"Successfully marked diet {diet_id} as {status}")
                # Update the message to show completion/skip
                message = query.message.text
                status_emoji = "✅" if status == 'completed' else "⏭️"
                status_text = "completed" if status == 'completed' else "skipped"
                message += f"\n\n{status_emoji} **Diet Plan {status_text.title()}!**\n\n"
                
                if status == 'completed':
                    message += "Great job following your nutrition plan! Keep up the healthy eating habits! 💪\n\n"
                else:
                    message += "Diet plan marked as skipped. Remember to maintain a balanced diet! 🥗\n\n"
                
                message += "Would you like to view your progress?"
                
                # Update keyboard with only view progress button
                keyboard = [[
                    InlineKeyboardButton("📊 View Progress", callback_data="show_stats")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                logger.error(f"Failed to save diet {action} for diet {diet_id}")
                await query.answer(f"❌ Error saving diet {action}.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error in handle_diet_completion: {e}", exc_info=True)
            await query.answer(f"❌ Error marking diet as {status}.", show_alert=True)
    
    @staticmethod
    async def handle_progress_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /progress command to show user's fitness progress"""
        try:
            user_id = update.effective_user.id
            
            # Get recent workouts and diet plans
            workouts = Workout.get_user_workouts(user_id, limit=30)
            diet_plans = DietPlan.get_user_diets(user_id, limit=30)
            
            # Get all exercise completions for the user
            all_completions = ExerciseCompletion.get_user_completions(user_id)
            total_completed_exercises = len([c for c in all_completions if c.get('status') == 'completed'])
            total_skipped_exercises = len([c for c in all_completions if c.get('status') == 'skipped'])

            # Calculate overall statistics
            total_workouts = len(workouts)
            completed_workouts = len([w for w in workouts if w.status == "completed"])
            skipped_workouts = len([w for w in workouts if w.status == "skipped"])
            total_exercises = sum(w.total_exercises or 0 for w in workouts)
            total_diets = len(diet_plans)
            completed_diets = len([d for d in diet_plans if d.get('status') == "completed"])
            skipped_diets = len([d for d in diet_plans if d.get('status') == "skipped"])

            # Calculate completion percentages
            workout_completion = ((completed_workouts + skipped_workouts)/total_workouts)*100 if total_workouts else 0
            exercise_completion = ((total_completed_exercises + total_skipped_exercises)/total_exercises)*100 if total_exercises else 0
            diet_completion = ((completed_diets + skipped_diets)/total_diets)*100 if total_diets else 0

            # Build the progress message
            message = "📊 **Your Fitness Progress Report**\n\n"

            # Overall Statistics
            message += "🎯 **Overall Statistics**\n"
            message += f"• Total Workouts: {total_workouts}\n"
            message += f"• Completed Workouts: {completed_workouts} ({workout_completion:.1f}%)\n"
            message += f"• Skipped Workouts: {skipped_workouts}\n"
            message += f"• Total Exercises: {total_exercises}\n"
            message += f"• Completed Exercises: {total_completed_exercises} ({exercise_completion:.1f}%)\n"
            message += f"• Skipped Exercises: {total_skipped_exercises}\n"
            message += f"• Diet Plans Followed: {completed_diets}/{total_diets} ({diet_completion:.1f}%)\n"
            message += f"• Skipped Diet Plans: {skipped_diets}\n\n"

            # Recent Activity
            message += "📅 **Recent Activity (Last 5 Days)**\n"
            recent_workouts = sorted(workouts, 
                                  key=lambda x: x.scheduled_date or x.created_date, 
                                  reverse=True)[:5]
            
            for workout in recent_workouts:
                date_str = workout.scheduled_date or workout.created_date
                if isinstance(date_str, str):
                    date_str = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                elif isinstance(date_str, datetime):
                    date_str = date_str.date()
                
                status_emoji = "✅" if workout.status == "completed" else "⏭️" if workout.status == "skipped" else "⏳"
                workout_type = workout.workout_content.get('workout_type', 'Workout') if workout.workout_content else 'Workout'
                
                # Get exercise completion for this workout
                workout_completions = ExerciseCompletion.get_workout_completions(workout.id)
                exercises_done = len([c for c in workout_completions if c.get('status') == 'completed'])
                exercises_skipped = len([c for c in workout_completions if c.get('status') == 'skipped'])
                total_exercises = workout.total_exercises or 0
                exercise_status = f"({exercises_done} completed, {exercises_skipped} skipped out of {total_exercises} exercises)"
                
                message += f"{status_emoji} {date_str} - {workout_type} {exercise_status}\n"
                
                # Add exercise details if workout has any completed/skipped exercises
                if workout_completions:
                    message += "   └─ Exercises:\n"
                    for ex in workout_completions:
                        status_emoji = "✅" if ex.get('status') == 'completed' else "⏭️"
                        message += f"      {status_emoji} {ex.get('exercise_name', 'Unknown Exercise')}\n"
                message += "\n"

            # Muscle Group Distribution
            message += "💪 **Muscle Group Distribution**\n"
            muscle_groups = {}
            for workout in workouts:
                if workout.workout_content and 'workout_type' in workout.workout_content:
                    muscle_group = workout.workout_content['workout_type']
                    muscle_groups[muscle_group] = muscle_groups.get(muscle_group, 0) + 1
            
            for muscle_group, count in sorted(muscle_groups.items(), key=lambda x: x[1], reverse=True):
                message += f"• {muscle_group}: {count} workouts\n"

            # Create keyboard with only the Ask Question button
            keyboard = [[InlineKeyboardButton("❓ Ask Question", callback_data="ask_question")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing progress: {e}", exc_info=True)
            await update.message.reply_text("❌ Sorry, there was an error retrieving your progress. Please try again later.")
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 AI Workout Bot Help\n\n"

            "What I can do:\n"
            "• 💪 Generate personalized workouts with exercise completion tracking\n"
            "• 🥗 Create daily diet plans\n"
            "• 📊 Track your workout and diet progress\n"
            "• 💡 Answer your health, fitness, and nutrition questions\n\n"
            "Quick Actions:\n"
            "• Type 'schedule' to get your daily workout and diet plan\n"
            "• Type 'progress' to view your fitness journey stats\n"
            "• Ask me any health or fitness questions\n\n"
            "Examples:\n"
            "• 'What foods help with muscle recovery?'\n"
            "• 'How can I improve my workout form?'\n"
            "• 'What's a good pre-workout meal?'\n\n"
            "I'm here to help you achieve your fitness goals! 💪🤖"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong with my AI systems. Please try again or use /start to restart."
            )