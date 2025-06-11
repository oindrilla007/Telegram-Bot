import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.models import User, UserSession, Workout
from config.config import Config

logger = logging.getLogger(__name__)

class BotHandlers:
    
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
                "I'm your personal workout assistant. Here's what I can help you with:\n"
                "• Generate personalized workouts\n"
                "• Answer fitness and nutrition questions\n"
                "• Track your workout progress\n\n"
                "Just ask me anything or say 'workout' to get a new exercise plan!"
            )
            
            # Set session to ACTIVE
            session = UserSession.get_by_user_id(user_id) or UserSession(user_id=user_id)
            session.update_state(Config.States.ACTIVE)
            
        else:
            # New user or incomplete profile
            await update.message.reply_text(
                f"Hey {username}! 👋 Welcome to your personal Workout & Health Bot! 🏋️‍♂️\n\n"
                "I'm here to help you achieve your fitness goals with:\n"
                "• 🎯 Personalized workout plans\n"
                "• 💡 Expert fitness and nutrition advice\n"
                "• 📈 Progress tracking\n\n"
                "To get started, I'll need to know a bit about you. This will help me create the perfect workout plan tailored just for you!\n\n"
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
            "• General fitness and health 🌟\n\n"
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
                "This helps me create better workout plans for you! 🎯"
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
                "Perfect! I'm now ready to help you achieve your fitness goals! 🚀\n\n"
                "What would you like to do?\n"
                "• Type 'workout' to get a personalized exercise plan\n"
                "• Ask me any fitness or nutrition questions\n"
                "• Type 'progress' to see your workout history",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your profile. Please try again or contact support."
            )
    
    @staticmethod
    async def handle_workout_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle workout generation request"""
        user_id = update.effective_user.id
        
        # Check if user has complete profile
        user = User.get_by_user_id(user_id)
        if not user or not user.is_complete_profile():
            await update.message.reply_text(
                "Please complete your profile first by using /start command! 📝"
            )
            return
        
        await update.message.reply_text(
            "🔄 Generating your personalized workout plan...\n"
            "This may take a few seconds while I analyze your profile and create the perfect routine for you!"
        )
        
        # This will be implemented in Phase 3 with Gemini integration
        # For now, just acknowledge the request
        await update.message.reply_text(
            "⚠️ Workout generation is coming soon! This feature will be implemented in the next phase."
        )
    
    @staticmethod
    async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle general messages based on user state"""
        user_id = update.effective_user.id
        message_text = update.message.text.lower().strip()
        
        # Get user session to determine current state
        session = UserSession.get_by_user_id(user_id)
        
        if not session:
            # No session exists, treat as new user
            await BotHandlers.start_command(update, context)
            return
        
        state = session.conversation_state
        
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
            if any(word in message_text for word in ['workout', 'exercise', 'train']):
                await BotHandlers.handle_workout_request(update, context)
            elif any(word in message_text for word in ['progress', 'history', 'stats']):
                await BotHandlers.handle_progress_request(update, context)
            else:
                # General fitness question - will be handled by Gemini in Phase 3
                await update.message.reply_text(
                    "🤖 I understand you have a fitness question! This feature will be enhanced with AI responses in the next phase.\n\n"
                    "For now, try:\n"
                    "• 'workout' - for exercise plans\n"
                    "• 'progress' - to see your history\n"
                    "• /start - to update your profile"
                )
        else:
            # Unknown state, reset to start
            await BotHandlers.start_command(update, context)
    
    @staticmethod
    async def handle_progress_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle progress/history request"""
        user_id = update.effective_user.id
        
        # Get user workouts
        workouts = Workout.get_user_workouts(user_id, limit=5)
        
        if not workouts:
            await update.message.reply_text(
                "📊 **Your Progress**\n\n"
                "You haven't completed any workouts yet! 💪\n"
                "Type 'workout' to get your first personalized exercise plan and start building your fitness journey!"
            )
        else:
            completed_count = len([w for w in workouts if w.status == 'completed'])
            
            message = f"📊 **Your Progress**\n\n"
            message += f"🏆 Completed Workouts: {completed_count}\n"
            message += f"📅 Recent Activity:\n\n"
            
            for workout in workouts[:3]:  # Show last 3 workouts
                status_emoji = "✅" if workout.status == "completed" else "⏳"
                date = workout.created_date[:10] if workout.created_date else "Unknown"
                message += f"{status_emoji} {date} - {workout.status.title()}\n"
            
            message += f"\nKeep up the great work! 🌟"
            
            await update.message.reply_text(message, parse_mode='Markdown')
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 **Workout Bot Help**\n\n"
            "**Commands:**\n"
            "• /start - Set up your profile or restart\n"
            "• /help - Show this help message\n\n"
            "**What I can do:**\n"
            "• Generate personalized workouts\n"
            "• Answer fitness and nutrition questions\n"
            "• Track your workout progress\n\n"
            "**Quick Actions:**\n"
            "• Type 'workout' to get an exercise plan\n"
            "• Type 'progress' to see your stats\n"
            "• Ask me any fitness questions!\n\n"
            "Need help? Just ask! 💪"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again or use /start to restart."
            )