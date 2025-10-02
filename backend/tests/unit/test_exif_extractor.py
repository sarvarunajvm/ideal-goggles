"""Comprehensive unit tests for EXIF extractor worker module."""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.models.exif import EXIFData
from src.models.photo import Photo
from src.workers.exif_extractor import (
    AdvancedEXIFExtractor,
    EXIFExtractionPipeline,
    EXIFExtractor,
    EXIFValidator,
)


@pytest.fixture
def mock_photo():
    """Create a mock photo for testing."""
    photo = Mock(spec=Photo)
    photo.id = 1
    photo.path = "/path/to/photo.jpg"
    return photo


@pytest.fixture
def sample_exif_dict():
    """Create sample EXIF dictionary."""
    return {
        "DateTime": "2024:01:15 10:30:45",
        "Make": "Canon",
        "Model": "EOS R5",
        "LensModel": "RF 24-105mm F4 L IS USM",
        "ISOSpeedRatings": 400,
        "FNumber": 5.6,
        "ExposureTime": 0.004,
        "FocalLength": 50.0,
        "Orientation": 1,
        "GPSInfo": {
            "GPSLatitudeRef": "N",
            "GPSLatitude": [37, 46, 30],
            "GPSLongitudeRef": "W",
            "GPSLongitude": [122, 25, 9],
        },
    }


@pytest.fixture
def sample_exif_data():
    """Create sample EXIFData instance."""
    return EXIFData(
        file_id=1,
        shot_dt="2024-01-15T10:30:45",
        camera_make="Canon",
        camera_model="EOS R5",
        lens="RF 24-105mm F4 L IS USM",
        iso=400,
        aperture=5.6,
        shutter_speed="1/250",
        focal_length=50.0,
        gps_lat=37.775,
        gps_lon=-122.4192,
        orientation=1,
    )


