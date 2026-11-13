import os
from pathlib import Path
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Переменные
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

# Схема для хранения параметров модели
class ModelParams(BaseModel):
    name: str
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_tokens: int | None = Field(default=None, ge=0, le=32768)


# ===== DeepSeek Settings =====
class DeepSeekSettings(BaseSettings):
    """Настройки для DeepSeek провайдера.

    Теперь все поля сделаны необязательными, чтобы приложение могло
    стартовать даже без соответствующих переменных окружения. При фактическом
    обращении к провайдеру должна выполняться дополнительная проверка на
    наличие необходимых параметров (base_url, model, api_key).
    """

    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None

    # Параметры модели
    name: str = "deepseek"
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_tokens: int | None = None

    @property
    def model_params(self) -> ModelParams:
        return ModelParams(
            name=self.name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="DEEPSEEK_"
    )

# ===== Yandex Settings =====
class YandexSettings(BaseSettings):
    """Настройки для Yandex провайдера (поля сделаны необязательными)."""

    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    folder: str | None = None

    # Параметры модели
    name: str = "yandex"
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_tokens: int | None = Field(default=None, ge=0, le=32768)

    @property
    def model_params(self) -> ModelParams:
        return ModelParams(
            name=self.name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="YANDEX_"
    )

# ===== OpenAI Settings =====
class OpenAISettings(BaseSettings):
    """Настройки для OpenAI провайдера (поля сделаны необязательными)."""

    # Базовый публичный endpoint OpenAI
    base_url: str | None = "https://api.openai.com/v1"
    model: str | None = "gpt-4o-mini"
    api_key: str | None = None

    # Параметры модели
    name: str = "openai"
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_tokens: int | None = None

    # Прокси, предоставленный пользователем
    proxy_url: str | None = None

    @property
    def model_params(self) -> ModelParams:
        return ModelParams(
            name=self.name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="OPENAI_"
    )

class LangfuseSettings(BaseSettings):
    """Настройки для Langfuse (поля сделаны необязательными)."""

    enabled: bool = True
    public_key: str | None = None
    secret_key: str | None = None
    host: str | None = None
    flush_interval: int = Field(default=10, ge=1, le=30)

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="LANGFUSE_"
    )

# Все настройки проекта
class Settings(BaseSettings):
    # Общие настройки приложения
    app_name: str = Field(default="AI Analysis Service", alias = "API_NAME")
    app_host: str = Field(default="0.0.0.0", alias = "API_HOST")
    app_port: int = Field(default=8000, alias = "API_PORT")

    # Логирование
    log_level: str = Field(default="INFO", alias = "LOG_LEVEL")
    write_logs_to_file: bool = Field(default=False, alias = "WRITE_LOGS_TO_FILE")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Настройки провайдеров
    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    yandex: YandexSettings = Field(default_factory=YandexSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)

settings = Settings()
