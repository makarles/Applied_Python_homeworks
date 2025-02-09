import os
from dotenv import load_dotenv
from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from loguru import logger

# Загружаем переменные окружения из файла .env
load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
CALORIENINJAS_API_KEY = os.environ.get("CALORIENINJAS_API_KEY")
API_NINJAS_CALORIES_BURNED_API_KEY = os.environ.get("API_NINJAS_CALORIES_BURNED_API_KEY")

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        logger.info(f"Получено сообщение от {event.from_user.id}: {event.text}")
        return await handler(event, data)
