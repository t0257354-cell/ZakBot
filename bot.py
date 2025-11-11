import os
import logging
import random
import requests
import re
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
GEMINI_API_KEY = "AIzaSyCQjSpFUgGf5BZdR3HhP3k9M81pXqo8pBk"  # Бесплатный ключ от Google AI Studio

app = Flask(__name__)

class GeminiAI:
    def __init__(self):
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    def get_dog_response(self, user_message):
        """Получаем ответ через Google Gemini API"""
        try:
            prompt = {
                "contents": [{
                    "parts": [{
                        "text": f"""Ты - собака по имени Гаврюша, ты принадлежишь Даниилу Казаку. 
Отвечай ОЧЕНЬ кратко (максимум 1 предложение) как собака. 
Используй звуки: гав, вуф, ррр. 
Не объясняй ничего, просто отведи как собака.

Сообщение: {user_message}

Ответ:"""
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 30,  # Очень короткие ответы
                    "temperature": 0.8
                }
            }
            
            logger.info("🔄 Запрос к Google Gemini...")
            
            response = requests.post(
                self.api_url,
                json=prompt,
                timeout=15
            )
            
            logger.info(f"📡 Статус Gemini: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Ответ Gemini: {result}")
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    logger.info(f"✅ Ответ от ИИ: {response_text}")
                    return response_text.strip()
            else:
                logger.error(f"❌ Ошибка Gemini: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"🔥 Ошибка Gemini API: {e}")
        
        return self.get_fallback_response()
    
    def get_fallback_response(self):
        """Запасные ответы"""
        fallback_responses = [
            "Гав! Я собака Казака! 🐕",
            "Вуф-вуф! Даниил - мой хозяин! 🦴", 
            "Ррр... Гав! Я пёс! 🐾",
            "Гав-гав! Казак - мой человек! 🐶",
            "Вуф! Хочу на прогулку! 🏞️",
            "Гав-ррр! Даниил меня зовет! 🐕‍🦺",
            "Вуф! Мой хозяин - казак! 💂‍♂️",
            "Гав! Люблю своего казака! ❤️",
            "Ррр-вуф! Хочу играть! 🎾",
            "Гав! Казак самый лучший! 🌟"
        ]
        response = random.choice(fallback_responses)
        logger.info(f"🔄 Использован запасной ответ: {response}")
        return response

# Инициализация AI
dog_ai = GeminiAI()

def contains_kazak(text):
    """Проверяет слово 'казак'"""
    if not text or not isinstance(text, str):
        return False
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def send_message(chat_id, text):
    """Отправка сообщения"""
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
        chat_type = message['chat'].get('type', 'private')
        
        logger.info(f"📨 Сообщение в {chat_type}: {user_message}")
        
        # Игнорируем сообщения от ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        # Реагируем на "казак"
        if contains_kazak(user_message):
            logger.info(f"🎯 Найдено слово 'казак'!")
            
            # Получаем ответ
            dog_response = dog_ai.get_dog_response(user_message)
            
            # Отправляем ответ
            send_message(chat_id, dog_response)
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Собака Казака 🐶</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .dog { font-size: 48px; }
                .status { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="dog">🐕</div>
            <h1>Собака Казака</h1>
            <p class="status">✅ Бот работает с Google Gemini AI</p>
            <p>Отвечает на сообщения со словом "казак"</p>
        </body>
    </html>
    """

@app.route('/test')
def test_ai():
    """Тестовая страница для проверки ИИ"""
    test_message = "привет казак"
    response = dog_ai.get_dog_response(test_message)
    
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Тест ИИ</h1>
            <p><strong>Сообщение:</strong> {test_message}</p>
            <p><strong>Ответ ИИ:</strong> {response}</p>
            <p><a href="/">На главную</a></p>
        </body>
    </html>
    """

def set_webhook():
    """Установка вебхука"""
    try:
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        if render_url:
            webhook_url = f"{render_url}/webhook"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            response = requests.post(url, json={"url": webhook_url})
            if response.status_code == 200:
                logger.info(f"✅ Вебхук установлен: {webhook_url}")
            else:
                logger.error(f"❌ Ошибка вебхука: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка установки вебхука: {e}")

if __name__ == '__main__':
    # Устанавливаем вебхук
    set_webhook()
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Сервер запущен на порту {port}")
    logger.info("🐶 Собака Казака с Google Gemini готова к работе!")
    logger.info("🌐 Откройте /test для проверки ИИ")
    
    app.run(host='0.0.0.0', port=port)
