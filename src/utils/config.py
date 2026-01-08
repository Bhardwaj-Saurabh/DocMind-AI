"""
Configuration management for DocMind-AI.
"""

import os
from typing import Optional, Dict, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    provider: str  # "openai" or "anthropic"
    cost_per_1k_tokens: float = 0.0


class Config(BaseModel):
    """Application configuration."""

    # API Keys
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)

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
    text_fallback_models: List[str] = Field(
        default_factory=lambda: ["gpt-4o-mini", "gpt-4o", "claude-sonnet-4-5"]
    )
    vision_fallback_models: List[str] = Field(default_factory=lambda: ["gpt-4o", "gpt-4-turbo", "claude-sonnet-4-5"])

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

    class Config:
        env_prefix = ""

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        return cls(
            # API Keys
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            # Models
            text_extraction_model=os.getenv("TEXT_EXTRACTION_MODEL", "gpt-4o-mini"),
            text_extraction_provider=os.getenv("TEXT_EXTRACTION_PROVIDER", "openai"),
            vision_model=os.getenv("VISION_MODEL", "gpt-4o"),
            vision_provider=os.getenv("VISION_PROVIDER", "openai"),
            advanced_model=os.getenv("ADVANCED_MODEL", "claude-sonnet-4-5"),
            advanced_provider=os.getenv("ADVANCED_PROVIDER", "anthropic"),
            validator_model=os.getenv("VALIDATOR_MODEL", "gpt-4.1"),
            validator_provider=os.getenv("VALIDATOR_PROVIDER", "openai"),
            # Routing
            enable_adaptive_routing=os.getenv("ENABLE_ADAPTIVE_ROUTING", "true").lower() == "true",
            auto_model_selection=os.getenv("AUTO_MODEL_SELECTION", "true").lower() == "true",
            # Cost
            max_cost_per_document=float(os.getenv("MAX_COST_PER_DOCUMENT", "1.0")),
            max_cost_per_page=float(os.getenv("MAX_COST_PER_PAGE", "0.1")),
            enable_cost_tracking=os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true",
            cost_alert_threshold=float(os.getenv("COST_ALERT_THRESHOLD", "0.5")),
            # Processing
            max_parallel_pages=int(os.getenv("MAX_PARALLEL_PAGES", "5")),
            enable_vision_fallback=os.getenv("ENABLE_VISION_FALLBACK", "true").lower() == "true",
            enable_quality_validation=os.getenv("ENABLE_QUALITY_VALIDATION", "true").lower() == "true",
            # Logging
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "docmind.log"),
            enable_detailed_logging=os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true",
            # Cache
            enable_cache=os.getenv("ENABLE_CACHE", "true").lower() == "true",
            cache_dir=os.getenv("CACHE_DIR", ".cache"),
            cache_expiry_hours=int(os.getenv("CACHE_EXPIRY_HOURS", "24")),
            # Performance
            batch_size=int(os.getenv("BATCH_SIZE", "10")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )

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


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config.from_env()
    return _config
