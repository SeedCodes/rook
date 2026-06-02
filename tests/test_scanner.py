"""Tests for the system scanner."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / ".rook"))


class TestScannerHelpers(unittest.TestCase):
    """Test internal scanner helpers."""

    def test_run_captures_stdout(self):
        from rook import _run

        result = _run("echo hello", timeout=5)
        self.assertEqual(result, "hello")

    def test_run_handles_failure(self):
        from rook import _run

        result = _run("false", timeout=5)
        self.assertEqual(result, "")

    def test_run_handles_timeout(self):
        from rook import _run

        result = _run("sleep 100", timeout=1)
        self.assertEqual(result, "")

    def test_get_disk(self):
        from rook import _get_disk

        disk = _get_disk()
        self.assertIn("total", disk)
        self.assertIn("used", disk)
        self.assertIn("free", disk)
        # Format should be "XG"
        self.assertTrue(disk["total"].endswith("G"))

    @mock.patch("shutil.which")
    def test_get_packages_detects_managers(self, mock_which):
        from rook import _get_packages

        # Simulate apt and pip available
        mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x in ("apt", "pip") else None
        with mock.patch("rook._run") as mock_run:
            mock_run.return_value = "package1\npackage2"
            packages = _get_packages()

        self.assertIn("apt", packages)
        self.assertIn("pip", packages)


class TestScanSystem(unittest.TestCase):
    """Test full scan_system() function."""

    def test_scan_creates_context_file(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("rook.CONTEXT_PATH", Path(tmpdir) / "context.json"):
                from rook import scan_system

                scan_system()

                # Check file was created
                self.assertTrue((Path(tmpdir) / "context.json").exists())

                # Check required fields
                import json

                with open(Path(tmpdir) / "context.json") as f:
                    ctx = json.load(f)

                self.assertIn("os", ctx)
                self.assertIn("kernel", ctx)
                self.assertIn("shell", ctx)
                self.assertIn("user", ctx)
                self.assertIn("hostname", ctx)
                self.assertIn("last_scanned", ctx)


if __name__ == "__main__":
    unittest.main()
