import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hardcoded tokens (replace with your actual tokens)
TELEGRAM_BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
GROQ_API_KEY = "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"

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def generate_groq_response(user_message: str) -> str:
    """Generate a response using Groq API"""
    
    try:
        # You can customize the system prompt to define the bot's personality and response style
        system_prompt = """Ты - бот в Telegram группе. Ты отвечаешь на сообщения, содержащие слово 'Путин'. 
        Будь информативным, нейтральным и фактологичным в своих ответах. Отвечай кратко и по существу."""
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150,
            top_p=1
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "Не удалось сгенерировать ответ в данный момент."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and respond if they contain 'Путин'"""
    
    # Ignore messages without text
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text
    chat_id = update.message.chat_id
    
    # Check if message contains the target word (case insensitive)
    if 'путин' in message_text.lower():
        try:
            logger.info(f"Detected 'Путин' in message from chat {chat_id}")
            
            # Generate response using Groq
            response = generate_groq_response(message_text)
            
            # Send the response
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text("Извините, произошла ошибка при обработке сообщения.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add message handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot is starting...")
    print("✅ Bot is running with hardcoded tokens!")
    print(f"🤖 Bot token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"🔑 Groq token: {GROQ_API_KEY[:10]}...")
    
    # Start polling
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
