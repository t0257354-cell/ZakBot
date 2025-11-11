import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from collections import defaultdict
import requests

# Хранилище данных
chat_data = defaultdict(lambda: {"counter": 0, "history": []})
MAX_HISTORY = 10

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HuggingFaceAI:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def get_response(self, context):
        prompt = f"""
Ты - участник группового чата. Отвечай кратко и естественно.

Контекст:
{context}

Твой ответ:"""
        
        try:
            headers = {
                "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {"max_length": 80, "temperature": 0.7}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list):
                    return result[0]['generated_text'].replace(prompt, '').strip()
            return "Интересно... 🤔"
            
        except Exception as e:
            logger.error(f"AI error: {e}")
            return "Думаю... ⏳"

ai_client = HuggingFaceAI()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.is_bot:
        return
    
    chat_id = update.effective_chat.id
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    # Обновляем данные
    chat_data[chat_id]["counter"] += 1
    chat_data[chat_id]["history"].append(f"{user_name}: {user_message}")
    
    # Ограничиваем историю
    if len(chat_data[chat_id]["history"]) > MAX_HISTORY:
        chat_data[chat_id]["history"] = chat_data[chat_id]["history"][-MAX_HISTORY:]
    
    # Отвечаем на каждое третье сообщение
    if chat_data[chat_id]["counter"] % 3 == 0:
        history_text = "\n".join(chat_data[chat_id]["history"][-6:])
        ai_response = ai_client.get_response(history_text)
        
        await update.message.reply_text(ai_response)
        chat_data[chat_id]["history"].append(f"Бот: {ai_response}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Бот запущен! Отвечаю на каждое 3-е сообщение.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    counter = chat_data[chat_id]["counter"]
    await update.message.reply_text(f"📊 Сообщений: {counter}. До ответа: {3 - (counter % 3)}")

def main():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN not found!")
        return
    
    application = Application.builder().token(token).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    if webhook_url:
        # Для хостингов с webhook (Railway, Heroku)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}"
        )
    else:
        # Для локального тестирования
        application.run_polling()

if __name__ == "__main__":
    main()
