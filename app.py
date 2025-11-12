import os
import requests
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Токен бота Telegram из environment переменной
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Токен OpenRouter API для DeepSeek из environment переменной
OPENROUTER_API_KEY = os.environ.get('DS_TOKEN', '')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

async def get_deepseek_response(message_text):
    """Получает ответ от DeepSeek через OpenRouter API"""
    if not OPENROUTER_API_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Telegram Cat Bot"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Ты игривый кот. Отвечай очень коротко, как кот, используя звуки: мур, мяу, мефк, хррррр, мррр, шшшш и т.д. Будь милым и забавным. Отвечай максимально кратко - 1-3 слова, только кошачьи звуки. Не объясняй ничего, не задавай вопросов."
            },
            {
                "role": "user",
                "content": message_text
            }
        ],
        "max_tokens": 15,
        "temperature": 0.8,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
        
    except Exception as e:
        print(f"Ошибка при обращении к API: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений, который реагирует на слово 'Шмыг'"""
    if update.message:
        text = update.message.text
        if text and "шмыг" in text.lower():
            # Получаем ответ от DeepSeek через OpenRouter
            ai_response = await get_deepseek_response(f"Пользователь написал: '{text}'. Ответь как кот на слово 'шмыг'.")
            
            if ai_response:
                await update.message.reply_text(ai_response)
            else:
                # Фолбэк ответы если API не работает
                fallback_responses = [
                    "мефк! 🐾", 
                    "хррррр...", 
                    "мур-мур 😻", 
                    "мяу!", 
                    "шшшш!",
                    "мрррр...",
                    "*топчет лапками*",
                    "*выгибает спинку*"
                ]
                await update.message.reply_text(random.choice(fallback_responses))

def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        print("Ошибка: Токен Telegram бота не установлен!")
        print("Пожалуйста, установите переменную окружения BOT_TOKEN")
        return
    
    print("Проверка токенов...")
    print(f"BOT_TOKEN установлен: {'Да' if BOT_TOKEN else 'Нет'}")
    print(f"DS_TOKEN установлен: {'Да' if OPENROUTER_API_KEY else 'Нет'}")
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчик сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        print("Бот запущен и слушает сообщения с словом 'Шмыг'...")
        print("Используется DeepSeek через OpenRouter API")
        application.run_polling()
        
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        print("Возможные причины:")
        print("1. Неверный токен бота")
        print("2. Проблемы с сетью")
        print("3. Несовместимая версия библиотеки")

if __name__ == "__main__":
    main()
