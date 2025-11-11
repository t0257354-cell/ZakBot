import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration - using environment variables for security
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', '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')

# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

def query_huggingface(payload):
    """Query Hugging Face API for AI response"""
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 503:
            return {"error": "Model is loading, please try again in a few seconds"}
        return response.json()
    except Exception as e:
        logger.error(f"Hugging Face API error: {e}")
        return {"error": str(e)}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate AI responses"""
    user_message = update.message.text
    
    # Don't respond to commands or empty messages
    if user_message.startswith('/') or not user_message.strip():
        return
    
    try:
        # Show typing action
        await update.message.chat.send_action(action="typing")
        
        # Generate AI response using Hugging Face
        output = query_huggingface({
            "inputs": user_message,
            "parameters": {
                "max_length": 300,
                "temperature": 0.7,
                "do_sample": True,
                "pad_token_id": 50256
            }
        })
        
        if output and 'error' in output:
            ai_response = "🔄 The AI model is warming up. Please try again in 10-20 seconds!"
        elif output and isinstance(output, list) and len(output) > 0:
            if 'generated_text' in output[0]:
                ai_response = output[0]['generated_text']
            else:
                ai_response = "I received a response but cannot display it properly."
        else:
            ai_response = "Hello! I'm your AI assistant. How can I help you today?"
        
        # Clean response
        ai_response = str(ai_response).strip()
        
        # Limit response length for Telegram
        if len(ai_response) > 4000:
            ai_response = ai_response[:4000] + "..."
            
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    welcome_text = """
🤖 **Hello! I'm your AI Assistant Bot**

I'm powered by Hugging Face's AI models and can help you with:
• Answering questions
• Having conversations
• Providing information
• Creative writing

Just send me a message and I'll respond using AI technology!

**Note:** The AI might take 10-20 seconds to warm up when first starting.
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = """
📖 **How to use this bot:**

Simply send me any message or question, and I'll respond using AI!

**Examples:**
• "What is the capital of France?"
• "Explain machine learning"
• "Write a short poem about nature"
• "Tell me a joke"

**Commands:**
/start - Start the bot
/help - Show this help message
    """
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Command("start"), start_command))
    application.add_handler(MessageHandler(filters.Command("help"), help_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🤖 Bot is starting...")
    logger.info("✅ Using Hugging Face API")
    logger.info("🚀 Bot is running...")
    
    application.run_polling()

if __name__ == '__main__':
    main()
