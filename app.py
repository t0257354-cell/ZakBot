import os
import requests
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Токен бота Telegram из environment переменной
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Токен OpenRouter API для DeepSeek из environment переменной
OPENROUTER_API_KEY = os.environ.get('DS_TOKEN', '')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

async def get_deepseek_response(message_text):
    """Получает ответ от DeepSeek через OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",  # Обязательный заголовок для OpenRouter
        "X-Title": "Telegram Cat Bot"  # Название приложения
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",  # Модель через OpenRouter
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
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при обращении к OpenRouter API: {e}")
        return None
    except KeyError as e:
        print(f"Ошибка в формате ответа от API: {e}")
        print(f"Полный ответ: {response.text}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений, который реагирует на слово 'Шмыг'"""
    if update.message:
        text = update.message.text
        if text:
            # Проверяем наличие слова "Шмыг" в любом регистре
            if "шмыг" in text.lower():
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
                    import random
                    await update.message.reply_text(random.choice(fallback_responses))

def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        print("Ошибка: Токен Telegram бота не установлен!")
        print("Пожалуйста, установите переменную окружения BOT_TOKEN")
        return
    
    if not OPENROUTER_API_KEY:
        print("Ошибка: Токен DeepSeek API не установлен!")
        print("Пожалуйста, установите переменную окружения DS_TOKEN")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("Бот запущен и слушает сообщения с словом 'Шмыг'...")
    print("Используется DeepSeek через OpenRouter API")
    application.run_polling()

if __name__ == "__main__":
    main()
