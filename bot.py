import os
import logging
import requests
import re
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"

app = Flask(__name__)

class LocalAI:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.load_model()
    
    def load_model(self):
        """Загружаем локальную модель"""
        try:
            from transformers import pipeline
            logger.info("🔄 Загружаем модель...")
            
            # Используем маленькую модель для скорости
            self.chatbot = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                tokenizer="microsoft/DialoGPT-small",
                max_length=200,
                temperature=0.9,
                do_sample=True
            )
            logger.info("✅ Модель загружена!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            self.chatbot = None
    
    def get_cat_response(self, user_message):
        """Генерируем ответ через локальную модель"""
        if self.chatbot is None:
            return self.get_fallback_response()
        
        try:
            prompt = f"""Ты кот. Отвечай максимально тупо и длинно на сообщения о казаках. 
Сохраняй кошачьи повадки, будь постироничным. Растягивай ответы, добавляй ненужные детали, 
веди себя как ленивый кот, которому влом отвечать, но он все равно это делает.

Сообщение: {user_message}

Ответ кота:"""
            
            logger.info("🔄 Генерируем ответ...")
            
            result = self.chatbot(
                prompt,
                max_length=300,
                temperature=0.9,
                do_sample=True,
                pad_token_id=50256
            )
            
            generated_text = result[0]['generated_text']
            
            # Извлекаем только ответ после промпта
            response = generated_text.replace(prompt, "").strip()
            
            # Если ответ пустой, используем запасной
            if not response or len(response) < 10:
                return self.get_fallback_response()
                
            logger.info(f"✅ Сгенерирован ответ: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации: {e}")
            return self.get_fallback_response()
    
    def get_fallback_response(self):
        """Запасной ответ"""
        return "Мяу... ну казаки это... *лениво потягивается*... такие люди с лошадьми и усами... но мне вообще-то спать хочется, так что если можно покороче... муррр..."

# Инициализация AI
ai = LocalAI()

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
            logger.info(f"✅ Отправлено: {text[:100]}...")
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
            logger.info(f"🎯 Найдено слово 'казак': {user_message}")
            
            # Получаем ответ от кота
            cat_response = ai.get_cat_response(user_message)
            
            # Отправляем ответ
            send_message(chat_id, cat_response)
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    return "🐱 Кот-казак бот работает!"

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
    except Exception as e:
        logger.error(f"Ошибка установки вебхука: {e}")

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    logger.info("🐱 Кот-казак бот запущен!")
    app.run(host='0.0.0.0', port=port)
