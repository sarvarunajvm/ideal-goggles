"""Comprehensive unit tests for OCR worker module."""

import asyncio
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.models.ocr import OCRResult, OCRStats
from src.models.photo import Photo
from src.workers.ocr_worker import (
    OCRQualityFilter,
    SmartOCRWorker,
    TesseractOCRWorker,
)


@pytest.fixture
def mock_photo():
    """Create a mock photo for testing."""
    photo = Mock(spec=Photo)
    photo.id = 1
    photo.path = "/path/to/photo.jpg"
    return photo


@pytest.fixture
def mock_tesseract_success():
    """Mock successful tesseract execution."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
        "5\t1\t0\t0\t0\t0\t0\t0\t100\t100\t95\tHello\n"
        "5\t1\t0\t0\t0\t1\t100\t0\t100\t100\t90\tWorld\n"
    )
    mock_result.stderr = ""
    return mock_result


class TestTesseractOCRWorker:
    """Test TesseractOCRWorker class."""

    def test_worker_initialization_default(self):
        """Test OCR worker initialization with defaults."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()
            assert worker.max_workers == 2
            assert worker.languages == ["eng"]
            assert isinstance(worker.stats, OCRStats)
            assert worker.executor is not None

    def test_worker_initialization_custom(self):
        """Test OCR worker initialization with custom values."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker(max_workers=4, languages=["eng", "fra"])
            assert worker.max_workers == 4
            assert worker.languages == ["eng", "fra"]

    def test_validate_tesseract_success(self):
        """Test successful Tesseract validation."""
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "tesseract 5.0.0"

        langs_result = Mock()
        langs_result.returncode = 0
        langs_result.stdout = "List of available languages:\neng\nfra\ndeu\n"

        with patch("subprocess.run", side_effect=[version_result, langs_result]):
            worker = TesseractOCRWorker(languages=["eng", "fra"])
            assert worker.languages == ["eng", "fra"]

    def test_validate_tesseract_missing_language(self):
        """Test Tesseract validation with missing language."""
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "tesseract 5.0.0"

        langs_result = Mock()
        langs_result.returncode = 0
        langs_result.stdout = "List of available languages:\neng\n"

        with patch("subprocess.run", side_effect=[version_result, langs_result]):
            worker = TesseractOCRWorker(languages=["eng", "fra", "deu"])
            # Should only keep available languages
            assert worker.languages == ["eng"]

    def test_validate_tesseract_not_found(self):
        """Test Tesseract validation when not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="Tesseract validation failed"):
                TesseractOCRWorker()

    def test_validate_tesseract_timeout(self):
        """Test Tesseract validation timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
            with pytest.raises(RuntimeError, match="Tesseract validation failed"):
                TesseractOCRWorker()

    def test_validate_tesseract_error(self):
        """Test Tesseract validation with error return code."""
        error_result = Mock()
        error_result.returncode = 1

        with patch("subprocess.run", return_value=error_result):
            with pytest.raises(RuntimeError, match="Tesseract not found"):
                TesseractOCRWorker()

    @pytest.mark.asyncio
    async def test_extract_text_success(self, mock_photo, mock_tesseract_success):
        """Test successful text extraction."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch.object(worker, "_extract_text_sync") as mock_extract:
                mock_ocr_result = OCRResult(
                    file_id=1, text="Hello World", language="eng", confidence=0.9
                )
                mock_extract.return_value = mock_ocr_result

                result = await worker.extract_text(mock_photo)

                assert result is not None
                assert result.text == "Hello World"
                assert result.confidence == 0.9
                assert worker.stats.processed_files == 1

    @pytest.mark.asyncio
    async def test_extract_text_no_result(self, mock_photo):
        """Test text extraction with no OCR result."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch.object(worker, "_extract_text_sync", return_value=None):
                result = await worker.extract_text(mock_photo)

                assert result is None
                assert worker.stats.failed_files == 1

    @pytest.mark.asyncio
    async def test_extract_text_with_custom_language(self, mock_photo):
        """Test text extraction with custom language."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker(languages=["eng", "fra"])

            with patch.object(worker, "_extract_text_sync") as mock_extract:
                mock_ocr_result = OCRResult(
                    file_id=1, text="Bonjour", language="fra", confidence=0.9
                )
                mock_extract.return_value = mock_ocr_result

                result = await worker.extract_text(mock_photo, language="fra")

                assert result is not None
                assert result.language == "fra"
                mock_extract.assert_called_once_with("/path/to/photo.jpg", "fra")

    @pytest.mark.asyncio
    async def test_extract_text_exception(self, mock_photo):
        """Test text extraction handles exceptions."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch.object(
                worker, "_extract_text_sync", side_effect=Exception("OCR error")
            ):
                result = await worker.extract_text(mock_photo)

                assert result is None
                assert worker.stats.failed_files == 1

    def test_extract_text_sync_success(self, mock_tesseract_success):
        """Test synchronous text extraction."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch("subprocess.run", return_value=mock_tesseract_success):
                with patch("shutil.copy2"):
                    result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                    assert result is not None
                    assert "Hello" in result.text
                    assert "World" in result.text
                    assert result.confidence > 0

    def test_extract_text_sync_tesseract_failure(self):
        """Test synchronous extraction with Tesseract failure."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            error_result = Mock()
            error_result.returncode = 1
            error_result.stderr = "Error processing image"

            with patch("subprocess.run", return_value=error_result):
                result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                assert result is None

    def test_extract_text_sync_empty_output(self):
        """Test synchronous extraction with empty output."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            empty_result = Mock()
            empty_result.returncode = 0
            empty_result.stdout = ""

            with patch("subprocess.run", return_value=empty_result):
                result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                assert result is None

    def test_extract_text_sync_low_confidence(self):
        """Test synchronous extraction filters low confidence words."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            low_conf_result = Mock()
            low_conf_result.returncode = 0
            low_conf_result.stdout = (
                "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
                "5\t1\t0\t0\t0\t0\t0\t0\t100\t100\t95\tGood\n"
                "5\t1\t0\t0\t0\t1\t100\t0\t100\t100\t20\tBad\n"  # Low confidence
            )

            with patch("subprocess.run", return_value=low_conf_result):
                with patch("shutil.copy2"):
                    result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                    assert result is not None
                    assert "Good" in result.text
                    assert "Bad" not in result.text  # Filtered out

    def test_extract_text_sync_timeout(self):
        """Test synchronous extraction timeout."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)
            ):
                result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                assert result is None

    def test_extract_text_sync_exception(self):
        """Test synchronous extraction handles exceptions."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch("shutil.copy2", side_effect=Exception("Copy error")):
                result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                assert result is None

    @pytest.mark.asyncio
    async def test_extract_batch_empty(self):
        """Test batch extraction with empty list."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()
            results = await worker.extract_batch([])
            assert results == []

    @pytest.mark.asyncio
    async def test_extract_batch_success(self, mock_photo):
        """Test successful batch extraction."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            photos = [mock_photo, mock_photo]

            with patch.object(worker, "extract_text") as mock_extract:
                mock_result = OCRResult(
                    file_id=0, text="Test", language="eng", confidence=0.9
                )
                mock_extract.return_value = mock_result

                results = await worker.extract_batch(photos)

                assert len(results) == 2
                assert all(r.file_id == mock_photo.id for r in results)

    @pytest.mark.asyncio
    async def test_extract_batch_partial_success(self, mock_photo):
        """Test batch extraction with partial success."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            photos = [mock_photo, mock_photo, mock_photo]

            with patch.object(worker, "extract_text") as mock_extract:
                # First succeeds, second fails, third succeeds
                mock_result = OCRResult(
                    file_id=0, text="Test", language="eng", confidence=0.9
                )
                mock_extract.side_effect = [mock_result, None, mock_result]

                results = await worker.extract_batch(photos)

                assert len(results) == 3
                assert results[0] is not None
                assert results[1] is None
                assert results[2] is not None

    def test_get_statistics(self):
        """Test getting OCR statistics."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker(max_workers=4, languages=["eng", "fra"])

            stats = worker.get_statistics()

            assert "languages" in stats
            assert "max_workers" in stats
            assert stats["languages"] == ["eng", "fra"]
            assert stats["max_workers"] == 4

    def test_reset_statistics(self):
        """Test resetting OCR statistics."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            # Add some stats
            mock_result = OCRResult(
                file_id=1, text="Test", language="eng", confidence=0.9
            )
            worker.stats.add_result(mock_result, success=True)

            assert worker.stats.processed_files > 0

            worker.reset_statistics()

            assert worker.stats.processed_files == 0

    def test_shutdown(self):
        """Test worker shutdown."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = TesseractOCRWorker()

            with patch.object(worker.executor, "shutdown") as mock_shutdown:
                worker.shutdown()
                mock_shutdown.assert_called_once_with(wait=True)


class TestSmartOCRWorker:
    """Test SmartOCRWorker class."""

    def test_smart_worker_initialization_with_pil(self):
        """Test SmartOCRWorker initialization with PIL available."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = SmartOCRWorker(enable_preprocessing=True)
            assert worker.enable_preprocessing
            # pil_available depends on whether PIL is installed in the environment

    def test_smart_worker_initialization_without_pil(self):
        """Test SmartOCRWorker initialization with preprocessing disabled."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = SmartOCRWorker(enable_preprocessing=False)
            assert not worker.enable_preprocessing

    def test_extract_text_sync_with_preprocessing(self, mock_tesseract_success):
        """Test extraction with preprocessing enabled."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = SmartOCRWorker(enable_preprocessing=True)
            worker.pil_available = True

            with patch.object(worker, "_extract_with_preprocessing") as mock_preprocess:
                mock_result = OCRResult(
                    file_id=1, text="Test", language="eng", confidence=0.9
                )
                mock_preprocess.return_value = mock_result

                result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                assert result is not None
                mock_preprocess.assert_called_once()

    def test_extract_text_sync_without_preprocessing(self, mock_tesseract_success):
        """Test extraction without preprocessing."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            worker = SmartOCRWorker(enable_preprocessing=False)

            with patch("subprocess.run", return_value=mock_tesseract_success):
                with patch("shutil.copy2"):
                    result = worker._extract_text_sync("/path/to/photo.jpg", "eng")

                    assert result is not None

    def test_extract_with_preprocessing_success(self, mock_tesseract_success):
        """Test preprocessing and extraction."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image") as mock_image_module:
                with patch("PIL.ImageEnhance"):
                    with patch("PIL.ImageFilter"):
                        worker = SmartOCRWorker()
                        worker.pil_available = True

                        # Mock PIL Image
                        mock_img = Mock()
                        mock_img.mode = "RGB"
                        mock_img.__enter__ = Mock(return_value=mock_img)
                        mock_img.__exit__ = Mock(return_value=False)

                        mock_image_module.open.return_value = mock_img

                        with patch.object(
                            worker, "_preprocess_image", return_value=mock_img
                        ):
                            with patch.object(
                                worker, "_run_tesseract_on_file"
                            ) as mock_tesseract:
                                mock_result = OCRResult(
                                    file_id=1,
                                    text="Test",
                                    language="eng",
                                    confidence=0.9,
                                )
                                mock_tesseract.return_value = mock_result

                                result = worker._extract_with_preprocessing(
                                    "/path/to/photo.jpg", "eng"
                                )

                                assert result is not None

    def test_extract_with_preprocessing_fallback(self):
        """Test preprocessing falls back to normal extraction on error."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image") as mock_image_module:
                with patch("PIL.ImageEnhance"):
                    with patch("PIL.ImageFilter"):
                        worker = SmartOCRWorker()
                        worker.pil_available = True

                        mock_image_module.open.side_effect = Exception("Image error")

                        with patch.object(
                            TesseractOCRWorker, "_extract_text_sync"
                        ) as mock_base:
                            mock_result = OCRResult(
                                file_id=1, text="Test", language="eng", confidence=0.9
                            )
                            mock_base.return_value = mock_result

                            result = worker._extract_with_preprocessing(
                                "/path/to/photo.jpg", "eng"
                            )

                            assert result is not None
                            mock_base.assert_called_once()

    def test_preprocess_image_small(self):
        """Test preprocessing upscales small images."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image") as mock_image_module:
                with patch("PIL.ImageEnhance") as mock_enhance_module:
                    with patch("PIL.ImageFilter") as mock_filter_module:
                        worker = SmartOCRWorker()

                        mock_img = Mock()
                        mock_img.size = (200, 200)  # Small image

                        mock_resized = Mock()
                        mock_img.resize.return_value = mock_resized

                        mock_enhancer = Mock()
                        mock_enhancer.enhance.return_value = mock_resized

                        mock_enhance_module.Contrast.return_value = mock_enhancer
                        mock_enhance_module.Sharpness.return_value = mock_enhancer

                        mock_resized.filter.return_value = mock_resized

                        result = worker._preprocess_image(mock_img)

                        # Should upscale
                        mock_img.resize.assert_called_once()

    def test_preprocess_image_large(self):
        """Test preprocessing downscales large images."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image") as mock_image_module:
                with patch("PIL.ImageEnhance") as mock_enhance_module:
                    with patch("PIL.ImageFilter") as mock_filter_module:
                        worker = SmartOCRWorker()

                        mock_img = Mock()
                        mock_img.size = (5000, 5000)  # Large image

                        mock_resized = Mock()
                        mock_img.resize.return_value = mock_resized

                        mock_enhancer = Mock()
                        mock_enhancer.enhance.return_value = mock_resized

                        mock_enhance_module.Contrast.return_value = mock_enhancer
                        mock_enhance_module.Sharpness.return_value = mock_enhancer

                        mock_resized.filter.return_value = mock_resized

                        result = worker._preprocess_image(mock_img)

                        # Should downscale
                        mock_img.resize.assert_called_once()

    def test_run_tesseract_on_file_multiple_psm(self):
        """Test running Tesseract with multiple PSM modes."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image"):
                with patch("PIL.ImageEnhance"):
                    with patch("PIL.ImageFilter"):
                        worker = SmartOCRWorker()

                        # Mock different confidence levels for different PSM modes
                        results = []
                        for conf in [0.7, 0.9, 0.6]:
                            mock_result = Mock()
                            mock_result.returncode = 0
                            mock_result.stdout = (
                                f"level\tconf\ttext\n5\t{int(conf*100)}\tTest\n"
                            )
                            results.append(mock_result)

                        with patch("subprocess.run", side_effect=results):
                            with patch.object(
                                worker, "_parse_tesseract_output"
                            ) as mock_parse:
                                ocr_results = [
                                    OCRResult(
                                        file_id=1,
                                        text="Test",
                                        language="eng",
                                        confidence=conf,
                                    )
                                    for conf in [0.7, 0.9, 0.6]
                                ]
                                mock_parse.side_effect = ocr_results

                                result = worker._run_tesseract_on_file(
                                    "/path/to/photo.jpg", "eng"
                                )

                                # Should return best result (0.9 confidence)
                                assert result is not None
                                assert result.confidence == 0.9

    def test_run_tesseract_on_file_timeout(self):
        """Test running Tesseract with timeout."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image"):
                with patch("PIL.ImageEnhance"):
                    with patch("PIL.ImageFilter"):
                        worker = SmartOCRWorker()

                        with patch(
                            "subprocess.run",
                            side_effect=subprocess.TimeoutExpired("cmd", 30),
                        ):
                            result = worker._run_tesseract_on_file(
                                "/path/to/photo.jpg", "eng"
                            )

                            assert result is None

    def test_parse_tesseract_output_success(self):
        """Test parsing Tesseract TSV output."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image"):
                with patch("PIL.ImageEnhance"):
                    with patch("PIL.ImageFilter"):
                        worker = SmartOCRWorker()

                        tsv_output = (
                            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
                            "5\t1\t0\t0\t0\t0\t0\t0\t100\t100\t95\tHello\n"
                            "5\t1\t0\t0\t0\t1\t100\t0\t100\t100\t90\tWorld\n"
                        )

                        result = worker._parse_tesseract_output(tsv_output, "eng")

                        assert result is not None
                        assert "Hello" in result.text
                        assert "World" in result.text
                        assert result.confidence > 0

    def test_parse_tesseract_output_empty(self):
        """Test parsing empty Tesseract output."""
        with patch.object(TesseractOCRWorker, "_validate_tesseract"):
            with patch("PIL.Image"):
                with patch("PIL.ImageEnhance"):
                    with patch("PIL.ImageFilter"):
                        worker = SmartOCRWorker()

                        result = worker._parse_tesseract_output("", "eng")

                        assert result is None


