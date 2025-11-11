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

app = Flask(__name__)

class FastDogAI:
    def __init__(self):
        # БЫСТРЫЕ модели которые почти всегда загружены
        self.fast_models = [
            # 1. Самые быстрые (загружены почти всегда)
            "gpt2",                                  # ⚡ Мгновенно
            "distilgpt2",                            # ⚡ Еще быстрее
            "microsoft/DialoGPT-small",              # ⚡ Для диалогов
            
            # 2. Русскоязычные быстрые
            "sberbank-ai/rugpt3small_based_on_gpt2", # 🇷🇺 Русский, быстро
            "inkoziev/gpt2_chitchat_ru",             # 🇷🇺 Русские диалоги
            
            # 3. Резервные
            "microsoft/DialoGPT-medium",             # ✅ Надежный
            "facebook/blenderbot_small-90M"          # ✅ Легкий
        ]
        self.current_model_index = 0
        self.model_status = {}
        
    def test_model_speed(self, model_name):
        """Тестируем скорость модели"""
        try:
            api_url = f"https://api-inference.huggingface.co/models/{model_name}"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            # Короткий тестовый промпт
            test_prompt = "Привет"
            
            start_time = requests.time.time()
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    "inputs": test_prompt,
                    "parameters": {"max_length": 15, "max_time": 10}
                },
                timeout=15
            )
            response_time = requests.time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"✅ {model_name}: {response_time:.1f}сек")
                return True, response_time
            else:
                logger.warning(f"⚠️ {model_name}: ошибка {response.status_code}")
                return False, response_time
                
        except Exception as e:
            logger.error(f"❌ {model_name}: {e}")
            return False, 999
    
    def find_fastest_model(self):
        """Находим самую быструю модель"""
        logger.info("🏎️ Ищем самую быструю модель...")
        model_speeds = []
        
        for model in self.fast_models:
            works, speed = self.test_model_speed(model)
            if works:
                model_speeds.append((model, speed))
        
        if model_speeds:
            # Сортируем по скорости (самые быстрые первыми)
            model_speeds.sort(key=lambda x: x[1])
            fastest_model = model_speeds[0][0]
            logger.info(f"🎯 Самая быстрая модель: {fastest_model}")
            return fastest_model
        else:
            logger.error("🚨 Все модели недоступны")
            return None
    
    def get_dog_response(self, user_message):
        """Получаем ответ используя самую быструю модель"""
        # Сначала пробуем предварительно найденную быструю модель
        if hasattr(self, 'fastest_model') and self.fastest_model:
            response = self.try_model(self.fastest_model, user_message)
            if response:
                return response
        
        # Если быстрая не сработала, пробуем все по очереди
        for model in self.fast_models:
            response = self.try_model(model, user_message)
            if response:
                # Запоминаем рабочую модель для следующих запросов
                self.fastest_model = model
                return response
        
        # Если ничего не сработало
        return self.get_fallback_dog_response()
    
    def try_model(self, model_name, user_message):
        """Пробуем получить ответ от конкретной модели"""
        try:
            api_url = f"https://api-inference.huggingface.co/models/{model_name}"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            # Оптимизированный промпт для скорости
            if "ru" in model_name.lower() or "rugpt" in model_name:
                # Для русских моделей
                prompt = f"Ты собака. Отвечай кратко: {user_message}\nОтвет:"
            else:
                # Для английских моделей
                prompt = f"""You are a dog. Reply briefly in Russian with dog sounds like гав, вуф.

Human: {user_message}
Dog:"""
            
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 40,        # ⬅️ КОРОЧЕ для скорости
                        "max_time": 8,          # ⬅️ Таймаут короче
                        "temperature": 0.7,
                        "do_sample": True
                    }
                },
                timeout=10  # ⬅️ Короткий таймаут
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    response_text = generated.replace(prompt, '').strip()
                    
                    # Базовая очистка
                    response_text = re.sub(r'^[^а-яА-Я]*', '', response_text)
                    
                    if response_text and len(response_text) > 2:
                        logger.info(f"✅ {model_name}: {response_text}")
                        return response_text
            
            return None
                
        except Exception as e:
            logger.warning(f"⚠️ {model_name} не сработала: {e}")
            return None
    
    def get_fallback_dog_response(self):
        """Запасные ответы"""
        dog_responses = [
            "Гав! Я собака Казака! 🐕",
            "Вуф-вуф! Даниил - мой хозяин! 🦴", 
            "Ррр... Гав! Я пёс! 🐾",
            "Гав-гав! Казак - мой человек! 🐶",
            "Вуф! Я в телефоне! 📱"
        ]
        return random.choice(dog_responses)

# Инициализация AI
dog_ai = FastDogAI()

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
        
        # Игнорируем ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        # Реагируем на "казак"
        if contains_kazak(user_message):
            logger.info(f"🎯 Казак: {user_message}")
            dog_response = dog_ai.get_dog_response(user_message)
            send_message(chat_id, dog_response)
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    return """
    <html>
        <head><title>Собака Казака 🐶</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <div style="font-size: 48px;">🐕</div>
            <h1>Собака Казака</h1>
            <p style="color: green;">Бот работает! Реагирует на "казак"</p>
            <p>Использует быстрые AI модели</p>
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
            requests.post(url, json={"url": webhook_url})
            logger.info(f"✅ Вебхук: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Вебхук: {e}")

if __name__ == '__main__':
    # Находим самую быструю модель при запуске
    dog_ai.fastest_model = dog_ai.find_fastest_model()
    
    # Устанавливаем вебхук
    set_webhook()
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
