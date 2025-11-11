import os
import logging
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4')

# Simple AI responses
RESPONSES = {
    "hello": ["Hello! 👋", "Hi there!", "Hey! How can I help you?"],
    "how are you": ["I'm doing great! 😊", "I'm fine, thank you!", "All systems operational! 🤖"],
    "what is your name": ["I'm your AI assistant bot!", "I'm a helpful bot created to assist you!"],
    "thank you": ["You're welcome! 😊", "Happy to help!", "Anytime! 👍"],
    "help": ["I can answer questions and chat with you! Try asking me anything."],
    "default": [
        "That's an interesting question!",
        "I'm still learning about that topic.",
        "Could you tell me more about that?",
        "I'd be happy to help with that!",
        "Let me think about that...",
        "That's a great question!",
    ]
}

def get_ai_response(message):
    """Generate a response based on the user's message"""
    message_lower = message.lower()
    
    for key, responses in RESPONSES.items():
        if key in message_lower and key != "default":
            return random.choice(responses)
    
    return random.choice(RESPONSES["default"])

def handle_message(update, context):
    """Handle incoming messages"""
    user_message = update.message.text
    
    if user_message.startswith('/'):
        return
    
    # Show typing action
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Get AI response
    ai_response = get_ai_response(user_message)
    
    update.message.reply_text(ai_response)

def start(update, context):
    """Send a message when the command /start is issued."""
    welcome_text = """
🤖 Hello! I'm your AI Assistant Bot

I can help you with:
• Answering questions
• Having conversations
• Providing information

Just send me a message and I'll respond!
    """
    update.message.reply_text(welcome_text)

def help_command(update, context):
    """Send a message when the command /help is issued."""
    help_text = "Just send me any message and I'll respond with an AI-generated answer!"
    update.message.reply_text(help_text)

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
