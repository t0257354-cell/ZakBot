import os
import logging
import random
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Basic configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = '8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4'

# Response templates
RESPONSES = [
    "Hello! How can I help you?",
    "That's interesting! Tell me more.",
    "I understand what you're saying.",
    "Thanks for sharing that with me!",
    "What a great question!",
    "I'm here to help with anything you need.",
    "That's something worth discussing!",
]

async def start(update, context):
    await update.message.reply_text('🤖 Hello! I am your AI bot. Send me any message!')

async def echo(update, context):
    user_message = update.message.text
    response = random.choice(RESPONSES)
    await update.message.reply_text(response)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("Bot starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
