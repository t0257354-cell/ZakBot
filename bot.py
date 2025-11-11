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
    
    def generate_response(self, user_message):
        """Генерируем уникальный ответ через DeepSeek API"""
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
                        "content": """Ты - юмористическая версия Алексея Навального. Отвечай на сообщения о казаках с юмором и иронией, но без политических комментариев. 
                        
Твой стиль:
- Остроумные шутки про казаков
- Самоирония и легкая насмешливость
- Дружелюбный тон с элементами стендапа
- Избегай политики, говори только о юмористической стороне
- Отвечай как будто ведешь юмористический блог

Примеры хороших ответов:
"Казаки? Это те, у кого усы длиннее, чем список моих расследований! Шучу, конечно 😄"
"О, казаки! Готов поспорить, их чат-бот был бы с нагайкой и чувством юмора!"
"Знаете, казаки мне напоминают... ну, в общем, людей которые точно знают ответ! Правда, иногда этот ответ приходится искать на карте 🗺️"
"""
                    },
                    {
                        "role": "user", 
                        "content": f"Сообщение в чате: {user_message}"
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.9,
                "top_p": 0.9,
                "frequency_penalty": 0.5,
                "presence_penalty": 0.3
            }
            
            logger.info("🔄 Генерируем уникальный ответ через DeepSeek...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=prompt,
                timeout=30
            )
            
            logger.info(f"📡 Статус DeepSeek: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Полный ответ API: {result}")
                
                if 'choices' in result and len(result['choices']) > 0:
                    response_text = result['choices'][0]['message']['content'].strip()
                    logger.info(f"✅ Сгенерирован ответ: {response_text}")
                    
                    # Проверяем что ответ адекватный
                    if len(response_text) > 10 and not response_text.startswith("Я как искусственный интеллект"):
                        return response_text
                    else:
                        logger.warning("❌ Ответ слишком короткий или шаблонный")
                        return self._generate_fallback(user_message)
            
            logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return self._generate_fallback(user_message)
                
        except Exception as e:
            logger.error(f"🔥 Ошибка генерации: {e}")
            return self._generate_fallback(user_message)
    
    def _generate_fallback(self, user_message):
        """Генерируем простой ответ на основе контекста"""
        # Простая логика для разных типов сообщений
        if "привет" in user_message.lower():
            return "О, приветствую! Готов пошутить про казаков в своем неповторимом стиле! 😄"
        elif "как дела" in user_message.lower():
            return "Дела? Отлично! Как у казака после удачной шутки! Готов продолжать юмористическую атаку! 💪"
        else:
            return "Казаки! Отличный повод для шутки! Знаете, они бы точно оценили мое чувство юмора... или отправили бы в юмористический дозор! 🎭"

# Инициализация AI
ai = DeepSeekAI()

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
            
            # Генерируем уникальный ответ
            response = ai.generate_response(user_message)
            
            # Отправляем ответ
            send_message(chat_id, response)
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    return "🎭 Бот с генерацией ответов работает!"

@app.route('/test')
def test_generation():
    """Тест генерации ответа"""
    test_message = "привет казак"
    response = ai.generate_response(test_message)
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Тест генерации</h1>
            <p><strong>Сообщение:</strong> {test_message}</p>
            <p><strong>Сгенерированный ответ:</strong> {response}</p>
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
    logger.info("🎭 Бот с реальной генерацией ответов запущен!")
    logger.info("🌐 Откройте /test для проверки генерации")
    app.run(host='0.0.0.0', port=port)
