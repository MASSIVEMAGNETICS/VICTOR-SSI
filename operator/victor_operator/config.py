from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    api_token: str = Field(alias="VICTOR_API_TOKEN", min_length=16)
    host: str = Field(default="127.0.0.1", alias="VICTOR_HOST")
    port: int = Field(default=8765, alias="VICTOR_PORT", ge=1, le=65535)
    workspace: Path = Field(default=Path.home() / "VictorWorkspace", alias="VICTOR_WORKSPACE")
    data_dir: Path = Field(default=Path.home() / ".victor-operator", alias="VICTOR_DATA_DIR")
    allowed_domains: list[str] = Field(default_factory=list, alias="VICTOR_ALLOWED_DOMAINS")
    browser_headless: bool = Field(default=False, alias="VICTOR_BROWSER_HEADLESS")
    browser_channel: str | None = Field(default="chrome", alias="VICTOR_BROWSER_CHANNEL")
    max_steps: int = Field(default=40, alias="VICTOR_MAX_STEPS", ge=1, le=200)
    command_timeout_seconds: int = Field(
        default=120, alias="VICTOR_COMMAND_TIMEOUT_SECONDS", ge=5, le=1800
    )

    @field_validator("workspace", "data_dir", mode="before")
    @classmethod
    def expand_path(cls, value: object) -> Path:
        raw = os.path.expandvars(os.path.expanduser(str(value)))
        return Path(raw).resolve()

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def split_domains(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [part.strip().lower() for part in value.split(";") if part.strip()]
        return list(value or [])

    def prepare(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "screenshots").mkdir(exist_ok=True)
        (self.data_dir / "backups").mkdir(exist_ok=True)
