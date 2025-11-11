import os
import logging
import requests
import threading
import time
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8326410603:AAHeqICzU7ASRkr0xyDgmxP0a0ah2j4JMN4"

app = Flask(__name__)

active_chats = set()

class DogBot:
    def __init__(self):
        self.interval = 102
        self.is_running = False
        self.thread = None
    
    def start_barking(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._barking_loop, daemon=True)
        self.thread.start()
    
    def _barking_loop(self):
        while self.is_running:
            time.sleep(self.interval)
            if active_chats:
                self._bark_in_all_chats()
    
    def _bark_in_all_chats(self):
        for chat_id in list(active_chats):
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                data = {"chat_id": chat_id, "text": "гав"}
                requests.post(url, json=data, timeout=10)
            except:
                active_chats.discard(chat_id)
    
    def add_chat(self, chat_id):
        active_chats.add(chat_id)

dog_bot = DogBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            dog_bot.add_chat(chat_id)
        return jsonify({'status': 'ok'})
    except:
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    return ""

def set_webhook():
    try:
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        if render_url:
            webhook_url = f"{render_url}/webhook"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            requests.post(url, json={"url": webhook_url})
    except:
        pass

if __name__ == '__main__':
    set_webhook()
    dog_bot.start_barking()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
