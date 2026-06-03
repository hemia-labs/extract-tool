from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    max_file_size_mb: int = 25
    max_pdf_pages: int = 50
    max_image_pixels: int = 20_000_000
    ocr_default_language: str = "spa+eng"
    request_timeout_seconds: int = 60
    temp_dir: Path = Path("/tmp/hemia-extract")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
