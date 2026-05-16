from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Централизованная конфигурация приложения.
    Значения читаются из переменных окружения и .env файла.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорируем неизвестные env-переменные
        case_sensitive=False,
    )

    # 🌍 Окружение
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

    # 🌐 API
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_title: str = "NewsMap API"
    api_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 🗄️ База данных
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@newsmap-database:5432/database",
        description="PostgreSQL async URL",
    )
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=10, ge=0)
    db_echo: bool = False

    # 🌍 Внешние сервисы
    nominatim_user_agent: str = "NewsMap/1.0 (dev@example.com)"
    nominatim_timeout: float = Field(default=10.0, gt=0)
    parser_concurrency: int = Field(default=5, ge=1, le=50)
    parser_user_agent: str = "NewsMap Parser/1.0"

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise ValueError(
                "database_url должен быть PostgreSQL async URL (postgresql+asyncpg://...)"
            )
        return v

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    @property
    def is_prod(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Кэширует экземпляр Settings на весь жизненный цикл процесса.
    Вызовы после первого будут мгновенными (~0.0001ms).
    """
    return Settings()
