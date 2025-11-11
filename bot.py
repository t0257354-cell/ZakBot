import os
import logging
import re
import requests
import random
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
HF_TOKEN = "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"

# Создаем Flask приложение
app = Flask(__name__)

# Хранилище для истории (в памяти)
chat_history = {}

class DogAI:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
        
    def get_dog_response(self, user_message):
        """Получаем ответ от имени собаки Казака"""
        try:
            prompt = f"""
Ты - собака Даниила Казака. Ты умный пёс, который отвечает в Telegram. 
Отвечай кратко (1-2 предложения), как собака: используй "гав", "ррр", "вуф", но при этом будь остроумным.

Сообщение от человека: {user_message}

Ответ собаки Казака:"""
            
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 70,
                        "temperature": 0.9,
                        "do_sample": True,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    
                    # Извлекаем только ответ после промпта
                    if "Ответ собаки Казака:" in generated:
                        response_text = generated.split("Ответ собаки Казака:")[-1].strip()
                    else:
                        response_text = generated.replace(prompt, '').strip()
                    
                    # Очищаем ответ
                    response_text = re.sub(r'^[^а-яА-Я]*', '', response_text)
                    
                    if response_text and len(response_text) > 3:
                        return response_text
            
            # Если ИИ не сработал - запасные ответы собаки
            return self.get_fallback_dog_response()
            
        except Exception as e:
            logger.error(f"AI error: {e}")
            return self.get_fallback_dog_response()
    
    def get_fallback_dog_response(self):
        """Запасные ответы собаки"""
        dog_responses = [
            "Гав! Я собака Казака, а не просто казак! 🐕",
            "Вуф-вуф! Даниил - мой хозяин! 🦴",
            "Ррр... Гав! Я пёс, а не человек! 🐾",
            "Гав-гав! У меня есть хозяин Даниил! 🐶",
            "Вуф! Я собака, меня зовут... эм... я же собака! 🐕‍🦺",
            "Гав! Казак - это мой человек! 🎾",
            "Ррр... Я бы поиграл, но я в телефоне! 🎯",
            "Вуф-гав! У меня лапы, не могу печатать! 🐾",
            "Гав! Спроси у Даниила про меня! 🐶",
            "Ррр... Хочу косточку, а не чат! 🦴"
        ]
        return random.choice(dog_responses)

# Инициализация AI
dog_ai = DogAI()

def contains_kazak(text):
    """Проверяет, содержит ли текст слово 'казак' в любом регистре"""
    if not text or not isinstance(text, str):
        return False
    
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def send_message(chat_id, text):
    """Отправка сообщения через HTTP API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Sent to {chat_id}: {text}")
        else:
            logger.error(f"❌ Failed to send: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука от Telegram"""
    try:
        update = request.get_json()
        
        if 'message' not in update or 'text' not in update['message']:
            return jsonify({'status': 'ok'})
        
        message = update['message']
        chat_id = message['chat']['id']
        user_message = message['text']
        chat_type = message['chat'].get('type', 'private')
        
        # Логируем информацию о чате
        logger.info(f"📨 Message in {chat_type} chat {chat_id}: {user_message}")
        
        # Игнорируем сообщения от ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        # Реагируем ТОЛЬКО на слово "казак"
        if contains_kazak(user_message):
            logger.info(f"🎯 Казак detected in {chat_type} chat!")
            
            # Получаем ответ от собаки
            dog_response = dog_ai.get_dog_response(user_message)
            
            # Отправляем ответ
            send_message(chat_id, dog_response)
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check для Render.com"""
    return jsonify({'status': 'healthy', 'bot': 'Собака Казака 🐶'})

@app.route('/')
def home():
    """Главная страница"""
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
            <p class="status">Бот работает и ждет сообщения со словом "казак"!</p>
            <p>Добавьте бота в группу и напишите любое сообщение с словом "казак"</p>
        </body>
    </html>
    """

def set_webhook():
    """Установка вебхука при запуске"""
    try:
        # Получаем URL от Render.com
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        
        if not render_url:
            logger.warning("RENDER_EXTERNAL_URL not set, using local testing mode")
            return
        
        webhook_url = f"{render_url}/webhook"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logger.info(f"✅ Webhook set: {webhook_url}")
        else:
            logger.error(f"❌ Failed to set webhook: {response.text}")
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

if __name__ == '__main__':
    # Устанавливаем вебхук при запуске
    set_webhook()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Starting server on port {port}")
    logger.info("🐶 Собака Казака запущена!")
    logger.info("🎯 Реагирует только на слово 'казак'")
    
    app.run(host='0.0.0.0', port=port)