class TestEXIFExtractor:
    """Test EXIFExtractor class."""

    def test_extractor_initialization_default(self):
        """Test EXIF extractor initialization with defaults."""
        extractor = EXIFExtractor()
        assert extractor.max_workers == 4
        assert extractor.executor is not None
        assert extractor.stats["processed"] == 0
        assert extractor.stats["successful"] == 0
        assert extractor.stats["failed"] == 0

    def test_extractor_initialization_custom(self):
        """Test EXIF extractor initialization with custom values."""
        extractor = EXIFExtractor(max_workers=8)
        assert extractor.max_workers == 8

    @pytest.mark.asyncio
    async def test_extract_exif_success(self, mock_photo, sample_exif_dict):
        """Test successful EXIF extraction."""
        extractor = EXIFExtractor()

        with patch.object(extractor, "_extract_exif_sync") as mock_extract:
            mock_extract.return_value = sample_exif_dict

            result = await extractor.extract_exif(mock_photo)

            assert result is not None
            assert result.file_id == mock_photo.id
            assert result.camera_make == "Canon"
            assert extractor.stats["successful"] == 1
            assert extractor.stats["processed"] == 1

    @pytest.mark.asyncio
    async def test_extract_exif_no_data(self, mock_photo):
        """Test EXIF extraction with no data found."""
        extractor = EXIFExtractor()

        with patch.object(extractor, "_extract_exif_sync", return_value=None):
            result = await extractor.extract_exif(mock_photo)

            assert result is None
            assert extractor.stats["processed"] == 1

    @pytest.mark.asyncio
    async def test_extract_exif_exception(self, mock_photo):
        """Test EXIF extraction handles exceptions."""
        extractor = EXIFExtractor()

        with patch.object(
            extractor, "_extract_exif_sync", side_effect=Exception("EXIF error")
        ):
            result = await extractor.extract_exif(mock_photo)

            assert result is None
            assert extractor.stats["failed"] == 1
            assert extractor.stats["processed"] == 1

    @pytest.mark.asyncio
    async def test_extract_exif_updates_time_stats(self, mock_photo, sample_exif_dict):
        """Test EXIF extraction updates timing statistics."""
        extractor = EXIFExtractor()

        with patch.object(extractor, "_extract_exif_sync") as mock_extract:
            mock_extract.return_value = sample_exif_dict

            await extractor.extract_exif(mock_photo)

            assert extractor.stats["total_time"] > 0

    def test_extract_exif_sync_success(self, sample_exif_dict):
        """Test synchronous EXIF extraction."""
        extractor = EXIFExtractor()

        with patch("PIL.Image.open") as mock_open:
            mock_img = Mock()
            mock_img.__enter__ = Mock(return_value=mock_img)
            mock_img.__exit__ = Mock(return_value=False)
            mock_img._getexif.return_value = {
                306: "2024:01:15 10:30:45",  # DateTime tag
                271: "Canon",  # Make tag
                272: "EOS R5",  # Model tag
            }
            mock_open.return_value = mock_img

            result = extractor._extract_exif_sync("/path/to/photo.jpg")

            assert result is not None
            assert "DateTime" in result
            assert result["DateTime"] == "2024:01:15 10:30:45"

    def test_extract_exif_sync_no_exif(self):
        """Test synchronous extraction with no EXIF data."""
        extractor = EXIFExtractor()

        with patch("PIL.Image.open") as mock_open:
            mock_img = Mock()
            mock_img.__enter__ = Mock(return_value=mock_img)
            mock_img.__exit__ = Mock(return_value=False)
            mock_img._getexif.return_value = None
            mock_open.return_value = mock_img

            result = extractor._extract_exif_sync("/path/to/photo.jpg")

            assert result is None

    def test_extract_exif_sync_with_gps(self):
        """Test synchronous extraction with GPS data."""
        extractor = EXIFExtractor()

        with patch("PIL.Image.open") as mock_open:
            mock_img = Mock()
            mock_img.__enter__ = Mock(return_value=mock_img)
            mock_img.__exit__ = Mock(return_value=False)
            mock_img._getexif.return_value = {
                34853: {  # GPSInfo tag
                    1: "N",  # GPSLatitudeRef
                    2: [37, 46, 30],  # GPSLatitude
                    3: "W",  # GPSLongitudeRef
                    4: [122, 25, 9],  # GPSLongitude
                }
            }
            mock_open.return_value = mock_img

            result = extractor._extract_exif_sync("/path/to/photo.jpg")

            assert result is not None
            assert "GPSInfo" in result

    def test_extract_exif_sync_exception(self):
        """Test synchronous extraction handles exceptions."""
        extractor = EXIFExtractor()

        with patch("PIL.Image.open", side_effect=Exception("Image error")):
            result = extractor._extract_exif_sync("/path/to/photo.jpg")

            assert result is None

    @pytest.mark.asyncio
    async def test_extract_batch_empty(self):
        """Test batch extraction with empty list."""
        extractor = EXIFExtractor()
        results = await extractor.extract_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_extract_batch_success(self, mock_photo, sample_exif_dict):
        """Test successful batch extraction."""
        extractor = EXIFExtractor()

        photos = [mock_photo, mock_photo, mock_photo]

        with patch.object(extractor, "extract_exif") as mock_extract:
            mock_result = EXIFData(
                file_id=1, camera_make="Canon", camera_model="EOS R5"
            )
            mock_extract.return_value = mock_result

            results = await extractor.extract_batch(photos)

            assert len(results) == 3
            assert all(r.camera_make == "Canon" for r in results)

    @pytest.mark.asyncio
    async def test_extract_batch_partial_success(self, mock_photo):
        """Test batch extraction with partial success."""
        extractor = EXIFExtractor()

        photos = [mock_photo, mock_photo, mock_photo]

        with patch.object(extractor, "extract_exif") as mock_extract:
            # First succeeds, second fails, third succeeds
            mock_result = EXIFData(file_id=1, camera_make="Canon")
            mock_extract.side_effect = [mock_result, None, mock_result]

            results = await extractor.extract_batch(photos)

            assert len(results) == 3
            assert results[0] is not None
            assert results[1] is None
            assert results[2] is not None

    def test_get_statistics(self):
        """Test getting extraction statistics."""
        extractor = EXIFExtractor()

        # Add some stats manually
        extractor.stats["processed"] = 100
        extractor.stats["successful"] = 80
        extractor.stats["failed"] = 20
        extractor.stats["total_time"] = 10.0

        stats = extractor.get_statistics()

        assert stats["processed"] == 100
        assert stats["successful"] == 80
        assert stats["failed"] == 20
        assert stats["success_rate"] == 0.8
        assert stats["average_processing_time"] == 0.1

    def test_get_statistics_empty(self):
        """Test statistics with no data."""
        extractor = EXIFExtractor()

        stats = extractor.get_statistics()

        assert stats["processed"] == 0
        assert stats["success_rate"] == 0
        assert stats["average_processing_time"] == 0

    def test_reset_statistics(self):
        """Test resetting statistics."""
        extractor = EXIFExtractor()

        extractor.stats["processed"] = 100
        extractor.stats["successful"] = 80

        extractor.reset_statistics()

        assert extractor.stats["processed"] == 0
        assert extractor.stats["successful"] == 0

    def test_shutdown(self):
        """Test extractor shutdown."""
        extractor = EXIFExtractor()

        with patch.object(extractor.executor, "shutdown") as mock_shutdown:
            extractor.shutdown()
            mock_shutdown.assert_called_once_with(wait=True)


