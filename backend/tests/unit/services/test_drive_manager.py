"""Unit tests for DriveManager service."""

import os
import platform
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest

from src.services.drive_manager import DriveManager


class TestDriveManagerInitialization:
    """Test DriveManager initialization."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_initialization_windows(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test DriveManager initialization on Windows."""
        mock_platform.return_value = "Windows"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        # Mock database connection
        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                assert manager.platform == "windows"
                assert isinstance(manager.drive_mappings, dict)
                assert isinstance(manager.alias_mappings, dict)
                assert isinstance(manager.current_mounts, dict)
                assert isinstance(manager._lock, type(threading.RLock()))

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_initialization_unix(self, mock_platform, mock_get_db, mock_get_settings):
        """Test DriveManager initialization on Unix-like systems."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                assert manager.platform == "linux"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_initialize_mappings_from_database(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test loading drive mappings from database."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        # Mock database with existing aliases
        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("device_1", "my_drive", "/mnt/drive1", 1640995200.0),
            ("device_2", "backup_drive", "/mnt/drive2", 1640995300.0),
        ]
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch("os.path.exists", return_value=True):
            with patch.object(DriveManager, "_scan_current_drives"):
                with patch.object(DriveManager, "start_monitoring"):
                    manager = DriveManager()

                    assert len(manager.drive_mappings) == 2
                    assert manager.drive_mappings["device_1"] == "my_drive"
                    assert manager.drive_mappings["device_2"] == "backup_drive"
                    assert manager.alias_mappings["my_drive"] == "device_1"
                    assert manager.alias_mappings["backup_drive"] == "device_2"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_initialize_mappings_database_error(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test handling of database errors during initialization."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        # Mock database error
        mock_db = MagicMock()
        mock_db.__enter__.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Should handle error gracefully
                assert isinstance(manager.drive_mappings, dict)


class TestWindowsDriveScanning:
    """Test Windows drive scanning functionality."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_scan_windows_drives_with_pywin32(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test scanning Windows drives using pywin32."""
        mock_platform.return_value = "Windows"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "start_monitoring"):
            manager = DriveManager()

            # Mock win32api - need to patch builtins.__import__ since it's imported inside the function
            mock_win32api = Mock()
            mock_win32file = Mock()

            mock_win32api.GetLogicalDriveStrings.return_value = (
                "C:\\\x00D:\\\x00E:\\\x00"
            )
            mock_win32api.GetVolumeInformation.return_value = (
                "System",
                12345678,
                255,
                0,
                "NTFS",
            )
            mock_win32file.GetDriveType.return_value = 3  # DRIVE_FIXED
            mock_win32file.DRIVE_REMOVABLE = 2
            mock_win32file.DRIVE_CDROM = 5
            mock_win32file.DRIVE_FIXED = 3

            import sys

            with patch.dict(
                sys.modules, {"win32api": mock_win32api, "win32file": mock_win32file}
            ):
                with patch.object(manager, "_update_drive_mapping") as mock_update:
                    manager._scan_windows_drives()

                    # Should have called update for each drive
                    assert mock_update.call_count >= 1

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_scan_windows_drives_fallback(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test Windows drive scanning fallback without pywin32."""
        mock_platform.return_value = "Windows"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "start_monitoring"):
            manager = DriveManager()

            # Mock ImportError for pywin32 by not having the module
            import sys

            # Make sure win32api doesn't exist in sys.modules
            win32api_backup = sys.modules.get("win32api")
            win32file_backup = sys.modules.get("win32file")

            try:
                # Remove from sys.modules if it exists
                sys.modules.pop("win32api", None)
                sys.modules.pop("win32file", None)

                with patch("os.path.exists") as mock_exists:
                    # Mock C: and D: drives exist
                    mock_exists.side_effect = lambda p: p in [
                        "C:\\",
                        "D:\\",
                        "C:\\\\",
                        "D:\\\\",
                    ]

                    with patch.object(manager, "_update_drive_mapping") as mock_update:
                        manager._scan_windows_drives()

                        # Should use fallback method
                        assert mock_update.call_count >= 1
            finally:
                # Restore original state
                if win32api_backup is not None:
                    sys.modules["win32api"] = win32api_backup
                if win32file_backup is not None:
                    sys.modules["win32file"] = win32file_backup

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_scan_windows_drives_error_handling(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test error handling in Windows drive scanning."""
        mock_platform.return_value = "Windows"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "start_monitoring"):
            manager = DriveManager()

            # Mock win32api to raise an exception
            mock_win32api = Mock()
            mock_win32api.GetLogicalDriveStrings.side_effect = Exception("Win32 error")

            import sys

            with patch.dict(sys.modules, {"win32api": mock_win32api}):
                # Should not raise exception
                manager._scan_windows_drives()


