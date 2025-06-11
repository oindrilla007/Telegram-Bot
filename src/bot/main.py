import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.config import Config
from src.bot.handlers import BotHandlers

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if Config.DEBUG else logging.WARNING
)
logger = logging.getLogger(__name__)

class WorkoutBot:
    def __init__(self):
        """Initialize the workout bot"""
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    def setup_handlers(self):
        """Set up all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", BotHandlers.start_command))
        self.application.add_handler(CommandHandler("help", BotHandlers.help_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(
            BotHandlers.handle_fitness_level, 
            pattern="^level_"
        ))
        
        # Message handlers for general messages
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            BotHandlers.handle_general_message
        ))
        
        # Error handler
        self.application.add_error_handler(BotHandlers.error_handler)
        
        logger.info("All handlers set up successfully")
    
    def run(self):
        """Run the bot synchronously using run_polling"""
        try:
            # Validate configuration
            Config.validate_config()
            logger.info("Configuration validated successfully")
            
            # Set up bot handlers
            self.setup_handlers()
            logger.info("Bot handlers set")

            # Start bot polling (blocking call)
            logger.info("🤖 Bot is running! Press Ctrl+C to stop.")
            self.application.run_polling(allowed_updates=["message", "callback_query"])

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            raise

def main():
    """Main entry point"""
    print("🚀 Starting Workout Bot...")
    print("=" * 40)
    
    try:
        bot = WorkoutBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped gracefully")
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        return False

    return True

if __name__ == "__main__":
    main()
