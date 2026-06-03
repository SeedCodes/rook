"""Tests for chat REPL and AI backend integration."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / ".rook"))

from tests.fixtures import SAMPLE_RECORDING, SAMPLE_TERMINAL_LOG  # noqa: E402


class TestCallAi(unittest.TestCase):
    """Test call_ai() function with mocked HTTP."""

    @mock.patch("requests.post")
    def test_successful_request(self, mock_post):
        from rook import call_ai

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, world!"}}]
        }
        mock_post.return_value = mock_response

        cfg = {"model": "gemma3:1b", "ollama_url": "http://localhost:11434"}
        messages = [{"role": "user", "content": "hi"}]

        result = call_ai(messages, cfg)

        self.assertEqual(result, "Hello, world!")
        mock_post.assert_called_once()

    @mock.patch("requests.post")
    def test_api_error(self, mock_post):
        from rook import call_ai

        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        cfg = {"model": "gemma3:1b", "ollama_url": "http://localhost:11434"}
        messages = [{"role": "user", "content": "hi"}]

        result = call_ai(messages, cfg)

        self.assertIn("API error", result)
        self.assertIn("500", result)


class TestAiQuery(unittest.TestCase):
    """Test ai_query() with mocked AI backend."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @mock.patch("rook.call_ai")
    def test_simple_query(self, mock_ai):
        from rook import ai_query

        mock_ai.return_value = "I am Rook."

        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            result = ai_query("who are you?", mode="query")

        self.assertEqual(result, "I am Rook.")
        mock_ai.assert_called_once()

    @mock.patch("rook.call_ai")
    @mock.patch("rook.web_search")
    def test_web_search_triggered(self, mock_search, mock_ai):
        from rook import ai_query

        mock_search.return_value = [
            {"title": "Test", "url": "https://example.com", "description": "Test desc"}
        ]
        mock_ai.return_value = "Found it."

        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            result = ai_query("how to install docker", mode="query")

        mock_search.assert_called_once()
        self.assertEqual(result, "Found it.")


class TestCmdQuery(unittest.TestCase):
    """Test cmd_query() prints AI response."""

    @mock.patch("rook.ai_query")
    @mock.patch("builtins.print")
    def test_cmd_query_prints(self, mock_print, mock_ai):
        from rook import cmd_query

        mock_ai.return_value = "The answer is 42."

        args = mock.Mock()
        args.query = ["what", "is", "the", "answer"]

        cmd_query(args)

        mock_ai.assert_called_once_with("what is the answer", mode="query")
        mock_print.assert_called_once_with("The answer is 42.")


class TestChatContextInjection(unittest.TestCase):
    """Test that cmd_chat() includes terminal context in messages."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_chat_includes_recording(self):
        from rook import load_recording

        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            (Path(self.tmpdir) / "recording.log").write_text(SAMPLE_RECORDING)
            (Path(self.tmpdir) / "terminal.log").write_text(SAMPLE_TERMINAL_LOG)

            recording = load_recording(max_lines=20)

        self.assertIn("zsh: command not found: exho", recording)

    def test_chat_includes_cmd_log(self):
        from rook import load_cmd_log

        with mock.patch("rook.ROOK_DIR", Path(self.tmpdir)):
            (Path(self.tmpdir) / "terminal.log").write_text(SAMPLE_TERMINAL_LOG)

            log = load_cmd_log(max_lines=20)

        self.assertIn("[127]", log)
        self.assertIn("exho $SHELL", log)


class TestVersion(unittest.TestCase):
    """Test that __version__ is defined and follows semver."""

    def test_version_is_defined(self):
        import rook

        self.assertTrue(hasattr(rook, "__version__"))

    def test_version_format(self):
        import re

        import rook

        self.assertRegex(rook.__version__, r"^\d+\.\d+\.\d+$")


class TestPrintBanner(unittest.TestCase):
    """Test print_banner() output."""

    def test_banner_contains_rook_text(self):
        from io import StringIO

        from rook import print_banner

        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            print_banner()
            output = fake_out.getvalue()

        self.assertIn("R  O  O  K", output)
        self.assertIn("System-aware AI copilot", output)

    def test_banner_contains_escape_codes(self):
        from io import StringIO

        from rook import print_banner

        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            print_banner()
            output = fake_out.getvalue()

        # Should have ANSI color codes
        self.assertIn(chr(27) + "[1;32m", output)  # green
        self.assertIn(chr(27) + "[0m", output)      # reset

    def test_banner_contains_version(self):
        from io import StringIO

        import rook
        from rook import print_banner

        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            print_banner()
            output = fake_out.getvalue()

        self.assertIn(rook.__version__, output)

    def test_banner_contains_ascii_art_chars(self):
        from io import StringIO

        from rook import print_banner

        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            print_banner()
            output = fake_out.getvalue()

        # Box drawing chars
        self.assertIn("▄", output)  # lower half block
        self.assertIn("▀", output)  # upper half block
        self.assertIn("█", output)  # full block


if __name__ == "__main__":
    unittest.main()
