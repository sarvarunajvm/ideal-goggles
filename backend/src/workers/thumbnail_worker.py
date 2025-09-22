"""Thumbnail generator worker for creating preview images."""

import asyncio
import logging
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image

from ..models.photo import Photo
from ..models.thumbnail import Thumbnail, ThumbnailCache

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Worker for generating thumbnail images."""

    def __init__(self, cache_root: str, max_workers: int = 4,
                 max_size: int = 512, img_format: str = "webp", quality: int = 85):
        self.cache_root = Path(cache_root)
        self.max_workers = max_workers
        self.max_size = max_size
        self.format = img_format.lower()
        self.quality = quality
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Ensure cache directory exists
        self.cache_root.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "generated": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0.0,
            "cache_hits": 0,
        }

        # Validate PIL availability
        self._validate_pil()

    def _validate_pil(self):
        """Validate PIL installation and format support."""
        try:
            from PIL import Image

            # Check WebP support if using WebP format
            if self.format == "webp":
                test_img = Image.new("RGB", (1, 1))
                with tempfile.NamedTemporaryFile(suffix=".webp") as f:
                    test_img.save(f.name, "WEBP")
                logger.info("WebP support confirmed")

            logger.info(f"PIL available for thumbnail generation (format: {self.format})")

        except ImportError:
            msg = "PIL not available for thumbnail generation"
            raise RuntimeError(msg)
        except Exception as e:
            if self.format == "webp":
                logger.warning(f"WebP support issue: {e}, falling back to JPEG")
                self.format = "jpeg"
            else:
                msg = f"PIL format support issue: {e}"
                raise RuntimeError(msg)

    async def generate_thumbnail(self, photo: Photo, force_regenerate: bool = False) -> Thumbnail | None:
        """Generate thumbnail for a photo."""
        start_time = time.time()

        try:
            # Check if thumbnail already exists and is up-to-date
            existing_thumbnail = await self._check_existing_thumbnail(photo)
            if existing_thumbnail and not force_regenerate:
                if not existing_thumbnail.needs_regeneration(photo.modified_ts, str(self.cache_root)):
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Using cached thumbnail for {photo.path}")
                    return existing_thumbnail

            # Generate new thumbnail
            loop = asyncio.get_event_loop()
            thumbnail = await loop.run_in_executor(
                self.executor,
                self._generate_thumbnail_sync,
                photo
            )

            processing_time = time.time() - start_time

            if thumbnail:
                self.stats["generated"] += 1
                self.stats["total_time"] += processing_time
                logger.debug(f"Generated thumbnail for {photo.path} ({processing_time:.2f}s)")
                return thumbnail
            self.stats["failed"] += 1
            return None

        except Exception as e:
            logger.warning(f"Thumbnail generation failed for {photo.path}: {e}")
            self.stats["failed"] += 1
            return None

    def _generate_thumbnail_sync(self, photo: Photo) -> Thumbnail | None:
        """Synchronously generate thumbnail using PIL."""
        try:
            from PIL import Image, ImageOps

            # Load original image
            with Image.open(photo.path) as img:
                # Get original dimensions
                original_width, original_height = img.size

                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA"):
                    # Create white background for transparency
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Auto-orient image based on EXIF
                img = ImageOps.exif_transpose(img)

                # Calculate thumbnail dimensions
                thumb_width, thumb_height = self._calculate_thumbnail_size(
                    original_width, original_height, self.max_size
                )

                # Create thumbnail
                img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)

                # Create thumbnail object
                thumbnail = Thumbnail.create_for_photo(
                    photo.id, thumb_width, thumb_height, self.max_size, self.format
                )

                # Ensure directory exists
                thumb_abs_path = thumbnail.get_absolute_path(str(self.cache_root))
                Path(thumb_abs_path).parent.mkdir(parents=True, exist_ok=True)

                # Save thumbnail
                save_kwargs = self._get_save_kwargs()
                img.save(thumb_abs_path, self.format.upper(), **save_kwargs)

                return thumbnail

        except Exception as e:
            logger.debug(f"PIL thumbnail generation failed for {photo.path}: {e}")
            return None

    def _calculate_thumbnail_size(self, width: int, height: int, max_size: int) -> tuple[int, int]:
        """Calculate thumbnail dimensions preserving aspect ratio."""
        if width <= 0 or height <= 0:
            return max_size, max_size

        # Calculate aspect ratio
        aspect_ratio = width / height

        if width > height:
            # Landscape
            thumb_width = min(max_size, width)
            thumb_height = int(thumb_width / aspect_ratio)
        else:
            # Portrait or square
            thumb_height = min(max_size, height)
            thumb_width = int(thumb_height * aspect_ratio)

        # Ensure minimum size
        thumb_width = max(1, thumb_width)
        thumb_height = max(1, thumb_height)

        return thumb_width, thumb_height

    def _get_save_kwargs(self) -> dict[str, Any]:
        """Get save parameters for different formats."""
        if self.format == "webp":
            return {
                "quality": self.quality,
                "method": 6,  # High quality method
                "optimize": True,
            }
        if self.format == "jpeg":
            return {
                "quality": self.quality,
                "optimize": True,
                "progressive": True,
            }
        if self.format == "png":
            return {
                "optimize": True,
            }
        return {}

    async def _check_existing_thumbnail(self, photo: Photo) -> Thumbnail | None:
        """Check if thumbnail already exists."""
        # This would typically query the database
        # For now, just check if file exists in expected location
        thumbnail = Thumbnail.create_for_photo(
            photo.id, 0, 0, self.max_size, self.format
        )

        if thumbnail.file_exists(str(self.cache_root)):
            # Would load actual dimensions from database
            return thumbnail

        return None

    async def generate_batch(self, photos: list[Photo],
                           force_regenerate: bool = False) -> list[Thumbnail | None]:
        """Generate thumbnails for multiple photos."""
        if not photos:
            return []

        logger.info(f"Generating thumbnails for {len(photos)} photos")

        # Create tasks for concurrent processing
        tasks = [self.generate_thumbnail(photo, force_regenerate) for photo in photos]

        # Process with progress logging
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Log progress periodically
            if (i + 1) % 100 == 0:
                logger.info(f"Thumbnail generation progress: {i + 1}/{len(photos)}")

        successful_count = len([r for r in results if r])
        logger.info(f"Thumbnail generation completed: {successful_count}/{len(photos)} successful")

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get thumbnail generation statistics."""
        total_processed = self.stats["generated"] + self.stats["failed"]
        avg_time = (self.stats["total_time"] / self.stats["generated"]
                   if self.stats["generated"] > 0 else 0)

        return {
            "generated": self.stats["generated"],
            "failed": self.stats["failed"],
            "skipped": self.stats["skipped"],
            "cache_hits": self.stats["cache_hits"],
            "total_processed": total_processed,
            "success_rate": (self.stats["generated"] / total_processed
                           if total_processed > 0 else 0),
            "average_generation_time": avg_time,
            "total_generation_time": self.stats["total_time"],
            "cache_root": str(self.cache_root),
            "format": self.format,
            "max_size": self.max_size,
            "quality": self.quality,
        }

    def reset_statistics(self):
        """Reset generation statistics."""
        self.stats = {
            "generated": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0.0,
            "cache_hits": 0,
        }

    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)


