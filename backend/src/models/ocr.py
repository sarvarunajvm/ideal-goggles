"""OCR text model for photo search system."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


@dataclass
class OCRResult:
    """OCR text content extracted from images."""

    file_id: int
    text: str
    language: str = "eng"
    confidence: float = 0.0
    processed_at: Optional[float] = None

    @classmethod
    def from_tesseract_result(cls, file_id: int, tesseract_data: Dict[str, Any], language: str = "eng") -> "OCRResult":
        """Create OCRResult from Tesseract OCR output."""
        # Extract text and confidence from tesseract data
        text_parts = []
        confidences = []

        if 'text' in tesseract_data:
            # Simple text extraction
            text = str(tesseract_data['text']).strip()
            confidence = tesseract_data.get('conf', 0)
        else:
            # Detailed data with word-level information
            for i, word_text in enumerate(tesseract_data.get('text', [])):
                word_conf = tesseract_data.get('conf', [0])[i] if i < len(tesseract_data.get('conf', [])) else 0

                # Skip empty or low-confidence words
                if word_text.strip() and word_conf > 30:
                    text_parts.append(word_text.strip())
                    confidences.append(word_conf)

            text = ' '.join(text_parts)
            confidence = sum(confidences) / len(confidences) if confidences else 0

        # Clean up the text
        text = cls._clean_ocr_text(text)

        return cls(
            file_id=file_id,
            text=text,
            language=language,
            confidence=confidence / 100.0,  # Convert to 0-1 range
            processed_at=datetime.now().timestamp()
        )

    @classmethod
    def from_db_row(cls, row) -> "OCRResult":
        """Create OCRResult from database row."""
        return cls(
            file_id=row['file_id'],
            text=row['text'],
            language=row['language'],
            confidence=row['confidence'],
            processed_at=row['processed_at'],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'file_id': self.file_id,
            'text': self.text,
            'language': self.language,
            'confidence': self.confidence,
            'processed_at': self.processed_at,
        }

    def validate(self) -> List[str]:
        """Validate OCR data and return list of errors."""
        errors = []

        if self.file_id <= 0:
            errors.append("File ID must be positive")

        if not isinstance(self.text, str):
            errors.append("Text must be a string")

        if not (0.0 <= self.confidence <= 1.0):
            errors.append("Confidence must be between 0.0 and 1.0")

        if self.language and not re.match(r'^[a-z]{2,3}$', self.language):
            errors.append("Language must be a valid language code")

        return errors

    def is_valid(self) -> bool:
        """Check if OCR data is valid."""
        return len(self.validate()) == 0

    def has_meaningful_text(self, min_length: int = 3, min_confidence: float = 0.5) -> bool:
        """Check if OCR result contains meaningful text."""
        if self.confidence < min_confidence:
            return False

        cleaned_text = self.get_cleaned_text()
        return len(cleaned_text) >= min_length

    def get_cleaned_text(self) -> str:
        """Get cleaned text suitable for search indexing."""
        return self._clean_ocr_text(self.text)

    def get_word_count(self) -> int:
        """Get number of words in extracted text."""
        return len(self.get_cleaned_text().split())

    def get_confidence_grade(self) -> str:
        """Get confidence grade as letter."""
        if self.confidence >= 0.9:
            return "A"
        elif self.confidence >= 0.7:
            return "B"
        elif self.confidence >= 0.5:
            return "C"
        elif self.confidence >= 0.3:
            return "D"
        else:
            return "F"

    def extract_keywords(self, min_length: int = 3) -> List[str]:
        """Extract keywords from OCR text."""
        text = self.get_cleaned_text().lower()

        # Split into words and filter
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        keywords = [word for word in words if len(word) >= min_length]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)

        return unique_keywords

    def find_dates(self) -> List[str]:
        """Extract date patterns from OCR text."""
        text = self.get_cleaned_text()

        # Common date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b\w+\s+\d{1,2},?\s+\d{4}\b',       # Month DD, YYYY
            r'\b\d{1,2}\s+\w+\s+\d{4}\b',         # DD Month YYYY
        ]

        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        return list(set(dates))  # Remove duplicates

    def find_numbers(self) -> List[str]:
        """Extract number patterns from OCR text."""
        text = self.get_cleaned_text()

        # Find various number patterns
        patterns = [
            r'\b\d+\b',           # Simple numbers
            r'\b\d+\.\d+\b',      # Decimal numbers
            r'\b\d+,\d+\b',       # Numbers with commas
            r'\b\d+[-]\d+\b',     # Number ranges
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)

        return list(set(numbers))  # Remove duplicates

    def get_search_snippet(self, query: str, max_length: int = 150) -> str:
        """Get text snippet around search query for display."""
        text = self.get_cleaned_text()
        query_lower = query.lower()
        text_lower = text.lower()

        # Find query position
        query_pos = text_lower.find(query_lower)
        if query_pos == -1:
            # Query not found, return beginning of text
            return text[:max_length] + "..." if len(text) > max_length else text

        # Calculate snippet bounds
        start = max(0, query_pos - max_length // 2)
        end = min(len(text), start + max_length)

        # Adjust start if we're near the end
        if end - start < max_length:
            start = max(0, end - max_length)

        snippet = text[start:end]

        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    @staticmethod
    def _clean_ocr_text(text: str) -> str:
        """Clean OCR text by removing noise and normalizing."""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\-.,!?;:\'"()[\]{}]', '', text)

        # Remove isolated single characters (likely OCR errors)
        text = re.sub(r'\b[a-zA-Z]\b', '', text)

        # Clean up multiple punctuation
        text = re.sub(r'[.]{2,}', '...', text)
        text = re.sub(r'[,]{2,}', ',', text)

        # Normalize quotes
        text = re.sub(r'[""''`]', '"', text)

        return text.strip()


class OCRStats:
    """Statistics for OCR processing."""

    def __init__(self):
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_confidence = 0.0
        self.total_words = 0
        self.languages = {}

    def add_result(self, result: OCRResult, success: bool = True):
        """Add OCR result to statistics."""
        self.total_files += 1

        if success:
            self.processed_files += 1
            self.total_confidence += result.confidence
            self.total_words += result.get_word_count()

            # Track language usage
            if result.language in self.languages:
                self.languages[result.language] += 1
            else:
                self.languages[result.language] = 1
        else:
            self.failed_files += 1

    def get_average_confidence(self) -> float:
        """Get average confidence across all processed files."""
        if self.processed_files == 0:
            return 0.0
        return self.total_confidence / self.processed_files

    def get_average_words_per_file(self) -> float:
        """Get average word count per file."""
        if self.processed_files == 0:
            return 0.0
        return self.total_words / self.processed_files

    def get_success_rate(self) -> float:
        """Get OCR success rate."""
        if self.total_files == 0:
            return 0.0
        return self.processed_files / self.total_files

    def to_dict(self) -> dict:
        """Convert statistics to dictionary."""
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'average_confidence': round(self.get_average_confidence(), 3),
            'average_words_per_file': round(self.get_average_words_per_file(), 1),
            'success_rate': round(self.get_success_rate(), 3),
            'languages': self.languages,
            'total_words': self.total_words,
        }