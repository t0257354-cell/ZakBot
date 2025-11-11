import os
import logging
import re
import requests
import time
import random

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
HF_TOKEN = "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"

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

def handle_update(update_data):
    """Обработчик обновлений"""
    try:
        if 'message' not in update_data or 'text' not in update_data['message']:
            return
        
        message = update_data['message']
        chat_id = message['chat']['id']
        user_message = message['text']
        chat_type = message['chat'].get('type', 'private')
        
        # Логируем информацию о чате
        logger.info(f"📨 Message in {chat_type} chat {chat_id}: {user_message}")
        
        # Игнорируем сообщения от ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return
        
        # Реагируем ТОЛЬКО на слово "казак"
        if contains_kazak(user_message):
            logger.info(f"🎯 Казак detected in {chat_type} chat!")
            
            # Получаем ответ от собаки
            dog_response = dog_ai.get_dog_response(user_message)
            
            # Отправляем ответ
            send_message(chat_id, dog_response)
            
    except Exception as e:
        logger.error(f"Error handling update: {e}")

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

def get_updates(offset=None):
    """Получение обновлений через long polling"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            "timeout": 30,
            "offset": offset
        }
        response = requests.get(url, params=params, timeout=35)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return data['result']
            else:
                logger.error(f"Telegram API error: {data}")
        else:
            logger.error(f"HTTP error: {response.status_code}")
            
        return []
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return []

def set_webhook_info():
    """Устанавливаем информацию о боте для групп"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyName"
        data = {"name": "Собака Казака 🐶"}
        requests.post(url, json=data)
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyDescription"
        data = {"description": "Я собака Даниила Казака! Гав! 🐕"}
        requests.post(url, json=data)
        
        logger.info("✅ Bot profile updated")
    except Exception as e:
        logger.error(f"Error setting bot info: {e}")

def main():
    """Основной цикл бота"""
    logger.info("🐶 Собака Казака запущена!")
    logger.info("🎯 Реагирует только на слово 'казак'")
    logger.info("👥 Работает в личных сообщениях и группах")
    
    # Устанавливаем информацию о боте
    set_webhook_info()
    
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            for update in updates:
                handle_update(update)
                offset = update['update_id'] + 1
                
            # Если нет обновлений, ждем немного
            if not updates:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
