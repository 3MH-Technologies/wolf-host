from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid
import re

from app.models.bot import BotStatus, BotSourceType


class BotCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    source_type: BotSourceType
    git_url: str | None = None
    entrypoint: str = "main.py"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\- ]+$", value):
            raise ValueError("name_invalid_characters")
        return value

    @field_validator("entrypoint")
    @classmethod
    def validate_entrypoint(cls, value: str) -> str:
        if ".." in value or value.startswith("/"):
            raise ValueError("entrypoint_invalid")
        if not value.endswith(".py"):
            raise ValueError("entrypoint_must_be_python")
        return value


class BotEnvUpdateRequest(BaseModel):
    env_vars: dict[str, str]


class BotResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    source_type: BotSourceType
    status: BotStatus
    entrypoint: str
    container_name: str
    env_vars: dict[str, str] = {}
    cpu_limit: float
    ram_limit_mb: int
    disk_limit_mb: int
    process_limit: int
    auto_restart: bool
    restart_count: int
    created_at: datetime
    last_started_at: datetime | None

    model_config = {"from_attributes": True}


class BotStatsResponse(BaseModel):
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    memory_percent: float
    network_rx_bytes: int
    network_tx_bytes: int


class FileEntry(BaseModel):
    name: str
    is_dir: bool
    size: int
    modified_at: float


class FileWriteRequest(BaseModel):
    content: str


class FileRenameRequest(BaseModel):
    new_name: str


class FileMoveRequest(BaseModel):
    destination: str
