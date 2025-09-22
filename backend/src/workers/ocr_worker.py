"""OCR worker with Tesseract integration for text extraction from images."""

import asyncio
import contextlib
import logging
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from ..models.ocr import OCRResult, OCRStats
from ..models.photo import Photo

logger = logging.getLogger(__name__)


class TesseractOCRWorker:
    """OCR worker using Tesseract for text extraction."""

    def __init__(self, max_workers: int = 2, languages: list[str] | None = None):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.languages = languages or ["eng"]
        self.stats = OCRStats()

        # Validate Tesseract installation
        self._validate_tesseract()

    def _validate_tesseract(self):
        """Validate Tesseract installation and available languages."""
        try:
            # Check if tesseract is available
            result = subprocess.run(
                ["tesseract", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                msg = "Tesseract not found or not working"
                raise RuntimeError(msg)

            logger.info(f"Tesseract version: {result.stdout.split()[1]}")

            # Check available languages
            lang_result = subprocess.run(
                ["tesseract", "--list-langs"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if lang_result.returncode == 0:
                available_langs = set(lang_result.stdout.strip().split("\n")[1:])
                requested_langs = set(self.languages)

                missing_langs = requested_langs - available_langs
                if missing_langs:
                    logger.warning(f"Missing Tesseract languages: {missing_langs}")
                    # Remove missing languages
                    self.languages = [
                        lang for lang in self.languages if lang in available_langs
                    ]

                logger.info(f"Using Tesseract languages: {self.languages}")

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as e:
            msg = f"Tesseract validation failed: {e}"
            raise RuntimeError(msg)

    async def extract_text(
        self, photo: Photo, language: str | None = None
    ) -> OCRResult | None:
        """Extract text from a photo using Tesseract OCR."""
        start_time = time.time()

        try:
            # Use specified language or default
            ocr_language = language or self.languages[0]

            # Run OCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ocr_result = await loop.run_in_executor(
                self.executor, self._extract_text_sync, photo.path, ocr_language
            )

            time.time() - start_time

            if ocr_result:
                self.stats.add_result(ocr_result, success=True)
                logger.debug(
                    f"OCR extracted {ocr_result.get_word_count()} words from {photo.path}"
                )
                return ocr_result
            self.stats.add_result(None, success=False)
            return None

        except Exception as e:
            logger.warning(f"OCR failed for {photo.path}: {e}")
            self.stats.add_result(None, success=False)
            return None

    def _extract_text_sync(self, file_path: str, language: str) -> OCRResult | None:
        """Synchronously extract text using Tesseract."""
        try:
            # For safety, create a copy of the image in temp directory
            with tempfile.NamedTemporaryFile(
                suffix=Path(file_path).suffix, delete=False
            ) as temp_file:
                temp_path = temp_file.name

            try:
                # Copy file to temp location for processing
                import shutil

                shutil.copy2(file_path, temp_path)

                # Run Tesseract with detailed output
                cmd = [
                    "tesseract",
                    temp_path,
                    "stdout",
                    "-l",
                    language,
                    "--psm",
                    "3",  # Fully automatic page segmentation
                    "--oem",
                    "3",  # Default OCR Engine Mode
                    "-c",
                    "tessedit_create_tsv=1",  # Create TSV output for confidence scores
                ]

                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 second timeout
                )

                if result.returncode != 0:
                    logger.debug(f"Tesseract failed for {file_path}: {result.stderr}")
                    return None

                # Parse TSV output for confidence scores
                tsv_lines = result.stdout.strip().split("\n")
                if len(tsv_lines) < 2:
                    return None

                # Extract text and confidence
                text_parts = []
                confidences = []

                for line in tsv_lines[1:]:  # Skip header
                    fields = line.split("\t")
                    if len(fields) >= 12:
                        word_text = fields[11].strip()
                        try:
                            confidence = float(fields[10])
                        except (ValueError, IndexError):
                            confidence = 0

                        if word_text and confidence > 30:  # Filter low confidence words
                            text_parts.append(word_text)
                            confidences.append(confidence)

                if not text_parts:
                    return None

                full_text = " ".join(text_parts)
                avg_confidence = (
                    sum(confidences) / len(confidences) if confidences else 0
                )

                # Create OCR result
                # We need file_id, but we only have file_path here
                # This would typically be resolved by the calling code
                return OCRResult(
                    file_id=0,  # Will be set by caller
                    text=full_text,
                    language=language,
                    confidence=avg_confidence / 100.0,  # Convert to 0-1 range
                    processed_at=time.time(),
                )

            finally:
                # Clean up temp file
                with contextlib.suppress(OSError):
                    os.unlink(temp_path)

        except Exception as e:
            logger.debug(f"Tesseract processing failed for {file_path}: {e}")
            return None

    async def extract_batch(
        self, photos: list[Photo], language: str | None = None
    ) -> list[OCRResult | None]:
        """Extract text from multiple photos concurrently."""
        if not photos:
            return []

        logger.info(f"Starting OCR for {len(photos)} photos")

        # Create tasks for concurrent processing
        tasks = [self.extract_text(photo, language) for photo in photos]

        # Process with progress logging
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Set file_id for successful results
            if result and i < len(photos):
                result.file_id = photos[i].id

            # Log progress periodically
            if (i + 1) % 50 == 0:
                logger.info(f"OCR progress: {i + 1}/{len(photos)}")

        successful_count = len([r for r in results if r])
        logger.info(f"OCR completed: {successful_count}/{len(photos)} successful")

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get OCR processing statistics."""
        stats_dict = self.stats.to_dict()
        stats_dict.update(
            {
                "languages": self.languages,
                "max_workers": self.max_workers,
            }
        )
        return stats_dict

    def reset_statistics(self):
        """Reset OCR statistics."""
        self.stats = OCRStats()

    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)


class SmartOCRWorker(TesseractOCRWorker):
    """Smart OCR worker with image preprocessing and optimization."""

    def __init__(
        self,
        max_workers: int = 2,
        languages: list[str] | None = None,
        enable_preprocessing: bool = True,
    ):
        super().__init__(max_workers, languages)
        self.enable_preprocessing = enable_preprocessing

        # Try to import PIL for image preprocessing
        self.pil_available = False
        try:
            from PIL import Image, ImageEnhance, ImageFilter

            self.pil_available = True
            logger.info("PIL available for OCR preprocessing")
        except ImportError:
            logger.warning("PIL not available, skipping OCR preprocessing")

    def _extract_text_sync(self, file_path: str, language: str) -> OCRResult | None:
        """Enhanced text extraction with preprocessing."""
        if self.enable_preprocessing and self.pil_available:
            return self._extract_with_preprocessing(file_path, language)
        return super()._extract_text_sync(file_path, language)

    def _extract_with_preprocessing(
        self, file_path: str, language: str
    ) -> OCRResult | None:
        """Extract text with image preprocessing for better accuracy."""
        try:
            from PIL import Image

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Load and preprocess image
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    # Apply preprocessing steps
                    processed_img = self._preprocess_image(img)

                    # Save preprocessed image
                    processed_img.save(temp_path, "PNG")

                # Run OCR on preprocessed image
                return self._run_tesseract_on_file(temp_path, language)

            finally:
                # Clean up temp file
                with contextlib.suppress(OSError):
                    os.unlink(temp_path)

        except Exception as e:
            logger.debug(
                f"Preprocessing failed for {file_path}, trying direct OCR: {e}"
            )
            return super()._extract_text_sync(file_path, language)

    def _preprocess_image(self, img):
        """Apply image preprocessing for better OCR accuracy."""
        from PIL import Image, ImageEnhance, ImageFilter

        # Resize if image is too small or too large
        width, height = img.size
        if width < 300 or height < 300:
            # Upscale small images
            scale_factor = max(300 / width, 300 / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        elif width > 3000 or height > 3000:
            # Downscale very large images
            scale_factor = min(3000 / width, 3000 / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)

        # Apply slight denoising
        return img.filter(ImageFilter.MedianFilter(size=3))

    def _run_tesseract_on_file(self, file_path: str, language: str) -> OCRResult | None:
        """Run Tesseract on a preprocessed file."""
        try:
            # Try multiple PSM modes for better results
            psm_modes = [3, 6, 4]  # Different page segmentation modes

            best_result = None
            best_confidence = 0

            for psm in psm_modes:
                cmd = [
                    "tesseract",
                    file_path,
                    "stdout",
                    "-l",
                    language,
                    "--psm",
                    str(psm),
                    "--oem",
                    "3",
                    "-c",
                    "tessedit_create_tsv=1",
                ]

                try:
                    result = subprocess.run(
                        cmd, check=False, capture_output=True, text=True, timeout=30
                    )

                    if result.returncode == 0:
                        ocr_result = self._parse_tesseract_output(
                            result.stdout, language
                        )
                        if ocr_result and ocr_result.confidence > best_confidence:
                            best_result = ocr_result
                            best_confidence = ocr_result.confidence

                except subprocess.TimeoutExpired:
                    continue

            return best_result

        except Exception as e:
            logger.debug(f"Enhanced Tesseract processing failed: {e}")
            return None

    def _parse_tesseract_output(
        self, tsv_output: str, language: str
    ) -> OCRResult | None:
        """Parse Tesseract TSV output."""
        lines = tsv_output.strip().split("\n")
        if len(lines) < 2:
            return None

        text_parts = []
        confidences = []

        for line in lines[1:]:  # Skip header
            fields = line.split("\t")
            if len(fields) >= 12:
                word_text = fields[11].strip()
                try:
                    confidence = float(fields[10])
                except (ValueError, IndexError):
                    confidence = 0

                if word_text and confidence > 30:
                    text_parts.append(word_text)
                    confidences.append(confidence)

        if not text_parts:
            return None

        full_text = " ".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return OCRResult(
            file_id=0,  # Will be set by caller
            text=full_text,
            language=language,
            confidence=avg_confidence / 100.0,
            processed_at=time.time(),
        )


class OCRQualityFilter:
    """Filter for OCR results based on quality metrics."""

    def __init__(
        self,
        min_confidence: float = 0.5,
        min_word_count: int = 2,
        max_gibberish_ratio: float = 0.3,
    ):
        self.min_confidence = min_confidence
        self.min_word_count = min_word_count
        self.max_gibberish_ratio = max_gibberish_ratio

    def should_keep_result(self, ocr_result: OCRResult) -> bool:
        """Determine if OCR result meets quality criteria."""
        if not ocr_result:
            return False

        # Check confidence threshold
        if ocr_result.confidence < self.min_confidence:
            return False

        # Check word count
        if ocr_result.get_word_count() < self.min_word_count:
            return False

        # Check for gibberish
        return not self._is_mostly_gibberish(ocr_result.text)

    def _is_mostly_gibberish(self, text: str) -> bool:
        """Detect if text is mostly gibberish."""
        if not text:
            return True

        words = text.split()
        if not words:
            return True

        gibberish_count = 0

        for word in words:
            if self._is_gibberish_word(word):
                gibberish_count += 1

        gibberish_ratio = gibberish_count / len(words)
        return gibberish_ratio > self.max_gibberish_ratio

    def _is_gibberish_word(self, word: str) -> bool:
        """Check if a single word appears to be gibberish."""
        if len(word) < 2:
            return True

        # Check for excessive consonants or vowels
        vowels = set("aeiouAEIOU")
        consonants = set("bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ")

        vowel_count = sum(1 for c in word if c in vowels)
        consonant_count = sum(1 for c in word if c in consonants)

        # Words with no vowels or excessive consonants are likely gibberish
        if vowel_count == 0 and len(word) > 2:
            return True

        if consonant_count > len(word) * 0.8:
            return True

        # Check for repeating patterns
        return len(set(word.lower())) < len(word) / 3
