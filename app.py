import os
import requests
import random
from flask import Flask, request
import telebot

# Токены из environment переменных
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OPENROUTER_API_KEY = os.environ.get('DS_TOKEN', '')

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

def get_deepseek_response(message_text):
    """Получает ответ от DeepSeek через OpenRouter API"""
    if not OPENROUTER_API_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Telegram Fish Bot"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Ты - говорящая рыбка в аквариуме. Ты видишь, что твой хозяин делает смешные и забавные вещи. Отвечай очень коротко, 1-2 предложения, в рыбьем стиле: используй слова бульк, плеск, пузыри. Расскажи что ты видела смешного, но кратко и мило."
            },
            {
                "role": "user",
                "content": message_text
            }
        ],
        "max_tokens": 50,
        "temperature": 0.8
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                               headers=headers, json=payload, timeout=15)
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None

@app.route('/')
def home():
    return "Рыбка-бот работает! 🐠 Просто напиши 'рыбка' в Telegram"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука от Telegram"""
    if request.method == 'POST':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    return 'ok'

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработчик сообщений"""
    if message.text and "рыбка" in message.text.lower():
        ai_response = get_deepseek_response(message.text)
        if ai_response:
            bot.reply_to(message, ai_response)
        else:
            responses = [
                "Бульк-бульк! Видела как ты танцевал с пылесосом! 🐠",
                "Плеск! Ты разговаривал с кактусом, это было забавно! 💦",
                "Пузыри... А ты вчера пел в душе как рок-звезда! 🫧",
                "Бульк! Видела твою битву с дверью... победа за дверью! 🐟",
                "Плеск-плеск! Ты искал очки, а они были на лбу! 🌊",
                "Пузырьки смеха! Ты пытался поймать муху как лягушка! 🐠",
                "Бульк... Наблюдала за твоим танцем с тостером! 🔥"
            ]
            bot.reply_to(message, random.choice(responses))

if __name__ == '__main__':
    # Удаляем вебхук если был (для чистоты)
    bot.remove_webhook()
    
    # Устанавливаем вебхук
    render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if render_hostname:
        bot.set_webhook(url=f"https://{render_hostname}/webhook")
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