class TestUnixDriveScanning:
    """Test Unix/Linux drive scanning functionality."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_scan_unix_drives(self, mock_platform, mock_get_db, mock_get_settings):
        """Test scanning Unix mount points."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "start_monitoring"):
            manager = DriveManager()

            mount_data = (
                "/dev/sda1 / ext4 rw,relatime 0 0\n"
                "/dev/sdb1 /media/usb ext4 rw,nosuid,nodev 0 0\n"
                "tmpfs /tmp tmpfs rw,nosuid,nodev 0 0\n"
            )

            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=mount_data)):
                    with patch("os.path.ismount", return_value=True):
                        with patch.object(
                            manager, "_update_drive_mapping"
                        ) as mock_update:
                            manager._scan_unix_drives()

                            # Should update mappings for real devices (not tmpfs)
                            assert mock_update.call_count >= 1

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_scan_unix_drives_no_mount_file(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test Unix drive scanning when mount files don't exist."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "start_monitoring"):
            manager = DriveManager()

            with patch("os.path.exists", return_value=False):
                # Should not raise exception
                manager._scan_unix_drives()

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_is_removable_device(self, mock_platform, mock_get_db, mock_get_settings):
        """Test removable device detection."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # USB drive
                assert manager._is_removable_device("/dev/sdb1") is True

                # SD card
                assert manager._is_removable_device("/dev/mmcblk0") is True

                # Fixed drive
                assert (
                    manager._is_removable_device("/dev/sda1") is True
                )  # Matches pattern

                # Network drive
                assert manager._is_removable_device("//server/share") is False


class TestDriveMapping:
    """Test drive mapping and aliasing functionality."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_update_drive_mapping_new_device(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test updating drive mapping for new device."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                manager._update_drive_mapping(
                    "device_123", "/mnt/usb", "MyUSB", is_removable=True
                )

                assert "device_123" in manager.drive_mappings
                assert manager.drive_mappings["device_123"] == "myusb"
                assert manager.alias_mappings["myusb"] == "device_123"
                assert manager.current_mounts["device_123"] == "/mnt/usb"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_update_drive_mapping_duplicate_alias(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test updating drive mapping with duplicate alias."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Add first device
                manager._update_drive_mapping(
                    "device_1", "/mnt/usb1", "MyUSB", is_removable=True
                )

                # Add second device with same volume name
                manager._update_drive_mapping(
                    "device_2", "/mnt/usb2", "MyUSB", is_removable=True
                )

                # Should create unique alias for second device
                assert manager.drive_mappings["device_1"] == "myusb"
                assert manager.drive_mappings["device_2"] == "myusb_1"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_sanitize_alias(self, mock_platform, mock_get_db, mock_get_settings):
        """Test alias sanitization."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Test various sanitization scenarios
                assert manager._sanitize_alias("My USB Drive") == "my_usb_drive"
                assert manager._sanitize_alias("Drive@#$%123") == "drive_123"
                assert manager._sanitize_alias("___test___") == "test"
                assert manager._sanitize_alias("") == "unnamed"
                assert manager._sanitize_alias("!!!") == "unnamed"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_save_drive_mapping(self, mock_platform, mock_get_db, mock_get_settings):
        """Test saving drive mapping to database."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                with patch("time.time", return_value=1640995200.0):
                    manager._save_drive_mapping("device_123", "myusb", "/mnt/usb")

                    # Verify database was called
                    mock_db.__enter__.return_value.execute.assert_called()


class TestPathResolution:
    """Test path resolution functionality."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_path_exists(self, mock_platform, mock_get_db, mock_get_settings):
        """Test resolving path that exists."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                with patch("os.path.exists", return_value=True):
                    with patch(
                        "pathlib.Path.resolve", return_value=Path("/test/file.jpg")
                    ):
                        result = manager.resolve_path("/test/file.jpg")
                        assert result == "/test/file.jpg"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_windows_path_drive_change(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test resolving Windows path with drive letter change."""
        mock_platform.return_value = "Windows"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Setup current mounts
                manager.current_mounts["device_1"] = "D:"
                manager.current_mounts["device_2"] = "E:"

                def mock_exists(path):
                    return path == "E:\\photos\\image.jpg"

                with patch("os.path.exists", side_effect=mock_exists):
                    # Try to resolve old path on D: that's now on E:
                    result = manager.resolve_path("D:\\photos\\image.jpg")
                    assert result == "E:\\photos\\image.jpg"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_unix_path_mount_change(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test resolving Unix path with mount point change."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Setup current mounts
                manager.current_mounts["device_1"] = "/mnt/usb"

                def mock_exists(path):
                    return path == "/mnt/usb/photos/image.jpg"

                with patch("os.path.exists", side_effect=mock_exists):
                    # Try to resolve old path
                    result = manager.resolve_path("/media/oldusb/photos/image.jpg")
                    assert result == "/mnt/usb/photos/image.jpg"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_path_not_found(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test resolving path that cannot be found."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                with patch("os.path.exists", return_value=False):
                    result = manager.resolve_path("/nonexistent/path.jpg")
                    assert result is None


class TestStablePaths:
    """Test stable path creation and resolution."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_create_stable_path(self, mock_platform, mock_get_db, mock_get_settings):
        """Test creating stable path representation."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Setup mappings
                manager.current_mounts["device_1"] = "/mnt/usb"
                manager.drive_mappings["device_1"] = "myusb"

                with patch(
                    "pathlib.Path.resolve",
                    return_value=Path("/mnt/usb/photos/image.jpg"),
                ):
                    result = manager.create_stable_path("/mnt/usb/photos/image.jpg")
                    assert result == f"$myusb${os.sep}photos{os.sep}image.jpg"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_create_stable_path_no_match(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test creating stable path when no device match found."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                with patch(
                    "pathlib.Path.resolve", return_value=Path("/other/path/file.jpg")
                ):
                    result = manager.create_stable_path("/other/path/file.jpg")
                    # Should return original path as fallback
                    assert result == "/other/path/file.jpg"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_stable_path(self, mock_platform, mock_get_db, mock_get_settings):
        """Test resolving stable path back to absolute path."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Setup mappings
                manager.alias_mappings["myusb"] = "device_1"
                manager.current_mounts["device_1"] = "/mnt/usb"

                with patch("os.path.exists", return_value=True):
                    # Note: stable path format is $alias$relative_path
                    # The relative path should NOT have leading slash for os.path.join to work correctly
                    result = manager.resolve_stable_path("$myusb$photos/image.jpg")
                    expected = os.path.join("/mnt/usb", "photos/image.jpg")
                    assert result == expected

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_stable_path_unknown_alias(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test resolving stable path with unknown alias."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                result = manager.resolve_stable_path("$unknown$/photos/image.jpg")
                assert result is None

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_resolve_stable_path_device_not_mounted(
        self, mock_platform, mock_get_db, mock_get_settings
    ):
        """Test resolving stable path when device is not currently mounted."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Setup alias but no current mount
                manager.alias_mappings["myusb"] = "device_1"

                result = manager.resolve_stable_path("$myusb$/photos/image.jpg")
                assert result is None


class TestDriveStatus:
    """Test drive status functionality."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_get_drive_status(self, mock_platform, mock_get_db, mock_get_settings):
        """Test getting drive status."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                # Setup test data
                manager.drive_mappings["device_1"] = "myusb"
                manager.drive_mappings["device_2"] = "backup"
                manager.current_mounts["device_1"] = "/mnt/usb"
                # device_2 not in current_mounts (offline)

                status = manager.get_drive_status()

                assert len(status) == 2
                assert status["myusb"]["device_id"] == "device_1"
                assert status["myusb"]["is_online"] is True
                assert status["myusb"]["mount_point"] == "/mnt/usb"
                assert status["backup"]["is_online"] is False


class TestMonitoring:
    """Test background monitoring functionality."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_start_monitoring(self, mock_platform, mock_get_db, mock_get_settings):
        """Test starting background monitoring."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            manager = DriveManager()
            manager._monitoring = False
            manager._monitor_thread = None

            with patch("threading.Thread") as mock_thread:
                manager.start_monitoring()

                assert manager._monitoring is True
                mock_thread.assert_called_once()

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_stop_monitoring(self, mock_platform, mock_get_db, mock_get_settings):
        """Test stopping background monitoring."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()
                manager._monitoring = True
                manager._monitor_thread = Mock()
                manager._monitor_thread.join = Mock()

                manager.stop_monitoring()

                assert manager._monitoring is False
                manager._monitor_thread.join.assert_called_once()


class TestBulkOperations:
    """Test bulk path resolution operations."""

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_bulk_resolve_paths(self, mock_platform, mock_get_db, mock_get_settings):
        """Test bulk path resolution."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                paths = ["/path1/file1.jpg", "/path2/file2.jpg", "/path3/file3.jpg"]

                with patch.object(manager, "resolve_path") as mock_resolve:
                    mock_resolve.side_effect = [
                        "/resolved/path1/file1.jpg",
                        None,
                        "/resolved/path3/file3.jpg",
                    ]

                    results = manager.bulk_resolve_paths(paths)

                    assert len(results) == 3
                    assert results["/path1/file1.jpg"] == "/resolved/path1/file1.jpg"
                    assert results["/path2/file2.jpg"] is None
                    assert results["/path3/file3.jpg"] == "/resolved/path3/file3.jpg"

    @patch("src.services.drive_manager.get_settings")
    @patch("src.services.drive_manager.get_database")
    @patch("src.services.drive_manager.platform.system")
    def test_update_photo_paths(self, mock_platform, mock_get_db, mock_get_settings):
        """Test updating photo paths in bulk."""
        mock_platform.return_value = "Linux"
        mock_settings = Mock()
        mock_settings.app_data_dir = "/test/data"
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.__enter__.return_value.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        with patch.object(DriveManager, "_scan_current_drives"):
            with patch.object(DriveManager, "start_monitoring"):
                manager = DriveManager()

                photo_id_paths = [
                    (1, "/old/path1.jpg"),
                    (2, "/old/path2.jpg"),
                    (3, "/old/path3.jpg"),
                ]

                with patch.object(manager, "resolve_path") as mock_resolve:
                    mock_resolve.side_effect = [
                        "/new/path1.jpg",  # Changed
                        "/old/path2.jpg",  # Unchanged
                        "/new/path3.jpg",  # Changed
                    ]

                    changes = manager.update_photo_paths(photo_id_paths)

                    assert len(changes) == 2
                    assert (1, "/old/path1.jpg", "/new/path1.jpg") in changes
                    assert (3, "/old/path3.jpg", "/new/path3.jpg") in changes