class TestOCRQualityFilter:
    """Test OCRQualityFilter class."""

    def test_filter_initialization_default(self):
        """Test filter initialization with defaults."""
        filter_obj = OCRQualityFilter()
        assert filter_obj.min_confidence == 0.5
        assert filter_obj.min_word_count == 2
        assert filter_obj.max_gibberish_ratio == 0.3

    def test_filter_initialization_custom(self):
        """Test filter initialization with custom values."""
        filter_obj = OCRQualityFilter(
            min_confidence=0.7, min_word_count=5, max_gibberish_ratio=0.2
        )
        assert filter_obj.min_confidence == 0.7
        assert filter_obj.min_word_count == 5
        assert filter_obj.max_gibberish_ratio == 0.2

    def test_should_keep_result_good_quality(self):
        """Test filter keeps good quality results."""
        filter_obj = OCRQualityFilter()

        result = OCRResult(file_id=1, text="This is good quality text", confidence=0.9)

        assert filter_obj.should_keep_result(result)

    def test_should_keep_result_low_confidence(self):
        """Test filter rejects low confidence results."""
        filter_obj = OCRQualityFilter(min_confidence=0.7)

        result = OCRResult(file_id=1, text="Low confidence text", confidence=0.5)

        assert not filter_obj.should_keep_result(result)

    def test_should_keep_result_few_words(self):
        """Test filter rejects results with too few words."""
        filter_obj = OCRQualityFilter(min_word_count=5)

        result = OCRResult(file_id=1, text="Few words", confidence=0.9)

        assert not filter_obj.should_keep_result(result)

    def test_should_keep_result_none(self):
        """Test filter rejects None results."""
        filter_obj = OCRQualityFilter()

        assert not filter_obj.should_keep_result(None)

    def test_should_keep_result_gibberish(self):
        """Test filter rejects gibberish text."""
        filter_obj = OCRQualityFilter()

        result = OCRResult(file_id=1, text="xyz qwerty asdfgh zxcvbn", confidence=0.9)

        # Should be rejected as gibberish
        assert not filter_obj.should_keep_result(result)

    def test_is_mostly_gibberish_empty(self):
        """Test gibberish detection for empty text."""
        filter_obj = OCRQualityFilter()

        assert filter_obj._is_mostly_gibberish("")
        assert filter_obj._is_mostly_gibberish("   ")

    def test_is_mostly_gibberish_good_text(self):
        """Test gibberish detection for good text."""
        filter_obj = OCRQualityFilter()

        assert not filter_obj._is_mostly_gibberish("This is good readable text")

    def test_is_mostly_gibberish_mixed(self):
        """Test gibberish detection for mixed text."""
        filter_obj = OCRQualityFilter(max_gibberish_ratio=0.3)

        # More than 30% gibberish
        text = "good text words xyz qwerty asdfgh zxcvbn"
        assert filter_obj._is_mostly_gibberish(text)

    def test_is_gibberish_word_short(self):
        """Test single word gibberish detection for short words."""
        filter_obj = OCRQualityFilter()

        assert filter_obj._is_gibberish_word("x")
        assert filter_obj._is_gibberish_word("a")

    def test_is_gibberish_word_no_vowels(self):
        """Test single word gibberish detection for consonant-only words."""
        filter_obj = OCRQualityFilter()

        assert filter_obj._is_gibberish_word("xyz")
        assert filter_obj._is_gibberish_word("bcdfg")

    def test_is_gibberish_word_excessive_consonants(self):
        """Test single word gibberish detection for excessive consonants."""
        filter_obj = OCRQualityFilter()

        assert filter_obj._is_gibberish_word("qwrtypsdfghjkl")

    def test_is_gibberish_word_repeating_pattern(self):
        """Test single word gibberish detection for repeating patterns."""
        filter_obj = OCRQualityFilter()

        # Very repetitive patterns (less than 1/3 unique characters)
        assert filter_obj._is_gibberish_word("aaaa")  # 1 unique / 4 chars = 0.25
        assert filter_obj._is_gibberish_word("bbbbb")  # 1 unique / 5 chars = 0.2
        assert filter_obj._is_gibberish_word("aaaaaa")  # 1 unique / 6 chars = 0.16

    def test_is_gibberish_word_valid(self):
        """Test single word gibberish detection for valid words."""
        filter_obj = OCRQualityFilter()

        assert not filter_obj._is_gibberish_word("hello")
        assert not filter_obj._is_gibberish_word("world")
        assert not filter_obj._is_gibberish_word("quality")
