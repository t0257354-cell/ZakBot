import os
import requests
import random
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Токены из environment переменных
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OPENROUTER_API_KEY = os.environ.get('DS_TOKEN', '')
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

app = Flask(__name__)

# Инициализируем бота
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

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

# Добавляем обработчик в приложение
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return "Бот работает! 🐱"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Эндпоинт для вебхука от Telegram"""
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        application.update_queue.put(update)
    return 'ok'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка вебхука"""
    if not RENDER_EXTERNAL_HOSTNAME:
        return "RENDER_EXTERNAL_HOSTNAME не установлен"
    
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/webhook"
    result = bot.set_webhook(webhook_url)
    if result:
        return f"Вебхук установлен: {webhook_url}"
    else:
        return "Ошибка установки вебхука"

if __name__ == '__main__':
    # Запускаем Flask приложение
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
