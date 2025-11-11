import os
import logging
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
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
MAX_HISTORY = 15

class HuggingFaceAI:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def get_response(self, context, trigger_word="казак"):
        """Получаем ответ от Hugging Face с учетом контекста и триггерного слова"""
        try:
            prompt = f"""
Ты - участник чата в Telegram. Ты отвечаешь на сообщения, где упоминается слово "казак". 
Будь тематическим - отвечай в стиле казачьих традиций, с юмором и мудростью.
Используй соответствующие выражения и пословицы. Будь кратким и колоритным (1-2 предложения).
Можешь добавлять эмодзи.

Контекст беседы:
{context}

Триггерное слово: {trigger_word}
Твой ответ в казачьем стиле:"""
            
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 120,
                        "temperature": 0.8,
                        "do_sample": True,
                        "repetition_penalty": 1.2
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    # Извлекаем только ответ после промпта
                    if "Твой ответ в казачьем стиле:" in generated:
                        response_text = generated.split("Твой ответ в казачьем стиле:")[-1].strip()
                    else:
                        response_text = generated.replace(prompt, '').strip()
                    
                    # Очищаем ответ от возможных артефактов
                    response_text = re.sub(r'^[^а-яА-Я]*', '', response_text)
                    return response_text if response_text else "Так точно! 🐎"
                return "За душу взяло! 💪"
            else:
                logger.warning(f"HF API response: {response.status_code}")
                return "Эх, задумался казак... 🤔"
                
        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            return "Шашка затупилась, подождите... ⚔️"

# Инициализация AI
ai_client = HuggingFaceAI()

def contains_kazak(text):
    """Проверяет, содержит ли текст слово 'казак' в любом регистре"""
    if not text:
        return False
    
    # Ищем слово "казак" в любом регистре, учитывая разные формы
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений - реагирует на слово 'казак'"""
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
        
        logger.info(f"Chat {chat_id}, message: {user_message[:50]}...")
        
        # Проверяем, содержит ли сообщение слово "казак"
        if contains_kazak(user_message):
            logger.info(f"Trigger word 'казак' detected in chat {chat_id}")
            
            # Берем последние 8 сообщений для контекста
            recent_history = chat_data[chat_id]["history"][-8:]
            context_text = "\n".join(recent_history)
            
            # Получаем ответ от AI
            ai_response = ai_client.get_response(context_text)
            
            # Добавляем казачий колорит, если ответ слишком короткий
            if len(ai_response) < 3:
                ai_response = "За Дон и волю! 🐎"
            
            # Отправляем ответ
            await update.message.reply_text(ai_response)
            
            # Добавляем ответ бота в историю
            chat_data[chat_id]["history"].append(f"🤖 Казак-бот: {ai_response}")
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🤠 Салю, я казак-бот!\n\n"
        "Отвечаю на сообщения со словом «казак» в любом регистре.\n"
        "Пиши про казаков - буду отвечать с юмором и мудростью!\n\n"
        "Команды:\n"
        "/start - это сообщение\n"
        "/stats - статистика чата\n"
        "/kazak - казачья мудрость\n"
        "/help - помощь"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    chat_id = update.effective_chat.id
    history_size = len(chat_data[chat_id]["history"])
    
    # Считаем сколько раз упоминалось слово "казак"
    kazak_count = sum(1 for msg in chat_data[chat_id]["history"] if contains_kazak(msg))
    
    await update.message.reply_text(
        f"📊 Казачья статистика:\n"
        f"• Сообщений в истории: {history_size}\n"
        f"• Упоминаний казаков: {kazak_count}\n"
        f"• Бот готов к службе! 🐎"
    )

async def kazak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /kazak - случайная казачья мудрость"""
    kazak_wisdom = [
        "Казак без коня - что воин без ружья! 🐎",
        "Слава Богу, что мы казаки! 🙏",
        "Казачья воля дороже золота! 💰",
        "На казака да на смерть - суда нет! ⚔️",
        "Казак голоден, а конь его сыт - так и должно быть! 🥖",
        "Лучше смерть, чем позор! 💪",
        "Казак умирает, а слава его живёт! 🌟",
        "С Дона выдачи нет! 🏞️",
        "Казак и в беде не плачет! 😤",
        "Где казак, там и победа! 🎯"
    ]
    
    import random
    wisdom = random.choice(kazak_wisdom)
    await update.message.reply_text(f"💭 Казачья мудрость:\n{wisdom}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
🤠 Помощь по казак-боту:

Я отвечаю на сообщения, содержащие слово "КАЗАК" в любом регистре.

Примеры триггеров:
• "казак" • "Казак" • "КАЗАК" 
• "казаки" • "казачка" • "казачий"
• "казаках" • "казаком" • "о казаках"

Команды:
/start - приветствие
/help - эта справка  
/stats - статистика чата
/kazak - казачья мудрость

Казак сказал - казак сделал! 💪
"""
    await update.message.reply_text(help_text)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ping для проверки работы"""
    await update.message.reply_text("🟢 Казак-бот на посту! Готов к службе! 💂‍♂️")

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("kazak", kazak_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("🚀 Starting Kazak Bot...")
    logger.info("🤠 Bot will respond to messages containing 'казак'")
    logger.info(f"🔑 Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"🔑 HF Token: {HF_TOKEN[:10]}...")
    
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=60
        )
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        # Перезапуск через 10 секунд
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
