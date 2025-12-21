import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

from fastapi import HTTPException

# Import module under test
from src.api import config


class TestConfigCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock()

        self.patches = [
            patch("src.api.config.get_database_manager", return_value=self.mock_db_manager),
            patch("src.api.config.run_in_threadpool"),
            patch("src.api.config.validate_path"),
            patch("src.api.config.get_default_photo_roots", return_value=["/default/path"]),
        ]

        self.mock_deps = [p.start() for p in self.patches]
        self.mock_db = self.mock_deps[0].return_value
        self.mock_run = self.mock_deps[1]
        self.mock_validate = self.mock_deps[2]

        # Configure run_in_threadpool to execute the function immediately
        async def side_effect(func, *args, **kwargs):
            return func(*args, **kwargs)
        self.mock_run.side_effect = side_effect

    def tearDown(self):
        patch.stopall()

    def test_get_configuration_success(self):
        """Test getting configuration successfully."""
        # Mock _get_config_from_db logic (it calls db_manager.execute_query)
        self.mock_db.execute_query.return_value = [
            ("roots", '["/a/b"]'),
            ("face_search_enabled", "true"),
            ("batch_size", "100")
        ]

        result = asyncio.run(config.get_configuration())

        self.assertEqual(result.roots, ["/a/b"])
        self.assertTrue(result.face_search_enabled)
        self.assertEqual(result.batch_size, 100)

    def test_get_configuration_exception(self):
        """Test exception handling in get_configuration."""
        self.mock_run.side_effect = Exception("DB Error")

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(config.get_configuration())
        self.assertEqual(cm.exception.status_code, 500)

    def test_update_root_folders_success(self):
        """Test updating root folders."""
        # Setup existing roots
        # _get_config_from_db mock return
        self.mock_db.execute_query.return_value = [
            ("roots", '["/old/root"]')
        ]

        # Setup validate_path
        self.mock_validate.return_value = Path("/new/root")

        request = config.UpdateRootsRequest(roots=["/new/root"])

        # Mock result of sync function via run_in_threadpool (logic runs inside)
        # But wait, run_in_threadpool side_effect executes the function.
        # So I am testing _update_root_folders_sync logic too!

        result = asyncio.run(config.update_root_folders(request))

        self.assertIn("/new/root", result["roots"])
        self.assertIn("/old/root", result["removed_roots"])

        # Verify DB updates
        # Should have deleted photos from removed root
        # and updated config
        self.assertTrue(self.mock_db.execute_update.called)

    def test_update_root_folders_invalid_path(self):
        """Test updating with invalid path."""
        # Validation happens in Pydantic model validator, which calls validate_path
        # If I mock validate_path to raise, instantiating UpdateRootsRequest should fail.

        self.mock_validate.side_effect = ValueError("Invalid path")

        with self.assertRaises(ValueError):
            config.UpdateRootsRequest(roots=["/invalid"])

    def test_update_root_folders_exception(self):
        """Test exception during update."""
        self.mock_run.side_effect = Exception("Update failed")

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(config.update_root_folders(MagicMock()))
        self.assertEqual(cm.exception.status_code, 500)

    def test_remove_root_folder(self):
        """Test removing a root folder."""
        # Setup existing roots
        self.mock_db.execute_query.return_value = [
            ("roots", '["/root/1", "/root/2"]')
        ]

        result = asyncio.run(config.remove_root_folder(0))

        self.assertEqual(result["removed_root"], "/root/1")
        self.assertEqual(result["remaining_roots"], ["/root/2"])

    def test_remove_root_folder_index_error(self):
        """Test removing non-existent index."""
        self.mock_db.execute_query.return_value = [
            ("roots", '["/root/1"]')
        ]

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(config.remove_root_folder(10))
        self.assertEqual(cm.exception.status_code, 404)

    def test_reset_configuration(self):
        """Test resetting configuration."""
        result = asyncio.run(config.reset_configuration())

        self.assertEqual(result["configuration"]["thumbnail_size"], "medium")
        self.assertTrue(self.mock_db.execute_update.called)

    def test_update_configuration(self):
        """Test updating general config."""
        request = config.UpdateConfigRequest(batch_size=200)

        # Mock _get_config_from_db result after update
        self.mock_db.execute_query.return_value = [
            ("batch_size", "200")
        ]

        result = asyncio.run(config.update_configuration(request))

        self.assertIn("batch_size", result["updated_fields"])
        self.assertTrue(self.mock_db.execute_update.called)

    def test_update_configuration_empty(self):
        """Test updating with no fields."""
        request = config.UpdateConfigRequest()

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(config.update_configuration(request))
        self.assertEqual(cm.exception.status_code, 400)

    def test_parsing_helpers(self):
        """Test internal parsing helpers."""
        # _parse_boolean_setting
        self.assertTrue(config._parse_boolean_setting("true"))
        self.assertFalse(config._parse_boolean_setting("false"))
        self.assertFalse(config._parse_boolean_setting(None))

        # _parse_int_setting
        self.assertEqual(config._parse_int_setting("key", "123"), 123)
        self.assertEqual(config._parse_int_setting("key", "invalid"), 0) # Fallback

        # _parse_json_setting
        self.assertEqual(config._parse_json_setting("roots", '["a"]'), ["a"])
        self.assertEqual(config._parse_json_setting("roots", "invalid"), []) # Fallback

    def test_get_config_from_db_error(self):
        """Test DB error fallback in _get_config_from_db."""
        self.mock_db.execute_query.side_effect = Exception("DB Fail")

        result = config._get_config_from_db(self.mock_db)

        # Should return defaults
        self.assertIn("roots", result)
        self.assertEqual(result["thumbnail_size"], "medium")

    def test_get_config_defaults(self):
        """Test get_default_configuration endpoint."""
        result = asyncio.run(config.get_default_configuration())
        self.assertIn("roots", result)
        self.assertEqual(result["batch_size"], 50)


