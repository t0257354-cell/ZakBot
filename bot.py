import os
import logging
import requests
import re
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
HF_TOKEN = "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"

app = Flask(__name__)

class HuggingFaceAI:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
    
    def generate_response(self, user_message):
        """Генерируем уникальный ответ через Hugging Face API"""
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            prompt = f"""Ты - юмористическая версия Алексея Навального. Отвечай на сообщения о казаках с юмором и иронией, но без политики.

Сообщение: {user_message}

Юмористический ответ:"""
            
            logger.info("🔄 Генерируем ответ через Hugging Face...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 150,
                        "temperature": 0.9,
                        "do_sample": True,
                        "top_p": 0.9,
                        "repetition_penalty": 1.2
                    },
                    "options": {
                        "wait_for_model": True
                    }
                },
                timeout=30
            )
            
            logger.info(f"📡 Статус Hugging Face: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Полный ответ API: {result}")
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    logger.info(f"📝 Сгенерированный текст: {generated_text}")
                    
                    # Извлекаем только ответ после промпта
                    response_text = generated_text.replace(prompt, '').strip()
                    
                    # Очищаем ответ
                    response_text = re.sub(r'^[^а-яА-Я]*', '', response_text)
                    
                    if response_text and len(response_text) > 15:
                        logger.info(f"✅ Успешная генерация: {response_text}")
                        return response_text
                    else:
                        logger.warning("❌ Ответ слишком короткий")
                        return None
            
            elif response.status_code == 503:
                logger.warning("⏳ Модель загружается...")
                return None
            else:
                logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"🔥 Ошибка генерации: {e}")
            return None

# Инициализация AI
ai = HuggingFaceAI()

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
            logger.info(f"✅ Отправлен сгенерированный ответ: {text}")
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
    return "🎭 Бот с генерацией через Hugging Face"

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
            <h1>Тест генерации Hugging Face</h1>
            <p><strong>Сообщение:</strong> {test_message}</p>
            <p><strong>Статус:</strong> {status}</p>
            <p><strong>Ответ:</strong> {response if response else 'Нет ответа'}</p>
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
    except Exception as e:
        logger.error(f"Ошибка установки вебхука: {e}")

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    logger.info("🎭 Бот с реальной генерацией через Hugging Face запущен!")
    logger.info("🌐 Откройте /test для проверки генерации")
    app.run(host='0.0.0.0', port=port)
