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

        self.assertIn("Rook", output)
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

    def test_banner_no_unicode_art(self):
        from io import StringIO

        from rook import print_banner

        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            print_banner()
            output = fake_out.getvalue()

        # Should NOT contain any Unicode block drawing characters
        self.assertNotIn("▄", output)
        self.assertNotIn("▀", output)
        self.assertNotIn("█", output)


class TestRotateRecordings(unittest.TestCase):
    """Test that _rotate_recordings() clears the recording files."""

    def test_rotate_clears_recording_log(self):
        from rook import _rotate_recordings

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "recording.log").write_text("old noise from parent shell\n")
            (tmp / "terminal.log").write_text("1780408972|0|cls\n")

            with mock.patch("rook.ROOK_DIR", tmp):
                _rotate_recordings()

            self.assertEqual((tmp / "recording.log").read_text(), "")
            self.assertEqual((tmp / "terminal.log").read_text(), "")

    def test_rotate_handles_missing_files(self):
        from rook import _rotate_recordings

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # No files exist
            with mock.patch("rook.ROOK_DIR", tmp):
                # Should not raise
                _rotate_recordings()


class TestLoadRecordingFiltersNoise(unittest.TestCase):
    """Test that load_recording() filters out known banner noise."""

    def test_filters_cipher_banner(self):
        from rook import load_recording

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "recording.log").write_text(
                "========================================\n"
                "I am Cipher\n"
                "Disciplined | Focused | Relentless\n"
                "Build. Learn. Execute. Repeat.\n"
                "========================================\n"
                "actual user output\n"
            )

            with mock.patch("rook.ROOK_DIR", tmp):
                result = load_recording(max_lines=50)

        self.assertNotIn("Cipher", result)
        self.assertNotIn("Disciplined", result)
        self.assertNotIn("Build. Learn", result)
        self.assertIn("actual user output", result)


class TestRunCmd(unittest.TestCase):
    """Test _run_cmd() executes commands."""

    def test_runs_simple_command(self):
        from rook import _run_cmd

        output, code = _run_cmd("echo hello")
        self.assertEqual(output, "hello")
        self.assertEqual(code, 0)

    def test_captures_stderr(self):
        from rook import _run_cmd

        output, code = _run_cmd("ls /nonexistent_path_xyz 2>&1")
        self.assertIn("No such file", output)
        self.assertNotEqual(code, 0)

    def test_timeout(self):
        from rook import _run_cmd

        output, code = _run_cmd("sleep 60")
        self.assertIn("timed out", output)
        self.assertEqual(code, -1)


class TestHandleResponse(unittest.TestCase):
    """Test _handle_response() parses <cmd> tags and executes."""

    @mock.patch("builtins.print")
    def test_prints_text_before_cmd(self, mock_print):
        from rook import _handle_response

        messages = []
        cfg = {"model": "test", "ollama_url": "http://localhost:11434"}

        resp = "Let me check.\n<cmd>echo hello</cmd>"
        with mock.patch("rook._run_cmd", return_value=("hello", 0)):
            _handle_response(resp, messages, cfg)

        # Should have printed "Let me check."
        printed = [str(c) for c in mock_print.call_args_list]
        self.assertTrue(any("Let me check." in c for c in printed))

    @mock.patch("builtins.print")
    @mock.patch("rook._run_cmd", return_value=("output_line", 0))
    def test_executes_cmd_tag(self, mock_run, mock_print):
        from rook import _handle_response

        messages = []
        cfg = {"model": "test", "ollama_url": "http://localhost:11434"}

        resp = "<cmd>echo test</cmd>"
        _handle_response(resp, messages, cfg)

        mock_run.assert_called_once_with("echo test")
        # Output should be printed
        printed = [str(c) for c in mock_print.call_args_list]
        self.assertTrue(any("output_line" in c for c in printed))

    @mock.patch("builtins.print")
    @mock.patch("rook._run_cmd", return_value=("result", 0))
    def test_adds_cmd_result_to_messages(self, mock_run, mock_print):
        from rook import _handle_response

        messages = []
        cfg = {"model": "test", "ollama_url": "http://localhost:11434"}

        resp = "Check this:\n<cmd>ls</cmd>"
        _handle_response(resp, messages, cfg)

        # Should have 2 assistant messages: cmd_result + original
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]
        self.assertEqual(len(assistant_msgs), 2)
        self.assertIn("[command] ls", assistant_msgs[0]["content"])
        self.assertIn("[output] result", assistant_msgs[0]["content"])


if __name__ == "__main__":
    unittest.main()
