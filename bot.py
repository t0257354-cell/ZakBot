import os
import logging
import requests
import re
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

app = Flask(__name__)

class GroqAI:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        # Бесплатный API, не требует ключа
    
    def generate_response(self, user_message):
        """Генерируем ответ через Groq API"""
        try:
            data = {
                "model": "llama-3.1-8b-instant",  # Быстрая и бесплатная модель
                "messages": [
                    {
                        "role": "system",
                        "content": """Ты - юмористическая версия Алексея Навального. 
Отвечай на сообщения о казаках с юмором и иронией, но без политики. 
Будь остроумным, саркастичным и дружелюбным. 
Отвечай кратко (1-2 предложения) в разговорном стиле."""
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.9,
                "top_p": 0.9
            }
            
            logger.info("🔄 Генерируем ответ через Groq...")
            
            response = requests.post(
                self.api_url,
                json=data,
                timeout=20
            )
            
            logger.info(f"📡 Groq status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content'].strip()
                
                if response_text and len(response_text) > 10:
                    logger.info(f"✅ Успешная генерация: {response_text}")
                    return response_text
                else:
                    logger.warning("❌ Ответ слишком короткий")
                    return None
                    
            elif response.status_code == 429:
                logger.warning("⏳ Rate limit, waiting...")
                return None
            else:
                logger.error(f"❌ Groq error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"🔥 Groq error: {e}")
            return None

# Инициализация AI
ai = GroqAI()

def contains_kazak(text):
    """Проверяет слово 'казак'"""
    if not text or not isinstance(text, str):
        return False
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def send_message(chat_id, text):
    """Отправка сообщения"""
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
    """Обработчик вебхука"""
    try:
        update = request.get_json()
        
        if 'message' not in update or 'text' not in update['message']:
            return jsonify({'status': 'ok'})
        
        message = update['message']
        chat_id = message['chat']['id']
        user_message = message['text']
        
        # Игнорируем сообщения от ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        # Реагируем на "казак"
        if contains_kazak(user_message):
            logger.info(f"🎯 Найдено 'казак': {user_message}")
            
            # Пытаемся сгенерировать ответ
            response = ai.generate_response(user_message)
            
            # Если генерация удалась - отправляем, иначе молчим
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
            <h1>Telegram Bot with Groq AI</h1>
            <p>BOT_TOKEN: {bot_status}</p>
            <p>Использует Groq API (бесплатный и быстрый)</p>
            <p><a href="/test">Test Generation</a></p>
        </body>
    </html>
    """

@app.route('/test')
def test_generation():
    """Тест генерации ответа"""
    test_message = "привет казак"
    response = ai.generate_response(test_message)
    
    if response:
        status = "✅ Успешная генерация"
    else:
        status = "❌ Генерация не удалась"
    
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Тест генерации Groq</h1>
            <p><strong>Сообщение:</strong> {test_message}</p>
            <p><strong>Статус:</strong> {status}</p>
            <p><strong>Ответ:</strong> {response if response else 'Нет ответа'}</p>
            <p><a href="/">На главную</a></p>
        </body>
    </html>
    """

def set_webhook():
    """Установка вебхука"""
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
    logger.info("🎭 Бот запущен с Groq AI!")
    app.run(host='0.0.0.0', port=port)
