import os
from pathlib import Path
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Changed
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

# Schematic to store model parameters
class ModelParams(BaseModel):
    name: str
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_tokens: int | None = Field(default=None, ge=0, le=32768)


# ===== DeepSeek Settings =====
class DeepSeekSettings(BaseSettings):
    """It's for DeepSeek's service provider.

    Now all fields are made optional so the application can
    Start even without appropriate variables. Actual
    Additional testing of the service provider should be carried out
    Availability of necessary parameters (base_url, model, api_key)).
    """

    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None

    # Model Options
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
    'Mandex Provider settings (fields made optional)).'

    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    folder: str | None = None

    # Model Options
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
    'OpenAI service provider settings (fields made optional)).'

    # Basic Public Endpoint OpenAI
    base_url: str | None = "https://api.openai.com/v1"
    model: str | None = "gpt-4o-mini"
    api_key: str | None = None

    # Model Options
    name: str = "openai"
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_tokens: int | None = None

    # Proxie provided by the user
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
    '== sync, corrected by elderman == @elder_man'

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

# All Project Settings
class Settings(BaseSettings):
    # General application settings
    app_name: str = Field(default="AI Analysis Service", alias = "API_NAME")
    app_host: str = Field(default="0.0.0.0", alias = "API_HOST")
    app_port: int = Field(default=8000, alias = "API_PORT")

    # Logging
    log_level: str = Field(default="INFO", alias = "LOG_LEVEL")
    write_logs_to_file: bool = Field(default=False, alias = "WRITE_LOGS_TO_FILE")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Providers &apos; settings
    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    yandex: YandexSettings = Field(default_factory=YandexSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)

settings = Settings()
