"""Cấu hình chung của TaskMate, đọc từ biến môi trường và file .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình ứng dụng. Các giá trị bí mật dùng SecretStr để không lộ khi in hoặc log."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Jira
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: SecretStr = SecretStr("")
    jira_mode: Literal["mock", "real"] = "mock"
    jira_story_points_field: str = "customfield_10016"
    jira_sprint_field: str = "customfield_10020"
    jira_flagged_field: str = "customfield_10021"

    # LLM
    llm_api_key: SecretStr = SecretStr("")
    llm_model_main: str = "claude-sonnet-5-5"
    llm_model_fast: str = "claude-haiku-5-5"

    # Human-in-the-loop
    approval_secret: SecretStr = SecretStr("")

    # Lưu trữ và múi giờ
    db_path: Path = Path("data/taskmate.db")
    timezone: str = "Asia/Ho_Chi_Minh"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = "https://cloud.langfuse.com"

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Múi giờ không hợp lệ: {value}") from exc
        return value

    @property
    def tz(self) -> ZoneInfo:
        """Đối tượng múi giờ dùng cho mọi phép tính ngày giờ."""
        return ZoneInfo(self.timezone)


@lru_cache
def get_settings() -> Settings:
    """Trả về Settings dùng chung cho toàn ứng dụng (đọc một lần)."""
    return Settings()
