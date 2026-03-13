from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings."""

    database_url: str = "sqlite:///./data/db.sqlite"

    model_config = SettingsConfigDict(
        env_prefix="NOVEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_database_url(self) -> str:
        database_url = self.database_url.strip()
        if database_url.startswith("sqlite:///"):
            sqlite_path = database_url.removeprefix("sqlite:///")
            normalized = Path(sqlite_path).as_posix()
            return f"sqlite:///{normalized}"
        return database_url


settings = Settings()
