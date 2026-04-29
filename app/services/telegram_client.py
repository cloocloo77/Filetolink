from pyrogram import Client
from config import get_settings

settings = get_settings()

bot_client = Client(
    'filetolink-bot',
    api_id=settings.api_id,
    api_hash=settings.api_hash,
    bot_token=settings.bot_token,
    in_memory=True,
)
