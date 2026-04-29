from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.storage.db import get_file
from app.services.telegram_client import bot_client
from config import get_settings

router = APIRouter()
settings = get_settings()


def _is_streamable(mime: str) -> bool:
    return mime.startswith('video/') or mime.startswith('audio/')


def _parse_range(range_header: str | None, file_size: int) -> tuple[int, int]:
    if not range_header or not range_header.startswith('bytes='):
        return 0, file_size - 1
    raw = range_header.replace('bytes=', '', 1)
    start_s, end_s = raw.split('-', 1)
    start = int(start_s) if start_s else 0
    end = int(end_s) if end_s else file_size - 1
    if start > end or end >= file_size:
        raise HTTPException(status_code=416, detail='Invalid range')
    return start, end


async def _tg_stream(file_id: str, offset: int, limit: int) -> AsyncGenerator[bytes, None]:
    async for chunk in bot_client.stream_media(file_id, limit=1024 * 1024, offset=offset):
        if limit <= 0:
            break
        if len(chunk) > limit:
            yield chunk[:limit]
            break
        yield chunk
        limit -= len(chunk)


@router.get('/health')
async def health() -> JSONResponse:
    return JSONResponse({'status': 'ok'})


@router.get('/d/{token}')
async def download(token: str, request: Request) -> StreamingResponse:
    record = await get_file(token)
    if not record:
        raise HTTPException(status_code=404, detail='File link not found or expired')

    start, end = _parse_range(request.headers.get('range'), record.file_size)
    length = end - start + 1
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(length),
        'Content-Type': record.mime_type,
    }
    if settings.force_download:
        headers['Content-Disposition'] = f'attachment; filename="{record.file_name}"'

    status_code = 206 if request.headers.get('range') else 200
    if status_code == 206:
        headers['Content-Range'] = f'bytes {start}-{end}/{record.file_size}'

    return StreamingResponse(_tg_stream(record.file_id, start, length), status_code=status_code, headers=headers)


@router.get('/s/{token}')
async def stream(token: str, request: Request) -> StreamingResponse:
    record = await get_file(token)
    if not record:
        raise HTTPException(status_code=404, detail='Stream link not found or expired')
    if not _is_streamable(record.mime_type):
        raise HTTPException(status_code=400, detail='Not a streamable media file')
    return await download(token, request)
