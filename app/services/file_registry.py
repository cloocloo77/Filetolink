from app.storage.db import FileRecord, save_file, get_by_unique, new_expiry
from app.services.token_service import generate_token
from config import get_settings

settings = get_settings()


async def register_file(*, file_id: str, file_unique_id: str, file_name: str, mime_type: str, file_size: int) -> FileRecord:
    cached = await get_by_unique(file_unique_id)
    if cached:
        return cached

    record = FileRecord(
        token=generate_token(),
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_name=file_name,
        mime_type=mime_type or 'application/octet-stream',
        file_size=file_size,
        expires_at=new_expiry(settings.file_expiry_hours),
    )
    await save_file(record)
    return record
