# Overview

This is a Telegram chatbot that uses Groq's AI API to respond to messages. The bot has a specific personality - it acts as a teenage fish character named "Даня казак" (Danya Kazak) that only responds to messages containing the word "буль" (bul). The bot uses a post-ironic, sarcastic communication style with youth slang and informal language.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Technology**: Python Telegram Bot library (`python-telegram-bot`)
- **Pattern**: Event-driven message handler architecture
- **Rationale**: The bot uses the telegram.ext Application framework which provides a clean, asynchronous interface for handling Telegram updates. This approach simplifies webhook/polling management and message routing.

## AI Integration
- **Provider**: Groq API
- **Model**: Not specified in code (using default)
- **Approach**: Direct API integration using the official Groq Python client
- **Rationale**: Groq provides fast LLM inference with a simple API. The system prompt defines the bot's personality and behavior constraints.

## Message Processing
- **Filter Logic**: Only processes messages containing the word "буль"
- **Handler Type**: MessageHandler with text filters
- **Processing**: Synchronous processing of messages - each message triggers a single API call to Groq with the system prompt and user message

## Configuration Management
- **Method**: Environment variables
- **Required Variables**:
  - `TELEGRAM_BOT_TOKEN`: Telegram bot authentication token
  - `GROQ_API_KEY`: Groq API authentication key
- **Rationale**: Environment variables provide secure credential storage and easy deployment configuration

## Error Handling & Logging
- **Logging**: Standard Python logging module with INFO level
- **Format**: Timestamp, logger name, level, and message
- **Scope**: Currently logs received messages containing the trigger word

# External Dependencies

## APIs & Services
1. **Telegram Bot API**
   - Purpose: Receive and send messages via Telegram
   - Authentication: Bot token via environment variable
   - Integration: `python-telegram-bot` library

2. **Groq API**
   - Purpose: Generate AI responses based on system prompt and user input
   - Authentication: API key via environment variable
   - Integration: Official `groq` Python client library

## Python Libraries
- `python-telegram-bot`: Telegram bot framework
- `groq`: Groq API client for LLM inference
- Standard library: `os`, `logging`

## Runtime Requirements
- Python 3.x (version not specified)
- Environment variables must be configured before runtime
- Internet connectivity for API access