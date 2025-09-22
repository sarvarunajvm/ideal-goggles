"""Photo model for the photo search system."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Photo:
    """Core photo entity with metadata and processing state."""

    id: int | None = None
    path: str = ""
    folder: str = ""
    filename: str = ""
    ext: str = ""
    size: int = 0
    created_ts: float = 0.0
    modified_ts: float = 0.0
    sha1: str = ""
    phash: str | None = None
    indexed_at: float | None = None
    index_version: int = 1

    @classmethod
    def from_file_path(cls, file_path: str) -> "Photo":
        """Create Photo instance from file path."""
        path_obj = Path(file_path)

        if not path_obj.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        stat = path_obj.stat()

        return cls(
            path=str(path_obj.absolute()),
            folder=str(path_obj.parent),
            filename=path_obj.name,
            ext=path_obj.suffix.lower(),
            size=stat.st_size,
            created_ts=stat.st_ctime,
            modified_ts=stat.st_mtime,
            sha1=cls._calculate_sha1(file_path),
        )

    @classmethod
    def from_db_row(cls, row) -> "Photo":
        """Create Photo instance from database row."""
        return cls(
            id=row["id"],
            path=row["path"],
            folder=row["folder"],
            filename=row["filename"],
            ext=row["ext"],
            size=row["size"],
            created_ts=row["created_ts"],
            modified_ts=row["modified_ts"],
            sha1=row["sha1"],
            phash=row["phash"],
            indexed_at=row["indexed_at"],
            index_version=row["index_version"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "path": self.path,
            "folder": self.folder,
            "filename": self.filename,
            "ext": self.ext,
            "size": self.size,
            "created_ts": self.created_ts,
            "modified_ts": self.modified_ts,
            "sha1": self.sha1,
            "phash": self.phash,
            "indexed_at": self.indexed_at,
            "index_version": self.index_version,
        }

    def validate(self) -> list[str]:
        """Validate photo data and return list of errors."""
        errors = []

        if not self.path or not Path(self.path).is_absolute():
            errors.append("Path must be absolute")

        if self.ext not in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
            errors.append(f"Unsupported file extension: {self.ext}")

        if self.size <= 0:
            errors.append("File size must be positive")

        if len(self.sha1) != 40:
            errors.append("SHA1 hash must be 40 characters")

        if self.phash and len(self.phash) != 16:
            errors.append("Perceptual hash must be 16 characters")

        return errors

    def is_valid(self) -> bool:
        """Check if photo data is valid."""
        return len(self.validate()) == 0

    def file_exists(self) -> bool:
        """Check if the photo file still exists."""
        return Path(self.path).exists()

    def needs_reprocessing(self) -> bool:
        """Check if photo needs reprocessing based on modification time."""
        if not self.indexed_at:
            return True

        if not self.file_exists():
            return False

        return self.modified_ts > self.indexed_at

    def mark_indexed(self):
        """Mark photo as indexed with current timestamp."""
        self.indexed_at = datetime.now().timestamp()

    @staticmethod
    def _calculate_sha1(file_path: str) -> str:
        """Calculate SHA1 hash of file."""
        sha1_hash = hashlib.sha1()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha1_hash.update(chunk)
        except Exception:
            return ""

        return sha1_hash.hexdigest()

    def calculate_perceptual_hash(self) -> str | None:
        """Calculate perceptual hash for duplicate detection."""
        try:
            import imagehash
            from PIL import Image

            with Image.open(self.path) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Calculate average hash (simple but effective)
                hash_value = imagehash.average_hash(img, hash_size=8)
                return str(hash_value)

        except Exception:
            # If we can't calculate perceptual hash, it's not critical
            return None

    def get_display_name(self) -> str:
        """Get display name for UI."""
        return self.filename

    def get_relative_folder(self, root_path: str) -> str:
        """Get folder path relative to root."""
        try:
            folder_path = Path(self.folder)
            root_path_obj = Path(root_path)
            return str(folder_path.relative_to(root_path_obj))
        except ValueError:
            return self.folder


class PhotoState:
    """Photo processing state constants."""

    DISCOVERED = "discovered"
    PROCESSING = "processing"
    INDEXED = "indexed"
    REPROCESSING = "reprocessing"
    DELETED = "deleted"
    ERROR = "error"


class PhotoFilter:
    """Helper class for building photo queries."""

    def __init__(self):
        self.conditions = []
        self.params = []

    def by_folder(self, folder_path: str) -> "PhotoFilter":
        """Filter by folder path."""
        self.conditions.append("folder LIKE ?")
        self.params.append(f"{folder_path}%")
        return self

    def by_extension(self, extensions: list[str]) -> "PhotoFilter":
        """Filter by file extensions."""
        placeholders = ",".join("?" * len(extensions))
        self.conditions.append(f"ext IN ({placeholders})")
        self.params.extend(extensions)
        return self

    def by_date_range(self, start_ts: float, end_ts: float) -> "PhotoFilter":
        """Filter by creation date range."""
        self.conditions.append("created_ts BETWEEN ? AND ?")
        self.params.extend([start_ts, end_ts])
        return self

    def by_size_range(self, min_size: int, max_size: int) -> "PhotoFilter":
        """Filter by file size range."""
        self.conditions.append("size BETWEEN ? AND ?")
        self.params.extend([min_size, max_size])
        return self

    def indexed_only(self) -> "PhotoFilter":
        """Filter to only indexed photos."""
        self.conditions.append("indexed_at IS NOT NULL")
        return self

    def needs_processing(self) -> "PhotoFilter":
        """Filter to photos that need processing."""
        self.conditions.append("(indexed_at IS NULL OR modified_ts > indexed_at)")
        return self

    def build_where_clause(self) -> tuple[str, list]:
        """Build WHERE clause and parameters."""
        if not self.conditions:
            return "", []

        where_clause = "WHERE " + " AND ".join(self.conditions)
        return where_clause, self.params
