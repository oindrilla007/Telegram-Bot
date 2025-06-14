# AI-Powered Telegram Workout Bot 🤖💪

An intelligent Telegram bot that provides personalized workout plans, diet recommendations, and fitness advice using AI.

## Features

- 🤖 AI-generated personalized workout plans
- 🥗 Custom diet recommendations
- 📊 Progress tracking and statistics
- 💡 Fitness and nutrition advice
- ✅ Exercise completion tracking
- 🎯 Adaptive recommendations based on user progress

## Deployment to Railway

### Prerequisites

1. A [Railway](https://railway.app/) account
2. A [GitHub](https://github.com/) account
3. Your bot token from [@BotFather](https://t.me/botfather)
4. Your Supabase credentials
5. Your Google AI (Gemini) API key

### Deployment Steps

1. **Fork this repository**
   - Click the "Fork" button on GitHub to create your copy

2. **Set up Railway**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository

3. **Configure Environment Variables**
   In Railway, add these environment variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Deploy**
   - Railway will automatically deploy your bot
   - Monitor the deployment in the Railway dashboard
   - Check the logs to ensure everything is running correctly

5. **Verify Deployment**
   - Open your bot in Telegram
   - Send the `/start` command
   - The bot should respond and be fully functional

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-workout-bot.git
   cd telegram-workout-bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your environment variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. Run the bot:
   ```bash
   python src/main.py
   ```

## Support

If you encounter any issues or have questions:
1. Check the Railway logs for errors
2. Open an issue in the GitHub repository
3. Contact the bot maintainer

## License

This project is licensed under the MIT License - see the LICENSE file for details. 