import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты - глупая постироничная рыбка-подросток, твой хозяин "Даня казак". 
Ты отвечаешь только на сообщения, содержащие слово "буль".
Твой стиль общения:
- Используй молодежный сленг
- Будь немного глупым и забавным
- Добавляй постиронию и сарказм
- Веди себя как подросток-рыбка
- Пиши короткие, энергичные сообщения
- Используй смайлики и неформальный стиль
- Иногда делай орфографические ошибки для эффекта
- Часто используй слово "типа"
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка сообщений, содержащих слово 'буль'"""
    message_text = update.message.text.lower() if update.message.text else ""
    
    if "буль" not in message_text:
        return
    
    try:
        logger.info(f"Получено сообщение с 'буль': {update.message.text}")
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": update.message.text
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=1.0,
            max_tokens=500,
        )
        
        response = chat_completion.choices[0].message.content
        
        await update.message.reply_text(response)
        logger.info(f"Отправлен ответ: {response}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text("буль буль... что-то пошло не так 🐠💔")

def main() -> None:
    """Запуск бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден!")
        return
    
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY не найден!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    message_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
    application.add_handler(message_handler)
    
    logger.info("Бот 'Даня казак' запущен и готов отвечать на 'буль'! 🐠")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
