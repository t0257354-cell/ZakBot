import os
import logging
import re
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"
HF_TOKEN = "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"

# Хранилище в памяти
chat_history = {}
MAX_HISTORY = 10

class HuggingFaceAI:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def get_response(self, context):
        """Получаем ответ от Hugging Face"""
        try:
            prompt = f"""
Ты - казак в Telegram чате. Отвечай кратко (1 предложение) в казачьем стиле с юмором.
Контекст: {context}
Твой ответ:"""
            
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 80,
                        "temperature": 0.8,
                        "do_sample": True
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    # Извлекаем только ответ
                    response_text = generated.replace(prompt, '').strip()
                    return response_text if response_text else "Так точно! 🐎"
                return "За Дон и волю! 💪"
            else:
                return "Эх, задумался... 🤔"
                
        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            return "Шашка затупилась... ⚔️"

# Инициализация AI
ai_client = HuggingFaceAI()

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
        
        # Игнорируем сообщения от ботов
        if 'from' in message and message['from'].get('is_bot', False):
            return
        
        # Инициализируем историю для чата
        if chat_id not in chat_history:
            chat_history[chat_id] = []
        
        # Добавляем сообщение в историю
        user_name = message['from'].get('first_name', 'User')
        chat_history[chat_id].append(f"{user_name}: {user_message}")
        
        # Ограничиваем историю
        if len(chat_history[chat_id]) > MAX_HISTORY:
            chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]
        
        # Реагируем ТОЛЬКО на слово "казак"
        if contains_kazak(user_message):
            logger.info(f"Казак detected: {user_message}")
            
            # Берем последние 5 сообщений для контекста
            recent_history = chat_history[chat_id][-5:]
            context_text = "\n".join(recent_history)
            
            # Получаем ответ от ИИ
            ai_response = ai_client.get_response(context_text)
            
            # Отправляем ответ через простой HTTP запрос
            send_message(chat_id, ai_response)
            
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
        requests.post(url, json=data, timeout=10)
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
        return []
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return []

def main():
    """Основной цикл бота"""
    logger.info("🤠 Казак-бот запущен - реагирует только на слово 'казак'")
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            for update in updates:
                handle_update(update)
                offset = update['update_id'] + 1
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            import time
            time.sleep(5)

if __name__ == "__main__":
    main()
