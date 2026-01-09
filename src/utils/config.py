"""
Configuration management for DocMind-AI.
"""

from typing import ClassVar, Any
from threading import Lock
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    provider: str  # "openai" or "anthropic"
    cost_per_1k_tokens: float = 0.0


class Config(BaseSettings):
    """Application configuration with singleton pattern."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # API Keys
    openai_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)

    # Azure OpenAI Configuration
    azure_openai_api_key: str | None = Field(default=None)
    azure_openai_endpoint: str | None = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-12-01-preview")
    azure_openai_deployment_name: str | None = Field(default=None)
    azure_openai_vision_deployment: str | None = Field(default=None)

    # Azure Anthropic Configuration
    azure_anthropic_api_key: str | None = Field(default=None)
    azure_anthropic_endpoint: str | None = Field(default=None)
    azure_anthropic_api_version: str = Field(default="2024-01-01")
    azure_anthropic_deployment_name: str | None = Field(default=None)

    # Model Configuration
    text_extraction_model: str = Field(default="gpt-4o-mini")
    text_extraction_provider: str = Field(default="openai")

    vision_model: str = Field(default="gpt-4o")
    vision_provider: str = Field(default="openai")

    advanced_model: str = Field(default="claude-sonnet-4-5")
    advanced_provider: str = Field(default="anthropic")

    validator_model: str = Field(default="gpt-4.1")
    validator_provider: str = Field(default="openai")

    # Adaptive Routing
    enable_adaptive_routing: bool = Field(default=True)
    auto_model_selection: bool = Field(default=True)

    # Cost Limits
    max_cost_per_document: float = Field(default=1.0)
    max_cost_per_page: float = Field(default=0.1)
    enable_cost_tracking: bool = Field(default=True)
    cost_alert_threshold: float = Field(default=0.5)

    # Processing Configuration
    max_parallel_pages: int = Field(default=5)
    enable_vision_fallback: bool = Field(default=True)
    enable_quality_validation: bool = Field(default=True)

    # Model Fallback Chains
    text_fallback_models: str | list[str] = Field(
        default="gpt-4o-mini,gpt-4o,claude-sonnet-4-5"
    )
    vision_fallback_models: str | list[str] = Field(
        default="gpt-4o,gpt-4-turbo,claude-sonnet-4-5"
    )

    @field_validator('text_fallback_models', 'vision_fallback_models', mode='before')
    @classmethod
    def parse_comma_separated(cls, v: Any) -> list[str]:
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="docmind.log")
    enable_detailed_logging: bool = Field(default=True)

    # Cache Configuration
    enable_cache: bool = Field(default=True)
    cache_dir: str = Field(default=".cache")
    cache_expiry_hours: int = Field(default=24)

    # Performance Configuration
    batch_size: int = Field(default=10)
    request_timeout: int = Field(default=30)
    max_retries: int = Field(default=3)

    def get_model_config(self, model_type: str) -> ModelConfig:
        """Get configuration for a specific model type."""
        model_map = {
            "text": (self.text_extraction_model, self.text_extraction_provider),
            "vision": (self.vision_model, self.vision_provider),
            "advanced": (self.advanced_model, self.advanced_provider),
            "validator": (self.validator_model, self.validator_provider),
        }

        if model_type not in model_map:
            raise ValueError(f"Unknown model type: {model_type}")

        name, provider = model_map[model_type]
        return ModelConfig(name=name, provider=provider)


class SingletonMeta(type):
    """Thread-safe singleton metaclass."""
    _instances: ClassVar = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigManager(metaclass=SingletonMeta):
    """Singleton configuration manager."""

    def __init__(self):
        self._config: Config | None = None

    def get_config(self) -> Config:
        """Get global configuration instance."""
        if self._config is None:
            self._config = Config()
        return self._config

    def reload_config(self) -> Config:
        """Reload configuration from environment."""
        self._config = Config()
        return self._config


# Global configuration manager instance
_manager = ConfigManager()


def get_config() -> Config:
    """Get global configuration instance."""
    return _manager.get_config()


def reload_config() -> Config:
    """Reload configuration from environment."""
    return _manager.reload_config()