class SmartThumbnailGenerator(ThumbnailGenerator):
    """Smart thumbnail generator with adaptive quality and multiple sizes."""

    def __init__(self, cache_root: str, max_workers: int = 4,
                 sizes: list[int] | None = None, adaptive_quality: bool = True):
        # Default sizes for different use cases
        self.sizes = sizes or [128, 256, 512]
        self.adaptive_quality = adaptive_quality

        # Use largest size as max_size for base class
        super().__init__(cache_root, max_workers, max(self.sizes))

    async def generate_multi_size_thumbnails(self, photo: Photo) -> list[Thumbnail | None]:
        """Generate thumbnails in multiple sizes."""
        thumbnails = []

        for size in self.sizes:
            # Temporarily override max_size
            original_max_size = self.max_size
            self.max_size = size

            try:
                thumbnail = await self.generate_thumbnail(photo)
                thumbnails.append(thumbnail)
            finally:
                self.max_size = original_max_size

        return thumbnails

    def _generate_thumbnail_sync(self, photo: Photo) -> Thumbnail | None:
        """Enhanced thumbnail generation with adaptive quality."""
        try:
            from PIL import Image, ImageOps

            with Image.open(photo.path) as img:
                original_width, original_height = img.size

                # Determine quality based on image characteristics
                quality = self._calculate_adaptive_quality(img, photo)

                # Process image
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Auto-orient
                img = ImageOps.exif_transpose(img)

                # Apply image enhancements if needed
                img = self._enhance_image_for_thumbnail(img)

                # Calculate dimensions
                thumb_width, thumb_height = self._calculate_thumbnail_size(
                    original_width, original_height, self.max_size
                )

                # Create thumbnail with high-quality resampling
                img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)

                # Create thumbnail object
                thumbnail = Thumbnail.create_for_photo(
                    photo.id, thumb_width, thumb_height, self.max_size, self.format
                )

                # Save with adaptive quality
                thumb_abs_path = thumbnail.get_absolute_path(str(self.cache_root))
                Path(thumb_abs_path).parent.mkdir(parents=True, exist_ok=True)

                save_kwargs = self._get_adaptive_save_kwargs(quality)
                img.save(thumb_abs_path, self.format.upper(), **save_kwargs)

                return thumbnail

        except Exception as e:
            logger.debug(f"Smart thumbnail generation failed for {photo.path}: {e}")
            return None

    def _calculate_adaptive_quality(self, img: Image.Image, photo: Photo) -> int:
        """Calculate adaptive quality based on image characteristics."""
        if not self.adaptive_quality:
            return self.quality

        base_quality = self.quality

        # Adjust based on image size
        width, height = img.size
        total_pixels = width * height

        if total_pixels < 500000:  # Small images
            return min(95, base_quality + 10)
        if total_pixels > 10000000:  # Large images
            return max(70, base_quality - 10)

        # Adjust based on file size (if available)
        try:
            file_size_mb = photo.size / (1024 * 1024)
            if file_size_mb < 1:  # Small file, might be lower quality
                return min(95, base_quality + 5)
            if file_size_mb > 20:  # Large file, can reduce quality
                return max(75, base_quality - 5)
        except:
            pass

        return base_quality

    def _enhance_image_for_thumbnail(self, img: Image.Image) -> Image.Image:
        """Apply subtle enhancements for better thumbnails."""
        try:
            from PIL import ImageEnhance

            # Slightly increase contrast for better visibility at small sizes
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)

            # Slightly increase sharpness
            enhancer = ImageEnhance.Sharpness(img)
            return enhancer.enhance(1.02)


        except Exception:
            # If enhancement fails, return original
            return img

    def _get_adaptive_save_kwargs(self, quality: int) -> dict[str, Any]:
        """Get adaptive save parameters."""
        if self.format == "webp":
            return {
                "quality": quality,
                "method": 6 if quality > 80 else 4,
                "optimize": True,
            }
        if self.format == "jpeg":
            return {
                "quality": quality,
                "optimize": True,
                "progressive": quality > 80,
            }
        return super()._get_save_kwargs()


