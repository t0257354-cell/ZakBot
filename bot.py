import os
import logging
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from collections import defaultdict
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
HF_TOKEN = "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"

# Хранилище в памяти
chat_data = defaultdict(lambda: {"history": []})
MAX_HISTORY = 10

class HuggingFaceAI:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def get_response(self, context):
        """Получаем ответ от Hugging Face"""
        try:
            prompt = f"""
Ты - казак в Telegram чате. Отвечай кратко (1 предложение) в казачьем стиле с юмором.
Контекст: {context}
Твой ответ:"""
            
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 80,
                        "temperature": 0.8,
                        "do_sample": True
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    # Извлекаем только ответ
                    response_text = generated.replace(prompt, '').strip()
                    return response_text if response_text else "Так точно! 🐎"
                return "За Дон и волю! 💪"
            else:
                return "Эх, задумался... 🤔"
                
        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            return "Шашка затупилась... ⚔️"

# Инициализация AI
ai_client = HuggingFaceAI()

def contains_kazak(text):
    """Проверяет, содержит ли текст слово 'казак' в любом регистре"""
    if not text or not isinstance(text, str):
        return False
    
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единственный обработчик - реагирует только на слово 'казак' через ИИ"""
    try:
        # Игнорируем сообщения от ботов
        if update.effective_user.is_bot:
            return
        
        chat_id = update.effective_chat.id
        user_message = update.message.text
        user_name = update.effective_user.first_name
        
        # Добавляем сообщение в историю
        chat_data[chat_id]["history"].append(f"{user_name}: {user_message}")
        
        # Ограничиваем историю
        if len(chat_data[chat_id]["history"]) > MAX_HISTORY:
            chat_data[chat_id]["history"] = chat_data[chat_id]["history"][-MAX_HISTORY:]
        
        # Реагируем ТОЛЬКО на слово "казак"
        if contains_kazak(user_message):
            logger.info(f"Казак detected: {user_message}")
            
            # Берем последние 5 сообщений для контекста
            recent_history = chat_data[chat_id]["history"][-5:]
            context_text = "\n".join(recent_history)
            
            # Получаем ответ от ИИ
            ai_response = ai_client.get_response(context_text)
            
            # Отправляем ответ
            await update.message.reply_text(ai_response)
            
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ЕДИНСТВЕННЫЙ обработчик - только на сообщения с текстом
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("🤠 Казак-бот запущен - реагирует только на слово 'казак'")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
