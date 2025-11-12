import os
import logging
import requests
import re
import random
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

app = Flask(__name__)

class WorkingAI:
    def __init__(self):
        self.services = [
            self.try_groq,
            self.try_deepseek, 
            self.try_nova
        ]
    
    def try_groq(self, user_message):
        """Groq API - очень быстрый и бесплатный"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            data = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - юмористическая версия Алексея Навального. Отвечай на сообщения о казаках с юмором и иронией, но без политики. Отвечай кратко и остроумно."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.9
            }
            
            response = requests.post(url, json=data, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"Groq failed: {e}")
        return None
    
    def try_deepseek(self, user_message):
        """DeepSeek API - полностью бесплатный"""
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - юмористическая версия Алексея Навального. Отвечай на сообщения о казаках с юмором и иронией, но без политики. Отвечай кратко и остроумно."
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.9,
                "stream": False
            }
            
            response = requests.post(url, json=data, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"DeepSeek failed: {e}")
        return None
    
    def try_nova(self, user_message):
        """Nova API - еще один бесплатный вариант"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "HTTP-Referer": "https://telegram-bot.com",
                "X-Title": "Telegram Bot"
            }
            
            data = {
                "model": "google/gemma-7b-it:free",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - юмористическая версия Алексея Навального. Отвечай на сообщения о казаках с юмором и иронией, но без политики. Отвечай кратко и остроумно."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.9
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"Nova failed: {e}")
        return None
    
    def generate_response(self, user_message):
        """Пробуем все работающие API"""
        logger.info("🔄 Пробуем бесплатные AI API...")
        
        for service in self.services:
            try:
                response = service(user_message)
                if response and len(response) > 10:
                    logger.info(f"✅ Успешная генерация!")
                    return response
            except Exception as e:
                logger.warning(f"Сервис не сработал: {e}")
                continue
        
        logger.info("❌ Все API не сработали")
        return None

# Инициализация AI
ai = WorkingAI()

def contains_kazak(text):
    if not text or not isinstance(text, str):
        return False
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def send_message(chat_id, text):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set")
        return
        
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Отправлено: {text}")
        else:
            logger.error(f"❌ Ошибка отправки: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        
        if 'message' not in update or 'text' not in update['message']:
            return jsonify({'status': 'ok'})
        
        message = update['message']
        chat_id = message['chat']['id']
        user_message = message['text']
        
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        if contains_kazak(user_message):
            logger.info(f"🎯 Найдено 'казак': {user_message}")
            
            response = ai.generate_response(user_message)
            
            if response:
                send_message(chat_id, response)
            else:
                logger.info("🤐 Генерация не удалась - молчим")
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    bot_status = "✅ Configured" if BOT_TOKEN else "❌ Not set"
    
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Telegram Bot Status</h1>
            <p>BOT_TOKEN: {bot_status}</p>
            <p>Использует бесплатные AI API (Groq, DeepSeek, Nova)</p>
            <p><a href="/test">Test Generation</a></p>
        </body>
    </html>
    """

@app.route('/test')
def test_generation():
    test_message = "привет казак"
    response = ai.generate_response(test_message)
    
    if response:
        status = "✅ Успешная генерация"
    else:
        status = "❌ Генерация не удалась"
    
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Тест генерации</h1>
            <p><strong>Сообщение:</strong> {test_message}</p>
            <p><strong>Статус:</strong> {status}</p>
            <p><strong>Ответ:</strong> {response if response else 'Нет ответа'}</p>
            <p><a href="/">На главную</a></p>
        </body>
    </html>
    """

def set_webhook():
    if not BOT_TOKEN:
        logger.error("❌ Cannot set webhook - BOT_TOKEN not set")
        return
        
    try:
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        if render_url:
            webhook_url = f"{render_url}/webhook"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            requests.post(url, json={"url": webhook_url})
            logger.info(f"✅ Вебхук установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook setup error: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
    
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    logger.info("🎭 Бот запущен с бесплатными AI API!")
    app.run(host='0.0.0.0', port=port)
