"""EXIF metadata model for photo search system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class EXIFData:
    """EXIF metadata extracted from image files."""

    file_id: int
    shot_dt: str | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens: str | None = None
    iso: int | None = None
    aperture: float | None = None
    shutter_speed: str | None = None
    focal_length: float | None = None
    gps_lat: float | None = None
    gps_lon: float | None = None
    orientation: int | None = None

    @classmethod
    def from_exif_dict(cls, file_id: int, exif_dict: dict[str, Any]) -> "EXIFData":
        """Create EXIFData from raw EXIF dictionary."""
        instance = cls(file_id=file_id)

        # Extract datetime
        datetime_original = exif_dict.get("DateTime") or exif_dict.get(
            "DateTimeOriginal"
        )
        if datetime_original:
            try:
                # Parse EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                dt = datetime.strptime(str(datetime_original), "%Y:%m:%d %H:%M:%S")
                instance.shot_dt = dt.isoformat()
            except (ValueError, TypeError):
                pass

        # Extract camera information
        instance.camera_make = cls._clean_string(exif_dict.get("Make"))
        instance.camera_model = cls._clean_string(exif_dict.get("Model"))
        instance.lens = cls._clean_string(
            exif_dict.get("LensModel") or exif_dict.get("LensSpecification")
        )

        # Extract exposure settings
        instance.iso = cls._safe_int(
            exif_dict.get("ISOSpeedRatings") or exif_dict.get("ISO")
        )
        instance.aperture = cls._safe_float(
            exif_dict.get("FNumber") or exif_dict.get("ApertureValue")
        )
        instance.focal_length = cls._safe_float(exif_dict.get("FocalLength"))

        # Extract shutter speed
        shutter_speed = exif_dict.get("ExposureTime") or exif_dict.get(
            "ShutterSpeedValue"
        )
        if shutter_speed:
            instance.shutter_speed = cls._format_shutter_speed(shutter_speed)

        # Extract GPS coordinates
        gps_info = exif_dict.get("GPSInfo", {})
        if gps_info:
            lat, lon = cls._parse_gps_coordinates(gps_info)
            instance.gps_lat = lat
            instance.gps_lon = lon

        # Extract orientation
        instance.orientation = cls._safe_int(exif_dict.get("Orientation"))

        return instance

    @classmethod
    def from_db_row(cls, row) -> "EXIFData":
        """Create EXIFData from database row."""
        return cls(
            file_id=row["file_id"],
            shot_dt=row["shot_dt"],
            camera_make=row["camera_make"],
            camera_model=row["camera_model"],
            lens=row["lens"],
            iso=row["iso"],
            aperture=row["aperture"],
            shutter_speed=row["shutter_speed"],
            focal_length=row["focal_length"],
            gps_lat=row["gps_lat"],
            gps_lon=row["gps_lon"],
            orientation=row["orientation"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "file_id": self.file_id,
            "shot_dt": self.shot_dt,
            "camera_make": self.camera_make,
            "camera_model": self.camera_model,
            "lens": self.lens,
            "iso": self.iso,
            "aperture": self.aperture,
            "shutter_speed": self.shutter_speed,
            "focal_length": self.focal_length,
            "gps_lat": self.gps_lat,
            "gps_lon": self.gps_lon,
            "orientation": self.orientation,
        }

    def validate(self) -> list[str]:
        """Validate EXIF data and return list of errors."""
        errors = []

        if self.file_id <= 0:
            errors.append("File ID must be positive")

        if self.shot_dt:
            try:
                datetime.fromisoformat(self.shot_dt)
            except ValueError:
                errors.append("Invalid shot datetime format")

        if self.iso is not None and (self.iso <= 0 or self.iso > 102400):
            errors.append("ISO value out of valid range")

        if self.aperture is not None and (self.aperture <= 0 or self.aperture > 64):
            errors.append("Aperture value out of valid range")

        if self.focal_length is not None and (
            self.focal_length <= 0 or self.focal_length > 2000
        ):
            errors.append("Focal length out of valid range")

        if self.gps_lat is not None and not (-90 <= self.gps_lat <= 90):
            errors.append("GPS latitude out of valid range")

        if self.gps_lon is not None and not (-180 <= self.gps_lon <= 180):
            errors.append("GPS longitude out of valid range")

        if self.orientation is not None and not (1 <= self.orientation <= 8):
            errors.append("Orientation value out of valid range")

        return errors

    def is_valid(self) -> bool:
        """Check if EXIF data is valid."""
        return len(self.validate()) == 0

    def has_location(self) -> bool:
        """Check if EXIF contains GPS coordinates."""
        return self.gps_lat is not None and self.gps_lon is not None

    def has_camera_info(self) -> bool:
        """Check if EXIF contains camera information."""
        return bool(self.camera_make or self.camera_model)

    def has_exposure_info(self) -> bool:
        """Check if EXIF contains exposure settings."""
        return any([self.iso, self.aperture, self.shutter_speed, self.focal_length])

    def get_camera_description(self) -> str:
        """Get formatted camera description."""
        parts = []
        if self.camera_make:
            parts.append(self.camera_make)
        if self.camera_model:
            parts.append(self.camera_model)
        return " ".join(parts) if parts else "Unknown Camera"

    def get_exposure_description(self) -> str:
        """Get formatted exposure description."""
        parts = []

        if self.aperture:
            parts.append(f"f/{self.aperture:.1f}")

        if self.shutter_speed:
            parts.append(self.shutter_speed)

        if self.iso:
            parts.append(f"ISO {self.iso}")

        if self.focal_length:
            parts.append(f"{self.focal_length:.0f}mm")

        return " | ".join(parts) if parts else ""

    def get_location_description(self) -> str:
        """Get formatted location description."""
        if not self.has_location():
            return ""

        return f"{self.gps_lat:.6f}, {self.gps_lon:.6f}"

    @staticmethod
    def _clean_string(value: Any) -> str | None:
        """Clean and validate string values."""
        if value is None:
            return None

        cleaned = str(value).strip()
        return cleaned if cleaned else None

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        """Safely convert value to integer."""
        if value is None:
            return None

        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """Safely convert value to float."""
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _format_shutter_speed(value: Any) -> str:
        """Format shutter speed for display."""
        try:
            speed = float(value)
            if speed >= 1:
                return f"{speed:.1f}s"
            return f"1/{int(1/speed)}"
        except (ValueError, TypeError, ZeroDivisionError):
            return str(value)

    @staticmethod
    def _parse_gps_coordinates(
        gps_info: dict[str, Any],
    ) -> tuple[float | None, float | None]:
        """Parse GPS coordinates from EXIF GPS info."""
        try:
            # Extract latitude
            lat_ref = gps_info.get("GPSLatitudeRef", "")
            lat_data = gps_info.get("GPSLatitude", [])

            if lat_data and len(lat_data) >= 3:
                lat = (
                    float(lat_data[0])
                    + float(lat_data[1]) / 60
                    + float(lat_data[2]) / 3600
                )
                if lat_ref.upper() == "S":
                    lat = -lat
            else:
                lat = None

            # Extract longitude
            lon_ref = gps_info.get("GPSLongitudeRef", "")
            lon_data = gps_info.get("GPSLongitude", [])

            if lon_data and len(lon_data) >= 3:
                lon = (
                    float(lon_data[0])
                    + float(lon_data[1]) / 60
                    + float(lon_data[2]) / 3600
                )
                if lon_ref.upper() == "W":
                    lon = -lon
            else:
                lon = None

            return lat, lon

        except (ValueError, TypeError, IndexError):
            return None, None


class EXIFFilter:
    """Helper class for building EXIF-based queries."""

    def __init__(self):
        self.conditions = []
        self.params = []

    def by_camera_make(self, make: str) -> "EXIFFilter":
        """Filter by camera manufacturer."""
        self.conditions.append("camera_make LIKE ?")
        self.params.append(f"%{make}%")
        return self

    def by_camera_model(self, model: str) -> "EXIFFilter":
        """Filter by camera model."""
        self.conditions.append("camera_model LIKE ?")
        self.params.append(f"%{model}%")
        return self

    def by_date_range(self, start_date: str, end_date: str) -> "EXIFFilter":
        """Filter by shot date range."""
        self.conditions.append("shot_dt BETWEEN ? AND ?")
        self.params.extend([start_date, end_date])
        return self

    def by_iso_range(self, min_iso: int, max_iso: int) -> "EXIFFilter":
        """Filter by ISO range."""
        self.conditions.append("iso BETWEEN ? AND ?")
        self.params.extend([min_iso, max_iso])
        return self

    def by_aperture_range(
        self, min_aperture: float, max_aperture: float
    ) -> "EXIFFilter":
        """Filter by aperture range."""
        self.conditions.append("aperture BETWEEN ? AND ?")
        self.params.extend([min_aperture, max_aperture])
        return self

    def by_focal_length_range(self, min_fl: float, max_fl: float) -> "EXIFFilter":
        """Filter by focal length range."""
        self.conditions.append("focal_length BETWEEN ? AND ?")
        self.params.extend([min_fl, max_fl])
        return self

    def has_gps(self) -> "EXIFFilter":
        """Filter to photos with GPS coordinates."""
        self.conditions.append("gps_lat IS NOT NULL AND gps_lon IS NOT NULL")
        return self

    def in_location_box(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> "EXIFFilter":
        """Filter by GPS bounding box."""
        min_lat, max_lat = min(lat1, lat2), max(lat1, lat2)
        min_lon, max_lon = min(lon1, lon2), max(lon1, lon2)

        self.conditions.append("gps_lat BETWEEN ? AND ? AND gps_lon BETWEEN ? AND ?")
        self.params.extend([min_lat, max_lat, min_lon, max_lon])
        return self

    def build_where_clause(self) -> tuple[str, list]:
        """Build WHERE clause and parameters."""
        if not self.conditions:
            return "", []

        where_clause = "WHERE " + " AND ".join(self.conditions)
        return where_clause, self.params
