"""Tests for daemon_registry — PID-based daemon detection."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import daemon_registry


@pytest.fixture
def tmp_pid_dir(tmp_path):
    """Use a temporary directory for PID files."""
    with mock.patch.object(daemon_registry, 'PID_DIR', tmp_path):
        yield tmp_path


class TestIsDaemonRunning:
    def test_missing_pid_file(self, tmp_pid_dir):
        assert daemon_registry.is_daemon_running("Claude") is False

    def test_valid_pid_current_process(self, tmp_pid_dir):
        """Our own PID should be detected as running."""
        pid_file = tmp_pid_dir / "claude.pid"
        pid_file.write_text(str(os.getpid()))
        assert daemon_registry.is_daemon_running("Claude") is True

    def test_stale_pid(self, tmp_pid_dir):
        """A PID that doesn't exist should return False."""
        pid_file = tmp_pid_dir / "gemini.pid"
        # Use a very high PID unlikely to exist
        pid_file.write_text("9999999")
        assert daemon_registry.is_daemon_running("Gemini") is False

    def test_corrupt_pid_file(self, tmp_pid_dir):
        """Non-integer content should return False."""
        pid_file = tmp_pid_dir / "codex.pid"
        pid_file.write_text("not-a-pid")
        assert daemon_registry.is_daemon_running("Codex") is False

    def test_empty_pid_file(self, tmp_pid_dir):
        """Empty file should return False."""
        pid_file = tmp_pid_dir / "copilot.pid"
        pid_file.write_text("")
        assert daemon_registry.is_daemon_running("Copilot") is False

    def test_case_insensitive_name(self, tmp_pid_dir):
        """PID file lookup lowercases the name."""
        pid_file = tmp_pid_dir / "claude.pid"
        pid_file.write_text(str(os.getpid()))
        assert daemon_registry.is_daemon_running("CLAUDE") is True
        assert daemon_registry.is_daemon_running("claude") is True


class TestRunningDaemons:
    def test_no_daemons(self, tmp_pid_dir):
        assert daemon_registry.running_daemons() == []

    def test_some_running(self, tmp_pid_dir):
        """Only agents with valid PIDs should be listed."""
        (tmp_pid_dir / "claude.pid").write_text(str(os.getpid()))
        (tmp_pid_dir / "gemini.pid").write_text("9999999")
        result = daemon_registry.running_daemons()
        assert "Claude" in result
        assert "Gemini" not in result

    def test_all_running(self, tmp_pid_dir):
        """All four agents alive."""
        for name in daemon_registry.DAEMON_AGENTS:
            (tmp_pid_dir / f"{name.lower()}.pid").write_text(str(os.getpid()))
        result = daemon_registry.running_daemons()
        assert len(result) == 4


class TestPidFileFor:
    def test_returns_correct_path(self, tmp_pid_dir):
        path = daemon_registry.pid_file_for("Claude")
        assert path == tmp_pid_dir / "claude.pid"
