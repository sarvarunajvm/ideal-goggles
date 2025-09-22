"""Thumbnail model for photo search system."""

import contextlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Thumbnail:
    """Cached preview images for fast grid display."""

    file_id: int
    thumb_path: str
    width: int
    height: int
    format: str = "webp"
    generated_at: float | None = None

    def __post_init__(self):
        """Post-initialization validation and defaults."""
        if self.generated_at is None:
            self.generated_at = datetime.now().timestamp()

        # Normalize format
        self.format = self.format.lower()

    @classmethod
    def create_for_photo(cls, file_id: int, original_width: int, original_height: int,
                        max_size: int = 512, img_format: str = "webp") -> "Thumbnail":
        """Create thumbnail specification for a photo."""
        # Calculate thumbnail dimensions while preserving aspect ratio
        thumb_width, thumb_height = cls._calculate_thumbnail_size(
            original_width, original_height, max_size
        )

        # Generate thumbnail path
        thumb_path = cls._generate_thumbnail_path(file_id, img_format)

        return cls(
            file_id=file_id,
            thumb_path=thumb_path,
            width=thumb_width,
            height=thumb_height,
            format=img_format,
            generated_at=datetime.now().timestamp()
        )

    @classmethod
    def from_db_row(cls, row) -> "Thumbnail":
        """Create Thumbnail from database row."""
        return cls(
            file_id=row["file_id"],
            thumb_path=row["thumb_path"],
            width=row["width"],
            height=row["height"],
            format=row["format"],
            generated_at=row["generated_at"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "file_id": self.file_id,
            "thumb_path": self.thumb_path,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "generated_at": self.generated_at,
        }

    def to_db_params(self) -> tuple:
        """Convert to database parameters for insertion."""
        return (
            self.file_id,
            self.thumb_path,
            self.width,
            self.height,
            self.format,
            self.generated_at
        )

    def validate(self) -> list[str]:
        """Validate thumbnail data and return list of errors."""
        errors = []

        if self.file_id <= 0:
            errors.append("File ID must be positive")

        if not self.thumb_path:
            errors.append("Thumbnail path is required")

        if self.width <= 0 or self.height <= 0:
            errors.append("Width and height must be positive")

        if self.width > 1024 or self.height > 1024:
            errors.append("Thumbnail dimensions too large (max 1024px)")

        if self.format not in ["webp", "jpeg", "png"]:
            errors.append(f"Unsupported thumbnail format: {self.format}")

        return errors

    def is_valid(self) -> bool:
        """Check if thumbnail data is valid."""
        return len(self.validate()) == 0

    def get_absolute_path(self, cache_root: str) -> str:
        """Get absolute path to thumbnail file."""
        cache_path = Path(cache_root)
        return str(cache_path / self.thumb_path)

    def file_exists(self, cache_root: str) -> bool:
        """Check if thumbnail file exists."""
        abs_path = self.get_absolute_path(cache_root)
        return Path(abs_path).exists()

    def get_file_size(self, cache_root: str) -> int | None:
        """Get thumbnail file size in bytes."""
        abs_path = self.get_absolute_path(cache_root)
        try:
            return Path(abs_path).stat().st_size
        except FileNotFoundError:
            return None

    def get_aspect_ratio(self) -> float:
        """Get thumbnail aspect ratio."""
        if self.height == 0:
            return 0.0
        return self.width / self.height

    def is_landscape(self) -> bool:
        """Check if thumbnail is landscape orientation."""
        return self.width > self.height

    def is_portrait(self) -> bool:
        """Check if thumbnail is portrait orientation."""
        return self.height > self.width

    def is_square(self, tolerance: float = 0.05) -> bool:
        """Check if thumbnail is approximately square."""
        aspect_ratio = self.get_aspect_ratio()
        return abs(aspect_ratio - 1.0) <= tolerance

    def needs_regeneration(self, original_modified_time: float, cache_root: str) -> bool:
        """Check if thumbnail needs regeneration."""
        # Check if thumbnail is older than original file
        if self.generated_at < original_modified_time:
            return True

        # Check if thumbnail file doesn't exist
        return bool(not self.file_exists(cache_root))

    def get_size_category(self) -> str:
        """Get size category for UI purposes."""
        max_dimension = max(self.width, self.height)

        if max_dimension <= 128:
            return "small"
        if max_dimension <= 256:
            return "medium"
        if max_dimension <= 512:
            return "large"
        return "xlarge"

    def get_display_size(self, target_size: int) -> tuple[int, int]:
        """Get display dimensions for a target size."""
        if target_size <= 0:
            return self.width, self.height

        aspect_ratio = self.get_aspect_ratio()

        if self.width > self.height:
            # Landscape
            display_width = target_size
            display_height = int(target_size / aspect_ratio)
        else:
            # Portrait or square
            display_height = target_size
            display_width = int(target_size * aspect_ratio)

        return display_width, display_height

    @staticmethod
    def _calculate_thumbnail_size(original_width: int, original_height: int, max_size: int) -> tuple[int, int]:
        """Calculate thumbnail dimensions preserving aspect ratio."""
        if original_width <= 0 or original_height <= 0:
            return max_size, max_size

        aspect_ratio = original_width / original_height

        if original_width > original_height:
            # Landscape
            thumb_width = min(max_size, original_width)
            thumb_height = int(thumb_width / aspect_ratio)
        else:
            # Portrait or square
            thumb_height = min(max_size, original_height)
            thumb_width = int(thumb_height * aspect_ratio)

        # Ensure minimum size
        thumb_width = max(1, thumb_width)
        thumb_height = max(1, thumb_height)

        return thumb_width, thumb_height

    @staticmethod
    def _generate_thumbnail_path(file_id: int, img_format: str) -> str:
        """Generate relative path for thumbnail storage."""
        # Use file_id to create directory structure for better performance
        # e.g., file_id 12345 -> 12/34/12345.webp
        file_id_str = str(file_id)

        if len(file_id_str) >= 4:
            dir1 = file_id_str[-2:]
            dir2 = file_id_str[-4:-2]
        else:
            dir1 = "00"
            dir2 = "00"

        filename = f"{file_id}.{img_format}"
        return f"{dir1}/{dir2}/{filename}"

    @staticmethod
    def get_cache_directory_structure(cache_root: str) -> dict:
        """Get information about cache directory structure."""
        cache_path = Path(cache_root)

        if not cache_path.exists():
            return {
                "exists": False,
                "total_files": 0,
                "total_size_bytes": 0,
                "directories": 0,
            }

        total_files = 0
        total_size = 0
        directories = 0

        for item in cache_path.rglob("*"):
            if item.is_file():
                total_files += 1
                with contextlib.suppress(OSError):
                    total_size += item.stat().st_size
            elif item.is_dir():
                directories += 1

        return {
            "exists": True,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "directories": directories,
        }


class ThumbnailCache:
    """Manager for thumbnail cache operations."""

    def __init__(self, cache_root: str, max_size: int = 512, img_format: str = "webp"):
        self.cache_root = Path(cache_root)
        self.max_size = max_size
        self.format = img_format
        self.cache_root.mkdir(parents=True, exist_ok=True)

    def get_thumbnail_path(self, file_id: int) -> str:
        """Get absolute path for thumbnail."""
        thumb_path = Thumbnail._generate_thumbnail_path(file_id, self.format)
        return str(self.cache_root / thumb_path)

    def ensure_directory_exists(self, file_id: int):
        """Ensure thumbnail directory exists."""
        thumb_path = Thumbnail._generate_thumbnail_path(file_id, self.format)
        full_path = self.cache_root / thumb_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

    def cleanup_orphaned_thumbnails(self, valid_file_ids: list[int]) -> int:
        """Remove thumbnails for files that no longer exist."""
        valid_ids_set = set(valid_file_ids)
        removed_count = 0

        for thumb_file in self.cache_root.rglob(f"*.{self.format}"):
            try:
                # Extract file_id from filename
                file_id = int(thumb_file.stem)
                if file_id not in valid_ids_set:
                    thumb_file.unlink()
                    removed_count += 1
            except (ValueError, OSError):
                # Skip files that don't match expected pattern
                continue

        return removed_count

    def cleanup_empty_directories(self) -> int:
        """Remove empty directories from cache."""
        removed_count = 0

        # Walk directories from deepest to shallowest
        for dir_path in sorted(self.cache_root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    removed_count += 1
                except OSError:
                    # Directory not empty or permission issue
                    pass

        return removed_count

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return Thumbnail.get_cache_directory_structure(str(self.cache_root))
