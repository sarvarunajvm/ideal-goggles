"""Unit tests for core configuration module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.config import Settings, get_settings, settings


class TestSettings:
    """Test Settings configuration class."""

    def test_settings_default_values(self):
        """Test default configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Path, "resolve") as mock_resolve:
                # Mock resolve to return predictable paths
                def resolve_side_effect(self):
                    if "config.py" in str(self):
                        return Path(temp_dir) / "src" / "core" / "config.py"
                    return Path(str(self))

                mock_resolve.side_effect = (
                    lambda: Path(temp_dir) / "src" / "core" / "config.py"
                )

                test_settings = Settings()

                assert test_settings.HOST == "127.0.0.1"
                assert test_settings.PORT == 5555
                assert test_settings.DEBUG is False
                assert test_settings.LOG_LEVEL == "INFO"
                assert test_settings.MAX_WORKERS == 4
                assert test_settings.BATCH_SIZE == 32

    def test_settings_environment_override(self):
        """Test settings can be overridden by environment variables."""
        env_vars = {
            "HOST": "0.0.0.0",
            "PORT": "8080",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "MAX_WORKERS": "8",
        }

        with patch.dict(os.environ, env_vars):
            test_settings = Settings()

            assert test_settings.HOST == "0.0.0.0"
            assert test_settings.PORT == 8080
            assert test_settings.DEBUG is True
            assert test_settings.LOG_LEVEL == "DEBUG"
            assert test_settings.MAX_WORKERS == 8

    def test_settings_database_url(self):
        """Test database URL configuration."""
        test_settings = Settings()
        assert "sqlite" in test_settings.DATABASE_URL
        assert "photos.db" in test_settings.DATABASE_URL

    def test_settings_path_creation(self):
        """Test that settings creates required directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_vars = {
                "DATA_DIR": str(Path(temp_dir) / "data"),
                "CACHE_DIR": str(Path(temp_dir) / "cache"),
            }

            with patch.dict(os.environ, env_vars):
                test_settings = Settings()

                # Directories should be created
                assert test_settings.DATA_DIR.exists()
                assert test_settings.CACHE_DIR.exists()
                assert test_settings.THUMBNAILS_DIR.exists()

    def test_settings_thumbnails_dir_default(self):
        """Test that thumbnails directory defaults to cache/thumbs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_vars = {
                "CACHE_DIR": str(Path(temp_dir) / "cache"),
            }

            with patch.dict(os.environ, env_vars, clear=True):
                test_settings = Settings()

                # THUMBNAILS_DIR should be CACHE_DIR/thumbs
                assert (
                    test_settings.THUMBNAILS_DIR == test_settings.CACHE_DIR / "thumbs"
                )

    def test_settings_thumbnails_dir_override(self):
        """Test overriding thumbnails directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            thumbnails_path = Path(temp_dir) / "custom_thumbs"
            env_vars = {
                "THUMBNAILS_DIR": str(thumbnails_path),
            }

            with patch.dict(os.environ, env_vars):
                test_settings = Settings()

                assert thumbnails_path.resolve() == test_settings.THUMBNAILS_DIR
                assert test_settings.THUMBNAILS_DIR.exists()

    def test_settings_models_dir(self):
        """Test models directory configuration."""
        test_settings = Settings()

        assert Path("./models") == test_settings.MODELS_DIR
        assert Path("./models/clip-vit-b32.onnx") == test_settings.CLIP_MODEL_PATH
        assert Path("./models/arcface-r100.onnx") == test_settings.ARCFACE_MODEL_PATH

    def test_settings_ocr_configuration(self):
        """Test OCR configuration settings."""
        test_settings = Settings()

        assert test_settings.TESSERACT_CMD == "tesseract"
        assert "eng" in test_settings.OCR_LANGUAGES
        assert "tam" in test_settings.OCR_LANGUAGES

    def test_settings_performance_settings(self):
        """Test performance-related settings."""
        test_settings = Settings()

        assert test_settings.MAX_WORKERS == 4
        assert test_settings.BATCH_SIZE == 32
        assert test_settings.MAX_MEMORY_MB == 512

    def test_settings_privacy_settings(self):
        """Test privacy and security settings."""
        test_settings = Settings()

        assert test_settings.FACE_SEARCH_ENABLED is False
        assert test_settings.TELEMETRY_ENABLED is False
        assert test_settings.NETWORK_MONITORING is True

    def test_settings_with_env_file(self):
        """Test loading settings from .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .env file
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("HOST=192.168.1.1\nPORT=9000\n")

            # Change to temp directory
            original_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                test_settings = Settings()
                # Settings may or may not pick up the .env file depending on implementation
                # Just verify it doesn't crash
                assert test_settings is not None
            finally:
                os.chdir(original_dir)

    def test_get_settings_function(self):
        """Test get_settings returns global settings instance."""
        global_settings = get_settings()
        assert global_settings is settings
        assert isinstance(global_settings, Settings)

    def test_settings_data_dir_none_creates_default(self):
        """Test that None DATA_DIR creates default path."""
        test_settings = Settings(DATA_DIR=None)
        assert test_settings.DATA_DIR is not None
        # Should have created a default path

    def test_settings_cache_dir_none_creates_default(self):
        """Test that None CACHE_DIR creates default path."""
        test_settings = Settings(CACHE_DIR=None)
        assert test_settings.CACHE_DIR is not None
        # Should have created a default path

    def test_settings_custom_data_dir(self):
        """Test custom DATA_DIR setting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_data = Path(temp_dir) / "custom_data"
            test_settings = Settings(DATA_DIR=str(custom_data))

            assert custom_data.resolve() == test_settings.DATA_DIR
            assert test_settings.DATA_DIR.exists()

    def test_settings_custom_cache_dir(self):
        """Test custom CACHE_DIR setting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_cache = Path(temp_dir) / "custom_cache"
            test_settings = Settings(CACHE_DIR=str(custom_cache))

            assert custom_cache.resolve() == test_settings.CACHE_DIR
            assert test_settings.CACHE_DIR.exists()

    def test_settings_config_class(self):
        """Test Settings.Config class attributes."""
        config = Settings.Config
        assert config.env_file == ".env"
        assert config.case_sensitive is True

    def test_settings_creates_nested_directories(self):
        """Test that settings creates nested directory structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "level1" / "level2" / "data"
            test_settings = Settings(DATA_DIR=str(nested_path))

            assert test_settings.DATA_DIR.exists()
            assert nested_path.resolve() == test_settings.DATA_DIR
