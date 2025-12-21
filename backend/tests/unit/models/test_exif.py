"""Unit tests for EXIF models."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.models.exif import EXIFData, EXIFFilter


class TestEXIFDataModel:
    """Test EXIFData model functionality."""

    def test_exif_creation_with_minimal_data(self):
        """Test creating EXIFData with minimal required data."""
        exif = EXIFData(file_id=1)

        assert exif.file_id == 1
        assert exif.shot_dt is None
        assert exif.camera_make is None
        assert exif.camera_model is None
        assert exif.lens is None
        assert exif.iso is None
        assert exif.aperture is None
        assert exif.shutter_speed is None
        assert exif.focal_length is None
        assert exif.gps_lat is None
        assert exif.gps_lon is None
        assert exif.orientation is None

    def test_exif_creation_with_all_data(self):
        """Test creating EXIFData with all fields populated."""
        exif = EXIFData(
            file_id=1,
            shot_dt="2023-01-15T10:30:00",
            camera_make="Canon",
            camera_model="EOS R5",
            lens="RF 24-70mm F2.8",
            iso=800,
            aperture=2.8,
            shutter_speed="1/250",
            focal_length=50.0,
            gps_lat=37.7749,
            gps_lon=-122.4194,
            orientation=1,
        )

        assert exif.file_id == 1
        assert exif.shot_dt == "2023-01-15T10:30:00"
        assert exif.camera_make == "Canon"
        assert exif.camera_model == "EOS R5"
        assert exif.lens == "RF 24-70mm F2.8"
        assert exif.iso == 800
        assert exif.aperture == 2.8
        assert exif.shutter_speed == "1/250"
        assert exif.focal_length == 50.0
        assert exif.gps_lat == 37.7749
        assert exif.gps_lon == -122.4194
        assert exif.orientation == 1

    def test_from_exif_dict_datetime_original(self):
        """Test creating EXIFData from exif dict with DateTimeOriginal."""
        exif_dict = {"DateTimeOriginal": "2023:01:15 10:30:00"}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.file_id == 1
        assert exif.shot_dt == "2023-01-15T10:30:00"

    def test_from_exif_dict_datetime_fallback(self):
        """Test creating EXIFData with DateTime fallback."""
        exif_dict = {"DateTime": "2023:01:15 10:30:00"}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.shot_dt == "2023-01-15T10:30:00"

    def test_from_exif_dict_invalid_datetime(self):
        """Test creating EXIFData with invalid datetime."""
        exif_dict = {"DateTime": "invalid_date"}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.shot_dt is None

    def test_from_exif_dict_camera_info(self):
        """Test extracting camera information."""
        exif_dict = {
            "Make": "Nikon",
            "Model": "D850",
            "LensModel": "NIKKOR Z 24-70mm f/2.8 S",
        }

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.camera_make == "Nikon"
        assert exif.camera_model == "D850"
        assert exif.lens == "NIKKOR Z 24-70mm f/2.8 S"

    def test_from_exif_dict_lens_specification_fallback(self):
        """Test lens extraction with LensSpecification fallback."""
        exif_dict = {"LensSpecification": "24-70mm f/2.8"}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.lens == "24-70mm f/2.8"

    def test_from_exif_dict_exposure_settings(self):
        """Test extracting exposure settings."""
        exif_dict = {
            "ISOSpeedRatings": 1600,
            "FNumber": 4.0,
            "FocalLength": 85.0,
        }

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.iso == 1600
        assert exif.aperture == 4.0
        assert exif.focal_length == 85.0

    def test_from_exif_dict_iso_fallback(self):
        """Test ISO extraction with ISO key fallback."""
        exif_dict = {"ISO": 3200}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.iso == 3200

    def test_from_exif_dict_aperture_fallback(self):
        """Test aperture extraction with ApertureValue fallback."""
        exif_dict = {"ApertureValue": 5.6}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.aperture == 5.6

    def test_from_exif_dict_shutter_speed(self):
        """Test extracting shutter speed."""
        exif_dict = {"ExposureTime": 0.004}  # 1/250

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.shutter_speed == "1/250"

    def test_from_exif_dict_shutter_speed_fallback(self):
        """Test shutter speed with ShutterSpeedValue fallback."""
        exif_dict = {"ShutterSpeedValue": 0.5}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.shutter_speed == "1/2"

    def test_from_exif_dict_gps_coordinates(self):
        """Test extracting GPS coordinates."""
        exif_dict = {
            "GPSInfo": {
                "GPSLatitude": [37, 46, 29.64],
                "GPSLatitudeRef": "N",
                "GPSLongitude": [122, 25, 9.84],
                "GPSLongitudeRef": "W",
            }
        }

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.gps_lat is not None
        assert exif.gps_lon is not None
        assert abs(exif.gps_lat - 37.7749) < 0.001
        assert abs(exif.gps_lon - (-122.4194)) < 0.001

    def test_from_exif_dict_gps_south_west(self):
        """Test GPS coordinates with South and West references."""
        exif_dict = {
            "GPSInfo": {
                "GPSLatitude": [33, 51, 0],
                "GPSLatitudeRef": "S",
                "GPSLongitude": [151, 12, 0],
                "GPSLongitudeRef": "W",
            }
        }

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.gps_lat < 0  # South
        assert exif.gps_lon < 0  # West

    def test_from_exif_dict_orientation(self):
        """Test extracting orientation."""
        exif_dict = {"Orientation": 6}

        exif = EXIFData.from_exif_dict(file_id=1, exif_dict=exif_dict)

        assert exif.orientation == 6

    def test_from_db_row(self):
        """Test creating EXIFData from database row."""
        row = {
            "file_id": 1,
            "shot_dt": "2023-01-15T10:30:00",
            "camera_make": "Sony",
            "camera_model": "A7IV",
            "lens": "FE 24-70mm F2.8 GM",
            "iso": 800,
            "aperture": 2.8,
            "shutter_speed": "1/250",
            "focal_length": 50.0,
            "gps_lat": 37.7749,
            "gps_lon": -122.4194,
            "orientation": 1,
        }

        exif = EXIFData.from_db_row(row)

        assert exif.file_id == 1
        assert exif.shot_dt == "2023-01-15T10:30:00"
        assert exif.camera_make == "Sony"
        assert exif.camera_model == "A7IV"
        assert exif.lens == "FE 24-70mm F2.8 GM"
        assert exif.iso == 800
        assert exif.aperture == 2.8
        assert exif.shutter_speed == "1/250"
        assert exif.focal_length == 50.0
        assert exif.gps_lat == 37.7749
        assert exif.gps_lon == -122.4194
        assert exif.orientation == 1

    def test_to_dict(self):
        """Test converting EXIFData to dictionary."""
        exif = EXIFData(
            file_id=1,
            shot_dt="2023-01-15T10:30:00",
            camera_make="Fujifilm",
            camera_model="X-T5",
            iso=400,
            aperture=1.4,
            focal_length=56.0,
        )

        result = exif.to_dict()

        assert result["file_id"] == 1
        assert result["shot_dt"] == "2023-01-15T10:30:00"
        assert result["camera_make"] == "Fujifilm"
        assert result["camera_model"] == "X-T5"
        assert result["iso"] == 400
        assert result["aperture"] == 1.4
        assert result["focal_length"] == 56.0

    def test_validate_valid_exif(self):
        """Test validation of valid EXIFData."""
        exif = EXIFData(
            file_id=1,
            shot_dt="2023-01-15T10:30:00",
            iso=800,
            aperture=2.8,
            focal_length=50.0,
            gps_lat=45.0,
            gps_lon=-120.0,
            orientation=1,
        )

        errors = exif.validate()

        assert len(errors) == 0

    def test_validate_negative_file_id(self):
        """Test validation catches non-positive file_id."""
        exif = EXIFData(file_id=0)

        errors = exif.validate()

        assert any("File ID must be positive" in e for e in errors)

    def test_validate_invalid_shot_dt(self):
        """Test validation catches invalid datetime format."""
        exif = EXIFData(file_id=1, shot_dt="invalid_date")

        errors = exif.validate()

        assert any("Invalid shot datetime format" in e for e in errors)

    def test_validate_invalid_iso_low(self):
        """Test validation catches ISO too low."""
        exif = EXIFData(file_id=1, iso=0)

        errors = exif.validate()

        assert any("ISO value out of valid range" in e for e in errors)

    def test_validate_invalid_iso_high(self):
        """Test validation catches ISO too high."""
        exif = EXIFData(file_id=1, iso=200000)

        errors = exif.validate()

        assert any("ISO value out of valid range" in e for e in errors)

    def test_validate_invalid_aperture_low(self):
        """Test validation catches aperture too low."""
        exif = EXIFData(file_id=1, aperture=0)

        errors = exif.validate()

        assert any("Aperture value out of valid range" in e for e in errors)

    def test_validate_invalid_aperture_high(self):
        """Test validation catches aperture too high."""
        exif = EXIFData(file_id=1, aperture=100)

        errors = exif.validate()

        assert any("Aperture value out of valid range" in e for e in errors)

    def test_validate_invalid_focal_length_low(self):
        """Test validation catches focal length too low."""
        exif = EXIFData(file_id=1, focal_length=0)

        errors = exif.validate()

        assert any("Focal length out of valid range" in e for e in errors)

    def test_validate_invalid_focal_length_high(self):
        """Test validation catches focal length too high."""
        exif = EXIFData(file_id=1, focal_length=3000)

        errors = exif.validate()

        assert any("Focal length out of valid range" in e for e in errors)

    def test_validate_invalid_gps_lat_low(self):
        """Test validation catches latitude too low."""
        exif = EXIFData(file_id=1, gps_lat=-100)

        errors = exif.validate()

        assert any("GPS latitude out of valid range" in e for e in errors)

    def test_validate_invalid_gps_lat_high(self):
        """Test validation catches latitude too high."""
        exif = EXIFData(file_id=1, gps_lat=100)

        errors = exif.validate()

        assert any("GPS latitude out of valid range" in e for e in errors)

    def test_validate_invalid_gps_lon_low(self):
        """Test validation catches longitude too low."""
        exif = EXIFData(file_id=1, gps_lon=-200)

        errors = exif.validate()

        assert any("GPS longitude out of valid range" in e for e in errors)

    def test_validate_invalid_gps_lon_high(self):
        """Test validation catches longitude too high."""
        exif = EXIFData(file_id=1, gps_lon=200)

        errors = exif.validate()

        assert any("GPS longitude out of valid range" in e for e in errors)

    def test_validate_invalid_orientation(self):
        """Test validation catches invalid orientation."""
        exif = EXIFData(file_id=1, orientation=10)

        errors = exif.validate()

        assert any("Orientation value out of valid range" in e for e in errors)

    def test_is_valid(self):
        """Test is_valid method."""
        valid_exif = EXIFData(file_id=1, iso=800)
        assert valid_exif.is_valid() is True

        invalid_exif = EXIFData(file_id=0)
        assert invalid_exif.is_valid() is False

    def test_has_location_true(self):
        """Test has_location with GPS coordinates."""
        exif = EXIFData(file_id=1, gps_lat=37.7749, gps_lon=-122.4194)

        assert exif.has_location() is True

    def test_has_location_false_no_coords(self):
        """Test has_location without GPS coordinates."""
        exif = EXIFData(file_id=1)

        assert exif.has_location() is False

    def test_has_location_false_partial_coords(self):
        """Test has_location with only latitude."""
        exif = EXIFData(file_id=1, gps_lat=37.7749)

        assert exif.has_location() is False

    def test_has_camera_info_true(self):
        """Test has_camera_info with camera data."""
        exif = EXIFData(file_id=1, camera_make="Canon")

        assert exif.has_camera_info() is True

    def test_has_camera_info_false(self):
        """Test has_camera_info without camera data."""
        exif = EXIFData(file_id=1)

        assert exif.has_camera_info() is False

    def test_has_exposure_info_true(self):
        """Test has_exposure_info with exposure data."""
        exif = EXIFData(file_id=1, iso=800)

        assert exif.has_exposure_info() is True

    def test_has_exposure_info_false(self):
        """Test has_exposure_info without exposure data."""
        exif = EXIFData(file_id=1)

        assert exif.has_exposure_info() is False

    def test_get_camera_description_full(self):
        """Test getting camera description with both make and model."""
        exif = EXIFData(file_id=1, camera_make="Nikon", camera_model="Z9")

        description = exif.get_camera_description()

        assert description == "Nikon Z9"

    def test_get_camera_description_make_only(self):
        """Test getting camera description with only make."""
        exif = EXIFData(file_id=1, camera_make="Panasonic")

        description = exif.get_camera_description()

        assert description == "Panasonic"

    def test_get_camera_description_model_only(self):
        """Test getting camera description with only model."""
        exif = EXIFData(file_id=1, camera_model="GH6")

        description = exif.get_camera_description()

        assert description == "GH6"

    def test_get_camera_description_none(self):
        """Test getting camera description without data."""
        exif = EXIFData(file_id=1)

        description = exif.get_camera_description()

        assert description == "Unknown Camera"

    def test_get_exposure_description_full(self):
        """Test getting exposure description with all data."""
        exif = EXIFData(
            file_id=1,
            aperture=2.8,
            shutter_speed="1/250",
            iso=800,
            focal_length=50.0,
        )

        description = exif.get_exposure_description()

        assert "f/2.8" in description
        assert "1/250" in description
        assert "ISO 800" in description
        assert "50mm" in description

    def test_get_exposure_description_partial(self):
        """Test getting exposure description with partial data."""
        exif = EXIFData(file_id=1, aperture=4.0, iso=400)

        description = exif.get_exposure_description()

        assert "f/4.0" in description
        assert "ISO 400" in description

    def test_get_exposure_description_empty(self):
        """Test getting exposure description without data."""
        exif = EXIFData(file_id=1)

        description = exif.get_exposure_description()

        assert description == ""

    def test_get_location_description(self):
        """Test getting location description."""
        exif = EXIFData(file_id=1, gps_lat=37.7749, gps_lon=-122.4194)

        description = exif.get_location_description()

        assert "37.7749" in description
        assert "-122.4194" in description

    def test_get_location_description_no_location(self):
        """Test getting location description without GPS data."""
        exif = EXIFData(file_id=1)

        description = exif.get_location_description()

        assert description == ""

    def test_clean_string_valid(self):
        """Test cleaning valid string."""
        result = EXIFData._clean_string("  Canon  ")

        assert result == "Canon"

    def test_clean_string_empty(self):
        """Test cleaning empty string."""
        result = EXIFData._clean_string("   ")

        assert result is None

    def test_clean_string_none(self):
        """Test cleaning None value."""
        result = EXIFData._clean_string(None)

        assert result is None

    def test_safe_int_valid(self):
        """Test safe int conversion."""
        assert EXIFData._safe_int(800) == 800
        assert EXIFData._safe_int("800") == 800
        assert EXIFData._safe_int(800.5) == 800

    def test_safe_int_none(self):
        """Test safe int conversion with None."""
        assert EXIFData._safe_int(None) is None

    def test_safe_int_invalid(self):
        """Test safe int conversion with invalid value."""
        assert EXIFData._safe_int("invalid") is None

    def test_safe_float_valid(self):
        """Test safe float conversion."""
        assert EXIFData._safe_float(2.8) == 2.8
        assert EXIFData._safe_float("2.8") == 2.8
        assert EXIFData._safe_float(3) == 3.0

    def test_safe_float_none(self):
        """Test safe float conversion with None."""
        assert EXIFData._safe_float(None) is None

    def test_safe_float_invalid(self):
        """Test safe float conversion with invalid value."""
        assert EXIFData._safe_float("invalid") is None

    def test_format_shutter_speed_fast(self):
        """Test formatting fast shutter speed."""
        result = EXIFData._format_shutter_speed(0.004)

        assert result == "1/250"

    def test_format_shutter_speed_slow(self):
        """Test formatting slow shutter speed."""
        result = EXIFData._format_shutter_speed(2.5)

        assert result == "2.5s"

    def test_format_shutter_speed_one_second(self):
        """Test formatting one second shutter speed."""
        result = EXIFData._format_shutter_speed(1.0)

        assert result == "1.0s"

    def test_format_shutter_speed_invalid(self):
        """Test formatting invalid shutter speed."""
        result = EXIFData._format_shutter_speed("invalid")

        assert result == "invalid"

    def test_parse_gps_coordinates_valid(self):
        """Test parsing valid GPS coordinates."""
        gps_info = {
            "GPSLatitude": [37, 46, 29.64],
            "GPSLatitudeRef": "N",
            "GPSLongitude": [122, 25, 9.84],
            "GPSLongitudeRef": "W",
        }

        lat, lon = EXIFData._parse_gps_coordinates(gps_info)

        assert lat is not None
        assert lon is not None
        assert abs(lat - 37.7749) < 0.001
        assert abs(lon - (-122.4194)) < 0.001

    def test_parse_gps_coordinates_incomplete(self):
        """Test parsing incomplete GPS coordinates."""
        gps_info = {
            "GPSLatitude": [37, 46],  # Incomplete
            "GPSLatitudeRef": "N",
        }

        lat, lon = EXIFData._parse_gps_coordinates(gps_info)

        assert lat is None
        assert lon is None

    def test_parse_gps_coordinates_invalid(self):
        """Test parsing invalid GPS coordinates."""
        gps_info = {
            "GPSLatitude": ["invalid", "data", "here"],
            "GPSLatitudeRef": "N",
        }

        lat, lon = EXIFData._parse_gps_coordinates(gps_info)

        assert lat is None
        assert lon is None

    def test_parse_gps_coordinates_empty(self):
        """Test parsing empty GPS info."""
        lat, lon = EXIFData._parse_gps_coordinates({})

        assert lat is None
        assert lon is None


class TestEXIFFilter:
    """Test EXIFFilter functionality."""

    def test_exif_filter_creation(self):
        """Test creating EXIFFilter."""
        f = EXIFFilter()

        assert f.conditions == []
        assert f.params == []

    def test_by_camera_make(self):
        """Test filtering by camera make."""
        f = EXIFFilter()
        f.by_camera_make("Canon")

        assert "camera_make LIKE ?" in f.conditions
        assert "%Canon%" in f.params

    def test_by_camera_model(self):
        """Test filtering by camera model."""
        f = EXIFFilter()
        f.by_camera_model("R5")

        assert "camera_model LIKE ?" in f.conditions
        assert "%R5%" in f.params

    def test_by_date_range(self):
        """Test filtering by date range."""
        f = EXIFFilter()
        f.by_date_range("2023-01-01", "2023-12-31")

        assert "shot_dt BETWEEN ? AND ?" in f.conditions
        assert "2023-01-01" in f.params
        assert "2023-12-31" in f.params

    def test_by_iso_range(self):
        """Test filtering by ISO range."""
        f = EXIFFilter()
        f.by_iso_range(400, 1600)

        assert "iso BETWEEN ? AND ?" in f.conditions
        assert 400 in f.params
        assert 1600 in f.params

    def test_by_aperture_range(self):
        """Test filtering by aperture range."""
        f = EXIFFilter()
        f.by_aperture_range(1.4, 4.0)

        assert "aperture BETWEEN ? AND ?" in f.conditions
        assert 1.4 in f.params
        assert 4.0 in f.params

    def test_by_focal_length_range(self):
        """Test filtering by focal length range."""
        f = EXIFFilter()
        f.by_focal_length_range(24.0, 70.0)

        assert "focal_length BETWEEN ? AND ?" in f.conditions
        assert 24.0 in f.params
        assert 70.0 in f.params

    def test_has_gps(self):
        """Test filtering for photos with GPS."""
        f = EXIFFilter()
        f.has_gps()

        assert "gps_lat IS NOT NULL AND gps_lon IS NOT NULL" in f.conditions

    def test_in_location_box(self):
        """Test filtering by GPS bounding box."""
        f = EXIFFilter()
        f.in_location_box(37.0, -123.0, 38.0, -122.0)

        assert "gps_lat BETWEEN ? AND ?" in f.conditions[0]
        assert "gps_lon BETWEEN ? AND ?" in f.conditions[0]
        assert len(f.params) == 4

    def test_in_location_box_inverted_coords(self):
        """Test location box with inverted coordinates."""
        f = EXIFFilter()
        f.in_location_box(38.0, -122.0, 37.0, -123.0)  # Inverted

        # Should normalize to min/max
        assert 37.0 in f.params  # min lat
        assert 38.0 in f.params  # max lat
        assert -123.0 in f.params  # min lon
        assert -122.0 in f.params  # max lon

    def test_build_where_clause_empty(self):
        """Test building WHERE clause with no conditions."""
        f = EXIFFilter()

        where_clause, params = f.build_where_clause()

        assert where_clause == ""
        assert params == []

    def test_build_where_clause_single_condition(self):
        """Test building WHERE clause with single condition."""
        f = EXIFFilter()
        f.by_camera_make("Canon")

        where_clause, params = f.build_where_clause()

        assert where_clause.startswith("WHERE ")
        assert "camera_make LIKE ?" in where_clause
        assert params == ["%Canon%"]

    def test_build_where_clause_multiple_conditions(self):
        """Test building WHERE clause with multiple conditions."""
        f = EXIFFilter()
        f.by_camera_make("Canon")
        f.by_iso_range(400, 1600)
        f.has_gps()

        where_clause, params = f.build_where_clause()

        assert where_clause.startswith("WHERE ")
        assert " AND " in where_clause
        assert len(f.conditions) == 3
        assert len(params) == 3  # Canon, min_iso, max_iso

    def test_filter_chaining(self):
        """Test method chaining for filters."""
        f = EXIFFilter()
        result = f.by_camera_make("Canon").by_iso_range(400, 1600).has_gps()

        assert result is f  # Should return self
        assert len(f.conditions) == 3
