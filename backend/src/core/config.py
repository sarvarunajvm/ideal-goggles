"""Application configuration settings."""

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=5555)
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # Database configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/photos.db"
    )

    # Storage paths - use absolute paths
    DATA_DIR: Path | None = Field(default=None)
    CACHE_DIR: Path | None = Field(default=None)
    # Compute thumbnails dir relative to CACHE_DIR unless explicitly overridden.
    THUMBNAILS_DIR: Path | None = Field(default=None)

    # ML model paths (bundled with application)
    MODELS_DIR: Path = Field(default=Path("./models"))
    CLIP_MODEL_PATH: Path = Field(
        default=Path("./models/clip-vit-b32.onnx")
    )
    ARCFACE_MODEL_PATH: Path = Field(
        default=Path("./models/arcface-r100.onnx")
    )

    # Performance settings
    MAX_WORKERS: int = Field(default=4)
    BATCH_SIZE: int = Field(default=32)
    MAX_MEMORY_MB: int = Field(default=512)

    # Privacy and security
    FACE_SEARCH_ENABLED: bool = Field(default=False)
    TELEMETRY_ENABLED: bool = Field(default=False)
    NETWORK_MONITORING: bool = Field(default=True)

    # Timeout and retry configuration (seconds unless specified)
    DB_CONNECTION_TIMEOUT: float = Field(default=30.0)
    HTTP_REQUEST_TIMEOUT: float = Field(default=5.0)
    ML_INSTALL_TIMEOUT: float = Field(default=600.0)
    ML_VERIFY_TIMEOUT: float = Field(default=120.0)
    WORKER_SHUTDOWN_TIMEOUT: float = Field(default=30.0)
    THREAD_JOIN_TIMEOUT: float = Field(default=5.0)
    QUEUE_GET_TIMEOUT: float = Field(default=0.1)

    # Performance monitoring
    SLOW_REQUEST_THRESHOLD_MS: int = Field(
        default=1000
    )

    # CORS / security
    # Allow "null" origin (file://) only when explicitly enabled (Electron sets this).
    ALLOW_NULL_ORIGIN: bool = Field(default=False)
    # Comma separated list of extra allowed origins (besides the built-ins below)
    EXTRA_ALLOWED_ORIGINS: str | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and create required directories."""
        super().__init__(**kwargs)

        # Get backend directory for relative paths
        backend_dir = Path(__file__).resolve().parent.parent.parent

        # Set default paths if not provided
        if self.DATA_DIR is None:
            # Prefer Electron-provided app userData in packaged app (env overrides)
            # Fallback to backend-local data directory in dev/test.
            # Electron main sets DATA_DIR env when spawning backend.
            self.DATA_DIR = backend_dir / "data"
        else:
            self.DATA_DIR = Path(self.DATA_DIR).resolve()

        if self.CACHE_DIR is None:
            self.CACHE_DIR = backend_dir / "cache"
        else:
            self.CACHE_DIR = Path(self.CACHE_DIR).resolve()

        # Derive thumbnails directory if not set
        if self.THUMBNAILS_DIR is None:
            self.THUMBNAILS_DIR = self.CACHE_DIR / "thumbs"
        else:
            self.THUMBNAILS_DIR = Path(self.THUMBNAILS_DIR).resolve()

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


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