class ThumbnailCacheManager:
    """Manager for thumbnail cache operations and maintenance."""

    def __init__(self, cache_root: str):
        self.cache = ThumbnailCache(cache_root)

    async def cleanup_orphaned_thumbnails(self, valid_file_ids: list[int]) -> int:
        """Remove thumbnails for files that no longer exist."""
        loop = asyncio.get_event_loop()
        removed_count = await loop.run_in_executor(
            None,
            self.cache.cleanup_orphaned_thumbnails,
            valid_file_ids
        )

        logger.info(f"Removed {removed_count} orphaned thumbnails")
        return removed_count

    async def cleanup_empty_directories(self) -> int:
        """Remove empty directories from cache."""
        loop = asyncio.get_event_loop()
        removed_count = await loop.run_in_executor(
            None,
            self.cache.cleanup_empty_directories
        )

        logger.info(f"Removed {removed_count} empty directories")
        return removed_count

    async def get_cache_statistics(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.cache.get_cache_stats
        )


    async def validate_cache_integrity(self, sample_size: int = 100) -> dict[str, Any]:
        """Validate cache integrity by checking a sample of files."""
        stats = await self.get_cache_statistics()

        if not stats["exists"] or stats["total_files"] == 0:
            return {
                "valid_files": 0,
                "invalid_files": 0,
                "missing_files": 0,
                "total_checked": 0,
            }

        # TODO: Implement sampling and validation logic
        # This would check if thumbnail files are valid images

        return {
            "valid_files": 0,
            "invalid_files": 0,
            "missing_files": 0,
            "total_checked": 0,
        }
