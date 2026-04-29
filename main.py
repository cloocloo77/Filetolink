import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from pyrogram import idle

from app.api.stream import router
from app.storage.db import init_db, cleanup_expired
from app.services.telegram_client import bot_client
import app.bot.handlers  # noqa: F401
from config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)


async def cleanup_loop() -> None:
    while True:
        removed = await cleanup_expired()
        if removed:
            logging.info('cleanup_removed=%s', removed)
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    cleanup_task = asyncio.create_task(cleanup_loop())
    bot_running = False

    if settings.run_bot:
        await bot_client.start()
        bot_running = True
        logging.info('Telegram bot polling started in API process (RUN_BOT=true).')

    try:
        yield
    finally:
        cleanup_task.cancel()
        if bot_running:
            await bot_client.stop()


app = FastAPI(title='Telegram FileToLink', lifespan=lifespan)
app.include_router(router)


async def run_bot_only() -> None:
    await init_db()
    await bot_client.start()
    logging.info('Bot-only process started.')
    try:
        await idle()
    finally:
        await bot_client.stop()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'bot':
        asyncio.run(run_bot_only())
    else:
        uvicorn.run('main:app', host='0.0.0.0', port=settings.port, reload=False)