class TestAdvancedEXIFExtractor:
    """Test AdvancedEXIFExtractor class."""

    def test_advanced_extractor_initialization_with_exifread(self):
        """Test advanced extractor initialization with exifread."""
        extractor = AdvancedEXIFExtractor(use_exifread=True)
        assert extractor.use_exifread
        # exifread availability depends on environment

    def test_advanced_extractor_initialization_without_exifread(self):
        """Test advanced extractor initialization without exifread."""
        extractor = AdvancedEXIFExtractor(use_exifread=False)
        assert not extractor.use_exifread
        assert extractor.exifread is None

    def test_extract_exif_sync_pil_success(self, sample_exif_dict):
        """Test extraction uses PIL successfully."""
        extractor = AdvancedEXIFExtractor(use_exifread=False)

        with patch.object(EXIFExtractor, "_extract_exif_sync") as mock_pil:
            mock_pil.return_value = sample_exif_dict

            result = extractor._extract_exif_sync("/path/to/photo.jpg")

            assert result is not None
            assert result == sample_exif_dict

    def test_extract_exif_sync_fallback_to_exifread(self):
        """Test extraction falls back to exifread when PIL fails."""
        extractor = AdvancedEXIFExtractor(use_exifread=True)
        if extractor.exifread is None:
            # Skip test if exifread not available
            return

        # PIL returns minimal data
        with patch.object(
            EXIFExtractor, "_extract_exif_sync", return_value={"Make": "Canon"}
        ):
            with patch.object(
                extractor, "_extract_with_exifread"
            ) as mock_exifread:
                mock_exifread.return_value = {
                    "Make": "Canon",
                    "Model": "EOS R5",
                    "DateTime": "2024:01:15 10:30:45",
                }

                result = extractor._extract_exif_sync("/path/to/photo.jpg")

                # Should use exifread result
                mock_exifread.assert_called_once()

    def test_extract_with_exifread_success(self):
        """Test extraction using exifread library."""
        extractor = AdvancedEXIFExtractor(use_exifread=True)
        if extractor.exifread is None:
            # Skip test if exifread not available
            return

        # Mock exifread tags
        mock_tags = {
            "Image Make": Mock(__str__=lambda x: "Canon"),
            "Image Model": Mock(__str__=lambda x: "EOS R5"),
            "EXIF DateTimeOriginal": Mock(__str__=lambda x: "2024:01:15 10:30:45"),
            "GPS GPSLatitude": Mock(__str__=lambda x: "[37, 46, 30]"),
            "Image Thumbnail": Mock(__str__=lambda x: "thumbnail_data"),  # Should skip
        }

        extractor.exifread.process_file = Mock(return_value=mock_tags)

        with patch("builtins.open", create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = extractor._extract_with_exifread("/path/to/photo.jpg")

            assert result is not None
            assert "Make" in result
            assert result["Make"] == "Canon"
            assert "thumbnail" not in str(result).lower()

    def test_extract_with_exifread_no_tags(self):
        """Test extraction with no exifread tags."""
        extractor = AdvancedEXIFExtractor(use_exifread=True)
        if extractor.exifread is None:
            # Skip test if exifread not available
            return

        extractor.exifread.process_file = Mock(return_value=None)

        with patch("builtins.open", create=True):
            result = extractor._extract_with_exifread("/path/to/photo.jpg")

            assert result is None

    def test_extract_with_exifread_with_gps(self):
        """Test extraction with GPS data using exifread."""
        extractor = AdvancedEXIFExtractor(use_exifread=True)
        if extractor.exifread is None:
            # Skip test if exifread not available
            return

        mock_tags = {
            "GPS GPSLatitudeRef": Mock(__str__=lambda x: "N"),
            "GPS GPSLatitude": Mock(__str__=lambda x: "[37, 46, 30]"),
        }

        extractor.exifread.process_file = Mock(return_value=mock_tags)

        with patch("builtins.open", create=True):
            result = extractor._extract_with_exifread("/path/to/photo.jpg")

            assert result is not None
            assert "GPSInfo" in result

    def test_extract_with_exifread_exception(self):
        """Test extraction handles exifread exceptions."""
        extractor = AdvancedEXIFExtractor(use_exifread=True)
        if extractor.exifread is None:
            # Skip test if exifread not available
            return

        with patch("builtins.open", side_effect=Exception("File error")):
            result = extractor._extract_with_exifread("/path/to/photo.jpg")

            assert result is None


class TestEXIFValidator:
    """Test EXIFValidator class."""

    def test_validate_exif_data_valid(self, sample_exif_data):
        """Test validation of valid EXIF data."""
        result = EXIFValidator.validate_exif_data(sample_exif_data)

        assert result["is_valid"]
        assert result["has_camera_info"]
        assert result["has_exposure_info"]
        assert result["has_location"]
        assert result["completeness_score"] > 0.8
        assert result["quality_score"] > 0.8

    def test_validate_exif_data_minimal(self):
        """Test validation of minimal EXIF data."""
        minimal_data = EXIFData(file_id=1, shot_dt="2024-01-15T10:30:45")

        result = EXIFValidator.validate_exif_data(minimal_data)

        assert result["is_valid"]
        assert result["has_camera_info"] is False
        assert result["has_exposure_info"] is False
        assert result["has_location"] is False
        assert result["completeness_score"] < 0.2
        assert result["quality_score"] == 0.3  # Only has date/time

    def test_validate_exif_data_no_datetime(self):
        """Test validation without datetime."""
        data = EXIFData(file_id=1, camera_make="Canon", camera_model="EOS R5")

        result = EXIFValidator.validate_exif_data(data)

        assert result["has_camera_info"]
        assert result["quality_score"] == 0.2  # Only camera info

    def test_validate_exif_data_with_location(self):
        """Test validation with GPS location."""
        data = EXIFData(file_id=1, gps_lat=37.775, gps_lon=-122.4192)

        result = EXIFValidator.validate_exif_data(data)

        assert result["has_location"]

    def test_validate_exif_data_completeness_score(self):
        """Test completeness score calculation."""
        # Data with all fields
        complete_data = EXIFData(
            file_id=1,
            shot_dt="2024-01-15T10:30:45",
            camera_make="Canon",
            camera_model="EOS R5",
            lens="RF 24-105mm",
            iso=400,
            aperture=5.6,
            shutter_speed="1/250",
            focal_length=50.0,
            gps_lat=37.775,
            gps_lon=-122.4192,
            orientation=1,
        )

        result = EXIFValidator.validate_exif_data(complete_data)

        # Should have high completeness (11/11 fields)
        assert result["completeness_score"] == 1.0

    def test_suggest_improvements_minimal_data(self):
        """Test improvement suggestions for minimal data."""
        minimal_data = EXIFData(file_id=1)

        suggestions = EXIFValidator.suggest_improvements(minimal_data)

        assert len(suggestions) > 0
        assert any("date/time" in s.lower() for s in suggestions)
        assert any("camera" in s.lower() for s in suggestions)

    def test_suggest_improvements_no_datetime(self):
        """Test suggestions when datetime is missing."""
        data = EXIFData(file_id=1, camera_make="Canon")

        suggestions = EXIFValidator.suggest_improvements(data)

        assert any("date/time" in s.lower() for s in suggestions)

    def test_suggest_improvements_no_camera_info(self):
        """Test suggestions when camera info is missing."""
        data = EXIFData(file_id=1, shot_dt="2024-01-15T10:30:45")

        suggestions = EXIFValidator.suggest_improvements(data)

        assert any("camera" in s.lower() for s in suggestions)

    def test_suggest_improvements_no_exposure(self):
        """Test suggestions when exposure info is missing."""
        data = EXIFData(file_id=1, camera_make="Canon")

        suggestions = EXIFValidator.suggest_improvements(data)

        assert any("exposure" in s.lower() for s in suggestions)

    def test_suggest_improvements_no_gps(self):
        """Test suggestions when GPS is missing."""
        data = EXIFData(file_id=1, camera_make="Canon", camera_model="EOS R5")

        suggestions = EXIFValidator.suggest_improvements(data)

        assert any("gps" in s.lower() or "location" in s.lower() for s in suggestions)

    def test_suggest_improvements_complete_data(self, sample_exif_data):
        """Test suggestions for complete data."""
        suggestions = EXIFValidator.suggest_improvements(sample_exif_data)

        # Should have minimal or no suggestions
        assert len(suggestions) <= 1


class TestEXIFExtractionPipeline:
    """Test EXIFExtractionPipeline class."""

    def test_pipeline_initialization_with_validation(self):
        """Test pipeline initialization with validation enabled."""
        pipeline = EXIFExtractionPipeline(max_workers=4, validate_results=True)
        assert isinstance(pipeline.extractor, AdvancedEXIFExtractor)
        assert pipeline.validator is not None
        assert pipeline.validate_results

    def test_pipeline_initialization_without_validation(self):
        """Test pipeline initialization with validation disabled."""
        pipeline = EXIFExtractionPipeline(max_workers=4, validate_results=False)
        assert pipeline.validator is None
        assert not pipeline.validate_results

    @pytest.mark.asyncio
    async def test_process_photos_empty(self):
        """Test processing empty photo list."""
        pipeline = EXIFExtractionPipeline()
        results = await pipeline.process_photos([])
        assert results == []

    @pytest.mark.asyncio
    async def test_process_photos_success(self, mock_photo, sample_exif_data):
        """Test successful photo processing."""
        pipeline = EXIFExtractionPipeline(validate_results=True)

        photos = [mock_photo, mock_photo]

        with patch.object(
            pipeline.extractor, "extract_batch"
        ) as mock_extract:
            mock_extract.return_value = [sample_exif_data, sample_exif_data]

            results = await pipeline.process_photos(photos)

            assert len(results) == 2
            assert all(r["extraction_successful"] for r in results)
            assert all(r["validation_result"] is not None for r in results)

    @pytest.mark.asyncio
    async def test_process_photos_partial_success(self, mock_photo, sample_exif_data):
        """Test processing with partial success."""
        pipeline = EXIFExtractionPipeline(validate_results=True)

        photos = [mock_photo, mock_photo, mock_photo]

        with patch.object(
            pipeline.extractor, "extract_batch"
        ) as mock_extract:
            mock_extract.return_value = [sample_exif_data, None, sample_exif_data]

            results = await pipeline.process_photos(photos)

            assert len(results) == 3
            assert results[0]["extraction_successful"]
            assert not results[1]["extraction_successful"]
            assert results[2]["extraction_successful"]

    @pytest.mark.asyncio
    async def test_process_photos_without_validation(self, mock_photo, sample_exif_data):
        """Test processing without validation."""
        pipeline = EXIFExtractionPipeline(validate_results=False)

        photos = [mock_photo]

        with patch.object(
            pipeline.extractor, "extract_batch"
        ) as mock_extract:
            mock_extract.return_value = [sample_exif_data]

            results = await pipeline.process_photos(photos)

            assert len(results) == 1
            assert results[0]["validation_result"] is None

    @pytest.mark.asyncio
    async def test_process_photos_updates_stats(self, mock_photo, sample_exif_data):
        """Test processing updates pipeline statistics."""
        pipeline = EXIFExtractionPipeline(validate_results=True)

        photos = [mock_photo, mock_photo]

        with patch.object(
            pipeline.extractor, "extract_batch"
        ) as mock_extract:
            mock_extract.return_value = [sample_exif_data, sample_exif_data]

            await pipeline.process_photos(photos)

            assert pipeline.pipeline_stats["total_processed"] == 2
            assert pipeline.pipeline_stats["extraction_successful"] == 2
            assert pipeline.pipeline_stats["validation_passed"] == 2

    @pytest.mark.asyncio
    async def test_process_photos_high_quality_tracking(
        self, mock_photo, sample_exif_data
    ):
        """Test tracking of high quality results."""
        pipeline = EXIFExtractionPipeline(validate_results=True)

        photos = [mock_photo]

        with patch.object(
            pipeline.extractor, "extract_batch"
        ) as mock_extract:
            mock_extract.return_value = [sample_exif_data]

            with patch.object(
                pipeline.validator, "validate_exif_data"
            ) as mock_validate:
                mock_validate.return_value = {
                    "is_valid": True,
                    "quality_score": 0.85,  # High quality
                }

                await pipeline.process_photos(photos)

                assert pipeline.pipeline_stats["high_quality_results"] == 1

    def test_get_pipeline_statistics(self):
        """Test getting pipeline statistics."""
        pipeline = EXIFExtractionPipeline()

        # Manually set some stats
        pipeline.pipeline_stats["total_processed"] = 100
        pipeline.pipeline_stats["extraction_successful"] = 80
        pipeline.pipeline_stats["validation_passed"] = 70
        pipeline.pipeline_stats["high_quality_results"] = 60

        stats = pipeline.get_pipeline_statistics()

        assert stats["total_processed"] == 100
        assert stats["extraction_success_rate"] == 0.8
        assert stats["validation_success_rate"] == 0.7
        assert stats["high_quality_rate"] == 0.6

    def test_get_pipeline_statistics_empty(self):
        """Test statistics with no data."""
        pipeline = EXIFExtractionPipeline()

        stats = pipeline.get_pipeline_statistics()

        assert stats["total_processed"] == 0

    def test_reset_statistics(self):
        """Test resetting pipeline statistics."""
        pipeline = EXIFExtractionPipeline()

        pipeline.pipeline_stats["total_processed"] = 100
        pipeline.extractor.stats["processed"] = 100

        pipeline.reset_statistics()

        assert pipeline.pipeline_stats["total_processed"] == 0
        assert pipeline.extractor.stats["processed"] == 0

    def test_shutdown(self):
        """Test pipeline shutdown."""
        pipeline = EXIFExtractionPipeline()

        with patch.object(pipeline.extractor, "shutdown") as mock_shutdown:
            pipeline.shutdown()
            mock_shutdown.assert_called_once()
