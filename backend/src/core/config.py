"""Application configuration settings."""

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=55555, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Database configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/photos.db", env="DATABASE_URL"
    )

    # Storage paths
    DATA_DIR: Path = Field(default=Path("./data"), env="DATA_DIR")
    CACHE_DIR: Path = Field(default=Path("./cache"), env="CACHE_DIR")
    # Compute thumbnails dir relative to CACHE_DIR unless explicitly overridden.
    THUMBNAILS_DIR: Path | None = Field(default=None, env="THUMBNAILS_DIR")

    # ML model paths (bundled with application)
    MODELS_DIR: Path = Field(default=Path("./models"), env="MODELS_DIR")
    CLIP_MODEL_PATH: Path = Field(
        default=Path("./models/clip-vit-b32.onnx"), env="CLIP_MODEL_PATH"
    )
    ARCFACE_MODEL_PATH: Path = Field(
        default=Path("./models/arcface-r100.onnx"), env="ARCFACE_MODEL_PATH"
    )

    # OCR configuration
    TESSERACT_CMD: str = Field(default="tesseract", env="TESSERACT_CMD")
    OCR_LANGUAGES: list[str] = Field(default=["eng", "tam"], env="OCR_LANGUAGES")

    # Performance settings
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    BATCH_SIZE: int = Field(default=32, env="BATCH_SIZE")
    MAX_MEMORY_MB: int = Field(default=512, env="MAX_MEMORY_MB")

    # Privacy and security
    FACE_SEARCH_ENABLED: bool = Field(default=False, env="FACE_SEARCH_ENABLED")
    TELEMETRY_ENABLED: bool = Field(default=False, env="TELEMETRY_ENABLED")
    NETWORK_MONITORING: bool = Field(default=True, env="NETWORK_MONITORING")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and create required directories."""
        super().__init__(**kwargs)
        # Derive thumbnails directory if not set
        if self.THUMBNAILS_DIR is None:
            self.THUMBNAILS_DIR = self.CACHE_DIR / "thumbs"
        self._create_directories()

    def _create_directories(self) -> None:
        """Create required application directories."""
        # Create data/cache directories. Do not attempt to create MODELS_DIR
        # because packaged apps bundle models in a read-only location.
        directories = [
            self.DATA_DIR,
            self.CACHE_DIR,
            self.THUMBNAILS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
