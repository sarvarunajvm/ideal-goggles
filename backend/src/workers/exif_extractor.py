"""EXIF extractor worker for photo metadata extraction."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

from ..models.exif import EXIFData
from ..models.photo import Photo

logger = logging.getLogger(__name__)


class EXIFExtractor:
    """Worker for extracting EXIF metadata from photos."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0,
        }

    async def extract_exif(self, photo: Photo) -> EXIFData | None:
        """Extract EXIF data from a photo file."""
        start_time = time.time()

        try:
            # Run EXIF extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            exif_dict = await loop.run_in_executor(
                self.executor,
                self._extract_exif_sync,
                photo.path
            )

            if exif_dict:
                exif_data = EXIFData.from_exif_dict(photo.id, exif_dict)
                self.stats["successful"] += 1
                return exif_data
            logger.debug(f"No EXIF data found in {photo.path}")
            return None

        except Exception as e:
            logger.warning(f"Failed to extract EXIF from {photo.path}: {e}")
            self.stats["failed"] += 1
            return None

        finally:
            processing_time = time.time() - start_time
            self.stats["processed"] += 1
            self.stats["total_time"] += processing_time

    def _extract_exif_sync(self, file_path: str) -> dict[str, Any] | None:
        """Synchronously extract EXIF data using PIL."""
        try:
            with Image.open(file_path) as img:
                # Get EXIF data
                exif_dict = img._getexif()

                if not exif_dict:
                    return None

                # Convert numeric tags to human-readable names
                decoded_exif = {}
                for tag_id, value in exif_dict.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    decoded_exif[tag_name] = value

                # Handle GPS data specially
                if "GPSInfo" in decoded_exif:
                    gps_data = decoded_exif["GPSInfo"]
                    decoded_gps = {}

                    for gps_tag_id, gps_value in gps_data.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        decoded_gps[gps_tag_name] = gps_value

                    decoded_exif["GPSInfo"] = decoded_gps

                return decoded_exif

        except Exception as e:
            logger.debug(f"PIL EXIF extraction failed for {file_path}: {e}")
            return None

    async def extract_batch(self, photos: list[Photo]) -> list[EXIFData | None]:
        """Extract EXIF data from multiple photos concurrently."""
        if not photos:
            return []

        logger.info(f"Extracting EXIF from {len(photos)} photos")

        # Create tasks for concurrent processing
        tasks = [self.extract_exif(photo) for photo in photos]

        # Process with progress logging
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Log progress periodically
            if (i + 1) % 100 == 0:
                logger.info(f"EXIF extraction progress: {i + 1}/{len(photos)}")

        logger.info(f"EXIF extraction completed: {len([r for r in results if r])} successful")

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get extraction statistics."""
        avg_time = (self.stats["total_time"] / self.stats["processed"]
                   if self.stats["processed"] > 0 else 0)

        return {
            "processed": self.stats["processed"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "success_rate": (self.stats["successful"] / self.stats["processed"]
                           if self.stats["processed"] > 0 else 0),
            "average_processing_time": avg_time,
            "total_processing_time": self.stats["total_time"],
        }

    def reset_statistics(self):
        """Reset extraction statistics."""
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0,
        }

    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)


class AdvancedEXIFExtractor(EXIFExtractor):
    """Advanced EXIF extractor with additional metadata sources."""

    def __init__(self, max_workers: int = 4, use_exifread: bool = True):
        super().__init__(max_workers)
        self.use_exifread = use_exifread

        # Try to import exifread for more comprehensive EXIF extraction
        self.exifread = None
        if use_exifread:
            try:
                import exifread
                self.exifread = exifread
                logger.info("Using exifread for enhanced EXIF extraction")
            except ImportError:
                logger.warning("exifread not available, falling back to PIL")

    def _extract_exif_sync(self, file_path: str) -> dict[str, Any] | None:
        """Enhanced EXIF extraction with multiple sources."""
        # Try PIL first
        pil_exif = super()._extract_exif_sync(file_path)

        # Try exifread if available and PIL didn't work well
        if self.exifread and (not pil_exif or len(pil_exif) < 10):
            exifread_data = self._extract_with_exifread(file_path)
            if exifread_data:
                # Merge or prefer exifread data
                return exifread_data

        return pil_exif

    def _extract_with_exifread(self, file_path: str) -> dict[str, Any] | None:
        """Extract EXIF using exifread library."""
        try:
            with open(file_path, "rb") as f:
                tags = self.exifread.process_file(f, details=False)

            if not tags:
                return None

            # Convert exifread tags to standard format
            decoded_exif = {}
            gps_data = {}

            for tag_name, tag_value in tags.items():
                # Skip thumbnail data
                if "thumbnail" in tag_name.lower():
                    continue

                # Handle GPS tags separately
                if tag_name.startswith("GPS"):
                    gps_key = tag_name.replace("GPS ", "")
                    gps_data[gps_key] = str(tag_value)
                else:
                    # Convert tag name to PIL-compatible format
                    clean_tag = tag_name.replace("EXIF ", "").replace("Image ", "")
                    decoded_exif[clean_tag] = str(tag_value)

            # Add GPS data if present
            if gps_data:
                decoded_exif["GPSInfo"] = gps_data

            return decoded_exif

        except Exception as e:
            logger.debug(f"exifread extraction failed for {file_path}: {e}")
            return None


class EXIFValidator:
    """Validator for EXIF data quality and completeness."""

    @staticmethod
    def validate_exif_data(exif_data: EXIFData) -> dict[str, Any]:
        """Validate EXIF data and return quality metrics."""
        validation_result = {
            "is_valid": exif_data.is_valid(),
            "errors": exif_data.validate(),
            "completeness_score": 0.0,
            "quality_score": 0.0,
            "has_camera_info": exif_data.has_camera_info(),
            "has_exposure_info": exif_data.has_exposure_info(),
            "has_location": exif_data.has_location(),
        }

        # Calculate completeness score (0-1)
        total_fields = 11  # Total possible EXIF fields
        filled_fields = sum([
            1 if exif_data.shot_dt else 0,
            1 if exif_data.camera_make else 0,
            1 if exif_data.camera_model else 0,
            1 if exif_data.lens else 0,
            1 if exif_data.iso else 0,
            1 if exif_data.aperture else 0,
            1 if exif_data.shutter_speed else 0,
            1 if exif_data.focal_length else 0,
            1 if exif_data.gps_lat else 0,
            1 if exif_data.gps_lon else 0,
            1 if exif_data.orientation else 0,
        ])

        validation_result["completeness_score"] = filled_fields / total_fields

        # Calculate quality score based on usefulness for photography
        quality_score = 0.0
        if exif_data.shot_dt:
            quality_score += 0.3  # Date/time is very important
        if exif_data.has_camera_info():
            quality_score += 0.2  # Camera info is useful
        if exif_data.has_exposure_info():
            quality_score += 0.3  # Exposure settings are valuable
        if exif_data.has_location():
            quality_score += 0.2  # GPS location is valuable

        validation_result["quality_score"] = quality_score

        return validation_result

    @staticmethod
    def suggest_improvements(exif_data: EXIFData) -> list[str]:
        """Suggest improvements for EXIF data quality."""
        suggestions = []

        if not exif_data.shot_dt:
            suggestions.append("Consider setting camera date/time")

        if not exif_data.has_camera_info():
            suggestions.append("Camera model information missing")

        if not exif_data.has_exposure_info():
            suggestions.append("Exposure settings not recorded")

        if not exif_data.has_location() and exif_data.camera_make:
            suggestions.append("Enable GPS for location tracking")

        return suggestions


class EXIFExtractionPipeline:
    """Pipeline for batch EXIF extraction with validation."""

    def __init__(self, max_workers: int = 4, validate_results: bool = True):
        self.extractor = AdvancedEXIFExtractor(max_workers)
        self.validator = EXIFValidator() if validate_results else None
        self.validate_results = validate_results

        self.pipeline_stats = {
            "total_processed": 0,
            "extraction_successful": 0,
            "validation_passed": 0,
            "high_quality_results": 0,
        }

    async def process_photos(self, photos: list[Photo]) -> list[dict[str, Any]]:
        """Process photos through the complete EXIF pipeline."""
        logger.info(f"Starting EXIF pipeline for {len(photos)} photos")

        results = []

        # Extract EXIF data
        exif_results = await self.extractor.extract_batch(photos)

        for photo, exif_data in zip(photos, exif_results, strict=False):
            result = {
                "photo_id": photo.id,
                "photo_path": photo.path,
                "exif_data": exif_data,
                "extraction_successful": exif_data is not None,
                "validation_result": None,
            }

            self.pipeline_stats["total_processed"] += 1

            if exif_data:
                self.pipeline_stats["extraction_successful"] += 1

                # Validate if requested
                if self.validate_results and self.validator:
                    validation_result = self.validator.validate_exif_data(exif_data)
                    result["validation_result"] = validation_result

                    if validation_result["is_valid"]:
                        self.pipeline_stats["validation_passed"] += 1

                    if validation_result["quality_score"] >= 0.7:
                        self.pipeline_stats["high_quality_results"] += 1

            results.append(result)

        logger.info(f"EXIF pipeline completed: {self.pipeline_stats['extraction_successful']}/{len(photos)} successful")

        return results

    def get_pipeline_statistics(self) -> dict[str, Any]:
        """Get pipeline processing statistics."""
        stats = self.pipeline_stats.copy()
        stats.update(self.extractor.get_statistics())

        if stats["total_processed"] > 0:
            stats["extraction_success_rate"] = (
                stats["extraction_successful"] / stats["total_processed"]
            )
            stats["validation_success_rate"] = (
                stats["validation_passed"] / stats["total_processed"]
            )
            stats["high_quality_rate"] = (
                stats["high_quality_results"] / stats["total_processed"]
            )

        return stats

    def reset_statistics(self):
        """Reset all pipeline statistics."""
        self.extractor.reset_statistics()
        self.pipeline_stats = {
            "total_processed": 0,
            "extraction_successful": 0,
            "validation_passed": 0,
            "high_quality_results": 0,
        }

    def shutdown(self):
        """Shutdown the pipeline."""
        self.extractor.shutdown()
