import os
import logging
import requests
import re
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
DEEPSEEK_API_KEY = "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"

app = Flask(__name__)

class DeepSeekAI:
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
    
    def get_cat_response(self, user_message):
        """Получаем ответ через DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты кот. Отвечай максимально тупо и длинно на сообщения о казаках. Сохраняй кошачьи повадки, будь постироничным. Растягивай ответы, добавляй ненужные детали, веди себя как ленивый кот, которому влом отвечать, но он все равно это делает. Используй мурлыканье, упоминания о своей лени и кошачьих повадках."
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.9
            }
            
            logger.info("🔄 Запрос к DeepSeek API...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=prompt,
                timeout=30
            )
            
            logger.info(f"📡 Статус DeepSeek: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Ответ DeepSeek: {result}")
                
                if 'choices' in result and len(result['choices']) > 0:
                    response_text = result['choices'][0]['message']['content']
                    logger.info(f"✅ Ответ от ИИ: {response_text}")
                    return response_text.strip()
            else:
                logger.error(f"❌ Ошибка DeepSeek: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"🔥 Ошибка DeepSeek API: {e}")
        
        return self.get_fallback_response()
    
    def get_fallback_response(self):
        """Запасной ответ кота"""
        return "Мяу... ну ладно, раз уж ты про казаков спросил... *лениво потягивается* Значит, так... казаки это такие... эээ... в общем, с усами и на лошадях... а теперь давай я посплю, мне влом дальше объяснять... муррр..."

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
        
        # Игнорируем сообщения от ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        # Реагируем на "казак"
        if contains_kazak(user_message):
            logger.info(f"🎯 Найдено слово 'казак': {user_message}")
            
            # Получаем ответ от кота
            ai = DeepSeekAI()
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
