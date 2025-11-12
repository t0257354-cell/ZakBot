import os
import logging
import requests
import re
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get tokens from environment variables (Render automatically provides these)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

app = Flask(__name__)

class HuggingFaceAI:
    def __init__(self):
        # Use models that definitely exist and work
        self.models = [
            "microsoft/DialoGPT-small",    # Small and fast
            "microsoft/DialoGPT-medium",   # Medium size
            "gpt2",                        # Always available
            "facebook/blenderbot-400M-distill"  # Chat model
        ]
        self.current_model = 0
    
    def generate_response(self, user_message):
        """Generate response through Hugging Face API"""
        if not HF_TOKEN:
            logger.error("❌ HF_TOKEN not set")
            return None
            
        # Try all models until one works
        for i in range(len(self.models)):
            model_name = self.models[self.current_model]
            
            try:
                api_url = f"https://api-inference.huggingface.co/models/{model_name}"
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                
                prompt = f"""Ты - юмористическая версия Алексея Навального. Отвечай на сообщения о казаках с юмором и иронией, но без политики.

Сообщение: {user_message}

Юмористический ответ:"""
                
                logger.info(f"🔄 Trying model: {model_name}")
                
                response = requests.post(
                    api_url,
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_length": 150,
                            "temperature": 0.9,
                            "do_sample": True,
                            "top_p": 0.9
                        }
                    },
                    timeout=30
                )
                
                logger.info(f"📡 Model {model_name} status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        
                        # Extract only the response after prompt
                        response_text = generated_text.replace(prompt, '').strip()
                        
                        # Clean up response
                        response_text = re.sub(r'^[^а-яА-Я]*', '', response_text)
                        
                        if response_text and len(response_text) > 10:
                            logger.info(f"✅ Success with {model_name}: {response_text}")
                            return response_text
                
                elif response.status_code == 404:
                    logger.warning(f"❌ Model {model_name} not found, trying next...")
                    self.current_model = (self.current_model + 1) % len(self.models)
                    continue
                    
                elif response.status_code == 503:
                    logger.warning(f"⏳ Model {model_name} loading...")
                    # Try next model
                    self.current_model = (self.current_model + 1) % len(self.models)
                    continue
                    
                else:
                    logger.warning(f"⚠️ Model {model_name} error {response.status_code}, trying next...")
                    self.current_model = (self.current_model + 1) % len(self.models)
                    continue
                    
            except Exception as e:
                logger.error(f"🔥 Error with {model_name}: {e}")
                self.current_model = (self.current_model + 1) % len(self.models)
                continue
        
        logger.error("❌ All models failed")
        return None

# Initialize AI
ai = HuggingFaceAI()

def contains_kazak(text):
    if not text or not isinstance(text, str):
        return False
    pattern = r'\b[Кк]аза[кч]\w*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def send_message(chat_id, text):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set")
        return
        
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Sent: {text}")
        else:
            logger.error(f"❌ Send failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Send error: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        
        if 'message' not in update or 'text' not in update['message']:
            return jsonify({'status': 'ok'})
        
        message = update['message']
        chat_id = message['chat']['id']
        user_message = message['text']
        
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ok'})
        
        if contains_kazak(user_message):
            logger.info(f"🎯 Found 'kazak': {user_message}")
            
            response = ai.generate_response(user_message)
            
            if response:
                send_message(chat_id, response)
            else:
                logger.info("🤐 Generation failed - staying silent")
        
        return jsonify({'status': 'ok'})
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    bot_status = "✅ Configured" if BOT_TOKEN else "❌ Not set"
    hf_status = "✅ Configured" if HF_TOKEN else "❌ Not set"
    
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Telegram Bot Status</h1>
            <p>BOT_TOKEN: {bot_status}</p>
            <p>HF_TOKEN: {hf_status}</p>
            <p>Current model: {ai.models[ai.current_model] if ai.models else 'None'}</p>
            <p><a href="/test">Test Generation</a></p>
        </body>
    </html>
    """

@app.route('/test')
def test_generation():
    test_message = "привет казак"
    response = ai.generate_response(test_message)
    
    if response:
        status = "✅ Successful generation"
    else:
        status = "❌ Generation failed"
    
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Hugging Face Generation Test</h1>
            <p><strong>Message:</strong> {test_message}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Response:</strong> {response if response else 'No response'}</p>
            <p><a href="/">Home</a></p>
        </body>
    </html>
    """

def set_webhook():
    if not BOT_TOKEN:
        logger.error("❌ Cannot set webhook - BOT_TOKEN not set")
        return
        
    try:
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        if render_url:
            webhook_url = f"{render_url}/webhook"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            requests.post(url, json={"url": webhook_url})
            logger.info(f"✅ Webhook set: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook setup error: {e}")

if __name__ == '__main__':
    # Check if tokens are set
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable not set!")
    if not HF_TOKEN:
        logger.error("❌ HF_TOKEN environment variable not set!")
    
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    logger.info("🎭 Bot started with multiple model fallbacks!")
    app.run(host='0.0.0.0', port=port)
