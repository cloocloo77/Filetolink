import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

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
    await bot_client.start()
    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        await bot_client.stop()


app = FastAPI(title='Telegram FileToLink', lifespan=lifespan)
app.include_router(router)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'bot':
        asyncio.run(bot_client.start())
        asyncio.get_event_loop().run_forever()
    else:
        uvicorn.run('main:app', host='0.0.0.0', port=settings.port, reload=False)
