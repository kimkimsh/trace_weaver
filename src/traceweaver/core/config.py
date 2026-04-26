"""User-facing configuration — Pydantic BaseSettings.

Resolution chain (highest priority first), per
``docs/plan/01_dev_environment.md §1.12``:

1. CLI flags          (handled in ``traceweaver.cli`` per command)
2. Environment vars   (``TW_*``)
3. ``$XDG_CONFIG_HOME/traceweaver/config.toml``
4. Built-in defaults  (this file)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from traceweaver.core.paths import config_home, data_home


class CollectorToggles(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TW_COLLECTORS_", extra="ignore")

    shell: bool = True
    git: bool = True
    fs: bool = True
    browser: bool = False
    tmux: bool = True
    tilix: bool = False


class DaemonSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TW_DAEMON_", extra="ignore")

    bind_address: str = Field(default="127.0.0.1", description="Loopback only — ADR-1.")
    http_port: int = 7777
    socket_path: Path | None = None  # default = paths.hook_socket() at runtime
    watchdog_sec: int = 60


class ExtractionSettings(BaseSettings):
    """ADR-15: user-configurable extraction schedule."""

    model_config = SettingsConfigDict(env_prefix="TW_EXTRACTION_", extra="ignore")

    mode: Literal["auto", "manual"] = "auto"
    interval_seconds: int = Field(default=1800, ge=60, le=86_400)


class ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TW_MODEL_", extra="ignore")

    backend: Literal["openvino", "ollama", "llama_cpp", "rules"] = "rules"
    model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    device: Literal["auto", "npu", "gpu", "cpu"] = "auto"


class RetentionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TW_RETENTION_", extra="ignore")

    raw_events_days: int = 30
    summaries_days: int = 180
    audit_days: int = 365


class Settings(BaseSettings):
    """Top-level runtime configuration."""

    model_config = SettingsConfigDict(extra="ignore")

    daemon: DaemonSettings = Field(default_factory=DaemonSettings)
    collectors: CollectorToggles = Field(default_factory=CollectorToggles)
    extraction: ExtractionSettings = Field(default_factory=ExtractionSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    retention: RetentionSettings = Field(default_factory=RetentionSettings)

    @property
    def database_url(self) -> str:
        # aiosqlite URL for SQLAlchemy async engine.
        return f"sqlite+aiosqlite:///{data_home() / 'events.db'}"

    @property
    def config_file(self) -> Path:
        return config_home() / "config.toml"


def load_settings() -> Settings:
    """Build the live ``Settings`` from env + defaults.

    NOTE: TOML overlay (priority 3) is left as a follow-up — the v1
    implementation reads env + defaults only and TOML support arrives
    when first user-facing setting demands it. See
    ``docs/plan/01_dev_environment.md §1.12.4``.
    """
    return Settings()
