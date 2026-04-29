from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer, select, delete

from config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class FileRecord(Base):
    __tablename__ = 'file_records'

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_id: Mapped[str] = mapped_column(String(255), index=True)
    file_unique_id: Mapped[str] = mapped_column(String(255), index=True)
    file_name: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(128), default='application/octet-stream')
    file_size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_file(record: FileRecord) -> None:
    async with SessionLocal() as session:
        session.add(record)
        await session.commit()


async def get_file(token: str) -> FileRecord | None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(FileRecord).where(
                FileRecord.token == token,
                FileRecord.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()


async def get_by_unique(unique_id: str) -> FileRecord | None:
    async with SessionLocal() as session:
        result = await session.execute(select(FileRecord).where(FileRecord.file_unique_id == unique_id))
        return result.scalars().first()


async def cleanup_expired() -> int:
    async with SessionLocal() as session:
        result = await session.execute(delete(FileRecord).where(FileRecord.expires_at < datetime.now(UTC)))
        await session.commit()
        return result.rowcount or 0


def new_expiry(hours: int) -> datetime:
    return datetime.now(UTC) + timedelta(hours=hours)
