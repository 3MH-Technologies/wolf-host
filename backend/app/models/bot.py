import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, func, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.session import Base


class BotStatus(str, enum.Enum):
    CREATED = "created"
    INSTALLING = "installing"
    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    DELETING = "deleting"
    ERROR = "error"


class BotSourceType(str, enum.Enum):
    ZIP = "zip"
    SINGLE_FILE = "single_file"
    GIT = "git"


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    source_type: Mapped[BotSourceType] = mapped_column(Enum(BotSourceType))
    git_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    entrypoint: Mapped[str] = mapped_column(String(255), default="main.py")
    status: Mapped[BotStatus] = mapped_column(Enum(BotStatus), default=BotStatus.CREATED)
    container_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    container_name: Mapped[str] = mapped_column(String(160), unique=True)
    storage_path: Mapped[str] = mapped_column(String(512))
    env_vars: Mapped[dict] = mapped_column(JSONB, default=dict)
    cpu_limit: Mapped[float] = mapped_column(default=0.5)
    ram_limit_mb: Mapped[int] = mapped_column(Integer, default=256)
    disk_limit_mb: Mapped[int] = mapped_column(Integer, default=512)
    process_limit: Mapped[int] = mapped_column(Integer, default=32)
    restart_policy: Mapped[str] = mapped_column(String(32), default="unless-stopped")
    auto_restart: Mapped[bool] = mapped_column(Boolean, default=True)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="bots")
