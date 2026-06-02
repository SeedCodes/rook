"""Tests for parsing and context-loading functions."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".rook"))

from tests.fixtures import (  # noqa: E402
    SAMPLE_CONTEXT,
    SAMPLE_RECORDING,
    SAMPLE_RECORDING_WITH_ANSI,
    SAMPLE_TERMINAL_LOG,
)


class TestParseResponse(unittest.TestCase):
    """Test parse_response() strips markdown code fences."""

    def test_strips_basic_code_fence(self):
        from rook import parse_response

        text = "```bash\necho hello\n```"
        result = parse_response(text)
        self.assertEqual(result, "echo hello")

    def test_strips_code_fence_with_language(self):
        from rook import parse_response

        text = "```python\nprint('hi')\n```"
        result = parse_response(text)
        self.assertEqual(result, "print('hi')")

    def test_strips_code_fence_without_language(self):
        from rook import parse_response

        text = "```\nls -la\n```"
        result = parse_response(text)
        self.assertEqual(result, "ls -la")

    def test_no_code_fence_unchanged(self):
        from rook import parse_response

        text = "echo hello"
        result = parse_response(text)
        self.assertEqual(result, "echo hello")

    def test_strips_whitespace(self):
        from rook import parse_response

        text = "  \n  echo hello  \n  "
        result = parse_response(text)
        self.assertEqual(result, "echo hello")

    def test_handles_multiple_fences(self):
        from rook import parse_response

        text = "First: ```bash\necho a\n``` then ```\necho b\n```"
        result = parse_response(text)
        self.assertIn("echo a", result)
        self.assertIn("echo b", result)


class TestLoadRecording(unittest.TestCase):
    """Test load_recording() cleans up script output."""

    def setUp(self):
        from rook import ROOK_DIR

        self.original_rook_dir = ROOK_DIR
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_loads_clean_recording(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            (Path(self.tmpdir) / "recording.log").write_text(SAMPLE_RECORDING)
            from rook import load_recording

            result = load_recording(max_lines=20)

        self.assertIn("exho $SHELL", result)
        self.assertIn("zsh: command not found: exho", result)
        self.assertIn("echo $SHELL", result)
        self.assertIn("/usr/bin/zsh", result)

    def test_strips_script_headers(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            (Path(self.tmpdir) / "recording.log").write_text(SAMPLE_RECORDING)
            from rook import load_recording

            result = load_recording(max_lines=20)

        self.assertNotIn("Script started", result)
        self.assertNotIn("Script done", result)
        self.assertNotIn("COMMAND=", result)

    def test_strips_ansi_codes(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            (Path(self.tmpdir) / "recording.log").write_text(SAMPLE_RECORDING_WITH_ANSI)
            from rook import load_recording

            result = load_recording(max_lines=20)

        self.assertNotIn("\x1b[", result)
        self.assertIn("exho $SHELL", result)

    def test_handles_missing_file(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            from rook import load_recording

            result = load_recording(max_lines=20)

        self.assertEqual(result, "")

    def test_respects_max_lines(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            long_recording = "line\n" * 200
            (Path(self.tmpdir) / "recording.log").write_text(long_recording)
            from rook import load_recording

            result = load_recording(max_lines=10)

        # 10 lines max
        self.assertEqual(len(result.splitlines()), 10)

    def test_normalizes_crlf(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            content = "line1\r\nline2\r\nline3\r\n"
            (Path(self.tmpdir) / "recording.log").write_text(content)
            from rook import load_recording

            result = load_recording(max_lines=20)

        self.assertNotIn("\r", result)
        self.assertIn("line1", result)
        self.assertIn("line2", result)


class TestLoadCmdLog(unittest.TestCase):
    """Test load_cmd_log() parses structured command log."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_loads_cmd_log(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            (Path(self.tmpdir) / "terminal.log").write_text(SAMPLE_TERMINAL_LOG)
            from rook import load_cmd_log

            result = load_cmd_log(max_lines=10)

        self.assertIn("exho $SHELL", result)
        self.assertIn("echo $SHELL", result)
        self.assertIn("[127]", result)
        self.assertIn("[0]", result)

    def test_handles_missing_file(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            from rook import load_cmd_log

            result = load_cmd_log(max_lines=10)

        self.assertEqual(result, "")

    def test_respects_max_lines(self):
        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            lines = "\n".join(f"{i}|0|cmd{i}" for i in range(50))
            (Path(self.tmpdir) / "terminal.log").write_text(lines)
            from rook import load_cmd_log

            result = load_cmd_log(max_lines=5)

        # Should only have 5 entries
        self.assertEqual(len([l for l in result.splitlines() if l.strip()]), 5)


class TestBuildSystemPrompt(unittest.TestCase):
    """Test build_system_prompt() formats context correctly."""

    def test_includes_system_info(self):
        from rook import build_system_prompt

        prompt = build_system_prompt(SAMPLE_CONTEXT, [])

        self.assertIn("Rook", prompt)
        self.assertIn("Ubuntu 26.04", prompt)
        self.assertIn("simran", prompt)
        self.assertIn("zsh", prompt)
        self.assertIn("AMD Ryzen", prompt)

    def test_includes_rules(self):
        from rook import build_system_prompt

        prompt = build_system_prompt(SAMPLE_CONTEXT, [])

        self.assertIn("<cmd>", prompt)
        self.assertIn("plain text", prompt.lower())

    def test_handles_empty_context(self):
        from rook import build_system_prompt

        prompt = build_system_prompt({}, [])

        self.assertIn("No system context", prompt)
        self.assertIn("rook scan", prompt)

    def test_includes_projects_from_home(self):
        from rook import build_system_prompt

        prompt = build_system_prompt(SAMPLE_CONTEXT, [])

        self.assertIn("Desktop", prompt)


if __name__ == "__main__":
    unittest.main()
