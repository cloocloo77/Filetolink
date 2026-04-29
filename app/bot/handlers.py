from pyrogram import filters
from pyrogram.types import Message

from config import get_settings
from app.services.telegram_client import bot_client
from app.services.file_registry import register_file

settings = get_settings()


@bot_client.on_message(filters.command('start'))
async def start_handler(_, message: Message) -> None:
    await message.reply_text('Send me any file up to 2GB and I will generate download/stream links.')


@bot_client.on_message(filters.command('help'))
async def help_handler(_, message: Message) -> None:
    await message.reply_text('Upload a document/video/audio. I return direct and stream links (if media).')


@bot_client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def file_handler(_, message: Message) -> None:
    media = message.document or message.video or message.audio
    if not media:
        return

    if media.file_size and media.file_size > settings.max_file_size:
        await message.reply_text('File exceeds MAX_FILE_SIZE limit configured on this bot.')
        return

    progress_msg = await message.reply_text('Processing file...')
    record = await register_file(
        file_id=media.file_id,
        file_unique_id=media.file_unique_id,
        file_name=media.file_name or f'{media.file_unique_id}.bin',
        mime_type=media.mime_type or 'application/octet-stream',
        file_size=media.file_size or 0,
    )

    dl = f"{settings.base_url.rstrip('/')}/d/{record.token}"
    is_streamable = record.mime_type.startswith('video/') or record.mime_type.startswith('audio/')
    stream_text = f"\n• Stream: {settings.base_url.rstrip('/')}/s/{record.token}" if is_streamable else ''

    await progress_msg.edit_text(
        f"✅ Links generated\n"
        f"• Name: {record.file_name}\n"
        f"• Size: {record.file_size} bytes\n"
        f"• MIME: {record.mime_type}\n"
        f"• Download: {dl}{stream_text}"
    )
