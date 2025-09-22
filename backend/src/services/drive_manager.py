"""Drive aliasing and path resolution service for handling drive letter changes."""

import json
import logging
import os
import platform
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from ..core.config import get_settings
from ..db.connection import get_database

logger = logging.getLogger(__name__)


class DriveManager:
    """
    Manages drive aliases and path resolution for cross-platform compatibility.

    This service handles:
    - Drive letter changes on Windows
    - Mount point changes on macOS/Linux
    - Network drive mappings
    - Path resolution with fallback mechanisms
    - Device identification and aliasing
    """

    def __init__(self):
        self.settings = get_settings()
        self.platform = platform.system().lower()

        # Drive mappings: device_id -> alias
        self.drive_mappings: dict[str, str] = {}
        # Reverse mapping: alias -> device_id
        self.alias_mappings: dict[str, str] = {}
        # Current mount points: device_id -> current_path
        self.current_mounts: dict[str, str] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Background monitoring
        self._monitoring = False
        self._monitor_thread = None

        # Initialize drive mappings
        self._initialize_mappings()
        self._scan_current_drives()

        # Start background monitoring
        self.start_monitoring()

    def _initialize_mappings(self):
        """Initialize drive mappings from database."""
        try:
            with get_database() as db:
                cursor = db.execute(
                    """
                    SELECT device_id, alias, mount_point, last_seen
                    FROM drive_aliases
                    ORDER BY last_seen DESC
                """
                )

                for row in cursor.fetchall():
                    device_id, alias, mount_point, _last_seen = row
                    self.drive_mappings[device_id] = alias
                    self.alias_mappings[alias] = device_id

                    # Check if mount point still exists
                    if mount_point and os.path.exists(mount_point):
                        self.current_mounts[device_id] = mount_point

                logger.info(f"Loaded {len(self.drive_mappings)} drive aliases")

        except Exception as e:
            logger.exception(f"Failed to initialize drive mappings: {e}")

    def _scan_current_drives(self):
        """Scan for currently available drives and update mappings."""
        try:
            if self.platform == "windows":
                self._scan_windows_drives()
            else:
                self._scan_unix_drives()

        except Exception as e:
            logger.exception(f"Failed to scan current drives: {e}")

    def _scan_windows_drives(self):
        """Scan Windows drives using volume information."""
        try:
            import win32api
            import win32file

            drives = win32api.GetLogicalDriveStrings()
            drive_list = drives.split("\x00")[:-1]

            for drive in drive_list:
                try:
                    # Get volume information
                    volume_info = win32api.GetVolumeInformation(drive)
                    (
                        volume_name,
                        volume_serial,
                        _max_component_length,
                        _file_system_flags,
                        _file_system_name,
                    ) = volume_info

                    # Create device ID from volume serial
                    device_id = f"win_vol_{volume_serial:08X}"

                    # Get drive type
                    drive_type = win32file.GetDriveType(drive)
                    is_removable = drive_type in [
                        win32file.DRIVE_REMOVABLE,
                        win32file.DRIVE_CDROM,
                    ]

                    # Update mappings
                    self._update_drive_mapping(
                        device_id, drive.rstrip("\\"), volume_name, is_removable
                    )

                except Exception as e:
                    logger.warning(f"Failed to get info for drive {drive}: {e}")

        except ImportError:
            # Fallback for systems without pywin32
            self._scan_windows_drives_fallback()

    def _scan_windows_drives_fallback(self):
        """Fallback Windows drive scanning without pywin32."""
        try:
            # Use basic drive detection
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    # Create a basic device ID
                    device_id = f"win_drive_{letter}"
                    self._update_drive_mapping(
                        device_id,
                        drive_path.rstrip("\\"),
                        f"Drive {letter}",
                        is_removable=False,
                    )

        except Exception as e:
            logger.exception(f"Fallback drive scanning failed: {e}")

    def _scan_unix_drives(self):
        """Scan Unix-like system mount points."""
        try:
            # Read /proc/mounts or /etc/mtab
            mount_files = ["/proc/mounts", "/etc/mtab"]
            mount_info = None

            for mount_file in mount_files:
                if os.path.exists(mount_file):
                    with open(mount_file) as f:
                        mount_info = f.read()
                    break

            if not mount_info:
                logger.warning("Could not read mount information")
                return

            # Parse mount points
            for line in mount_info.strip().split("\n"):
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 6:
                    continue

                device, mount_point, fs_type = parts[0], parts[1], parts[2]

                # Skip virtual filesystems
                if fs_type in ["proc", "sysfs", "devpts", "tmpfs", "devtmpfs"]:
                    continue

                # Skip if not a real mount point
                if not os.path.ismount(mount_point):
                    continue

                # Create device ID
                if device.startswith("/dev/"):
                    # Real device
                    device_id = f"unix_dev_{device.replace('/', '_')}"
                    is_removable = self._is_removable_device(device)
                else:
                    # Network or other
                    device_id = f"unix_net_{device.replace('/', '_').replace(':', '_')}"
                    is_removable = True

                self._update_drive_mapping(
                    device_id, mount_point, Path(device).name, is_removable
                )

        except Exception as e:
            logger.exception(f"Unix drive scanning failed: {e}")

    def _is_removable_device(self, device: str) -> bool:
        """Check if a device is removable on Unix systems."""
        try:
            # Check if device is in removable device directory
            removable_patterns = [
                r"/dev/sd[a-z]+\d*",  # USB drives
                r"/dev/mmcblk\d+",  # SD cards
                r"/dev/fd\d+",  # Floppy disks
            ]

            return any(re.match(pattern, device) for pattern in removable_patterns)

        except Exception:
            return False

    def _update_drive_mapping(
        self, device_id: str, mount_point: str, volume_name: str, is_removable: bool
    ):
        """Update drive mapping in memory and database."""
        with self._lock:
            try:
                # Update current mount
                self.current_mounts[device_id] = mount_point

                # Create or update alias
                if device_id not in self.drive_mappings:
                    # Create new alias
                    if volume_name and volume_name.strip():
                        alias = self._sanitize_alias(volume_name)
                    else:
                        alias = f"drive_{len(self.drive_mappings) + 1}"

                    # Ensure alias is unique
                    original_alias = alias
                    counter = 1
                    while alias in self.alias_mappings:
                        alias = f"{original_alias}_{counter}"
                        counter += 1

                    self.drive_mappings[device_id] = alias
                    self.alias_mappings[alias] = device_id

                # Update database
                self._save_drive_mapping(
                    device_id, self.drive_mappings[device_id], mount_point
                )

                logger.debug(
                    f"Updated drive mapping: {device_id} -> {alias} at {mount_point}"
                )

            except Exception as e:
                logger.exception(f"Failed to update drive mapping: {e}")

    def _sanitize_alias(self, name: str) -> str:
        """Sanitize a volume name to create a valid alias."""
        # Remove invalid characters and normalize
        alias = re.sub(r"[^\w\-_]", "_", name.strip())
        alias = re.sub(r"_+", "_", alias)
        alias = alias.strip("_").lower()

        # Ensure it's not empty
        if not alias:
            alias = "unnamed"

        return alias

    def _save_drive_mapping(self, device_id: str, alias: str, mount_point: str):
        """Save drive mapping to database."""
        try:
            with get_database() as db:
                db.execute(
                    """
                    INSERT OR REPLACE INTO drive_aliases
                    (device_id, alias, mount_point, last_seen)
                    VALUES (?, ?, ?, ?)
                """,
                    (device_id, alias, mount_point, time.time()),
                )

        except Exception as e:
            logger.exception(f"Failed to save drive mapping: {e}")

    def resolve_path(self, path: str) -> str | None:
        """
        Resolve a path that might contain outdated drive references.

        Args:
            path: Path to resolve (can be absolute or aliased)

        Returns:
            Resolved absolute path or None if not resolvable
        """
        try:
            # If path exists as-is, return it
            if os.path.exists(path):
                return str(Path(path).resolve())

            # Try path resolution based on platform
            if self.platform == "windows":
                return self._resolve_windows_path(path)
            return self._resolve_unix_path(path)

        except Exception as e:
            logger.debug(f"Failed to resolve path {path}: {e}")
            return None

    def _resolve_windows_path(self, path: str) -> str | None:
        """Resolve Windows path with drive letter changes."""
        try:
            # Extract drive letter
            if len(path) >= 2 and path[1] == ":":
                old_drive = path[:2]
                rest_of_path = path[2:]

                # Find current mapping for this drive type
                for current_mount in self.current_mounts.values():
                    if current_mount.lower().startswith(old_drive.lower()):
                        continue

                    # Try to find the same device on a different drive
                    candidate_path = current_mount + rest_of_path
                    if os.path.exists(candidate_path):
                        logger.info(f"Resolved path {path} -> {candidate_path}")
                        return candidate_path

                # Try all available drives
                for current_mount in self.current_mounts.values():
                    candidate_path = current_mount + rest_of_path
                    if os.path.exists(candidate_path):
                        logger.info(f"Resolved path {path} -> {candidate_path}")
                        return candidate_path

            return None

        except Exception as e:
            logger.debug(f"Windows path resolution failed: {e}")
            return None

    def _resolve_unix_path(self, path: str) -> str | None:
        """Resolve Unix path with mount point changes."""
        try:
            # Try to find the path in alternative mount points
            for current_mount in self.current_mounts.values():
                # Skip if it's the same mount point
                if path.startswith(current_mount):
                    continue

                # Find the relative part of the path
                for old_mount in ["/media", "/mnt", "/Volumes"]:
                    if path.startswith(old_mount):
                        # Extract the relative path
                        parts = path.split("/", 3)
                        if len(parts) >= 4:
                            relative_path = parts[3]
                            candidate_path = os.path.join(current_mount, relative_path)
                            if os.path.exists(candidate_path):
                                logger.info(f"Resolved path {path} -> {candidate_path}")
                                return candidate_path

            return None

        except Exception as e:
            logger.debug(f"Unix path resolution failed: {e}")
            return None

    def create_stable_path(self, path: str) -> str:
        """
        Create a stable path representation using device aliases.

        Args:
            path: Absolute path to convert

        Returns:
            Stable path representation
        """
        try:
            abs_path = str(Path(path).resolve())

            # Find the best matching device
            best_match = ""
            best_device_id = ""

            for device_id, mount_point in self.current_mounts.items():
                if abs_path.startswith(mount_point) and len(mount_point) > len(
                    best_match
                ):
                    best_match = mount_point
                    best_device_id = device_id

            if best_device_id and best_device_id in self.drive_mappings:
                alias = self.drive_mappings[best_device_id]
                relative_path = abs_path[len(best_match) :].lstrip(os.sep)
                return (
                    f"${alias}${os.sep}{relative_path}"
                    if relative_path
                    else f"${alias}$"
                )

            # Fallback to original path
            return abs_path

        except Exception as e:
            logger.debug(f"Failed to create stable path for {path}: {e}")
            return path

    def resolve_stable_path(self, stable_path: str) -> str | None:
        """
        Resolve a stable path back to current absolute path.

        Args:
            stable_path: Stable path with device alias

        Returns:
            Current absolute path or None
        """
        try:
            # Check if it's a stable path format
            if not stable_path.startswith("$") or "$" not in stable_path[1:]:
                return self.resolve_path(stable_path)

            # Extract alias and relative path
            parts = stable_path[1:].split("$", 1)
            if len(parts) != 2:
                return None

            alias, relative_path = parts

            # Find device for alias
            if alias not in self.alias_mappings:
                logger.debug(f"Unknown alias: {alias}")
                return None

            device_id = self.alias_mappings[alias]
            if device_id not in self.current_mounts:
                logger.debug(f"Device not currently mounted: {device_id}")
                return None

            # Reconstruct path
            mount_point = self.current_mounts[device_id]
            if relative_path:
                resolved_path = os.path.join(mount_point, relative_path)
            else:
                resolved_path = mount_point

            return resolved_path if os.path.exists(resolved_path) else None

        except Exception as e:
            logger.debug(f"Failed to resolve stable path {stable_path}: {e}")
            return None

    def get_drive_status(self) -> dict[str, dict]:
        """Get status of all known drives."""
        with self._lock:
            status = {}

            for device_id, alias in self.drive_mappings.items():
                is_online = device_id in self.current_mounts
                mount_point = self.current_mounts.get(device_id, "Unknown")

                status[alias] = {
                    "device_id": device_id,
                    "alias": alias,
                    "mount_point": mount_point,
                    "is_online": is_online,
                    "platform": self.platform,
                }

            return status

    def start_monitoring(self):
        """Start background monitoring for drive changes."""
        if self._monitoring:
            return

        self._monitoring = True

        def monitor_loop():
            """Background monitoring loop."""
            while self._monitoring:
                try:
                    self._scan_current_drives()
                    time.sleep(30)  # Check every 30 seconds

                except Exception as e:
                    logger.exception(f"Error in drive monitoring: {e}")
                    time.sleep(60)  # Wait longer on error

        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info("Drive monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Drive monitoring stopped")

    def bulk_resolve_paths(self, paths: list[str]) -> dict[str, str | None]:
        """
        Resolve multiple paths efficiently.

        Args:
            paths: List of paths to resolve

        Returns:
            Dictionary mapping original paths to resolved paths
        """
        results = {}

        for path in paths:
            resolved = self.resolve_path(path)
            results[path] = resolved

        return results

    def update_photo_paths(
        self, photo_id_paths: list[tuple[int, str]]
    ) -> list[tuple[int, str, str]]:
        """
        Update photo paths in bulk and return changes.

        Args:
            photo_id_paths: List of (photo_id, current_path) tuples

        Returns:
            List of (photo_id, old_path, new_path) tuples for changed paths
        """
        changes = []

        for photo_id, current_path in photo_id_paths:
            resolved_path = self.resolve_path(current_path)

            if resolved_path and resolved_path != current_path:
                changes.append((photo_id, current_path, resolved_path))

        return changes
