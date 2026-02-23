"""Daemon registry — check which agent daemons are alive via PID files."""

import os
import signal
from pathlib import Path
from typing import List

PID_DIR = Path(__file__).resolve().parent.parent / "runtimes" / "daemon-logs"

# Agents that can run as daemons
DAEMON_AGENTS = ("Claude", "Copilot", "Gemini", "Codex")


def pid_file_for(agent_name: str) -> Path:
    """Return the PID file path for an agent."""
    return PID_DIR / f"{agent_name.lower()}.pid"


def is_daemon_running(agent_name: str) -> bool:
    """Check if an agent daemon is alive via PID file + os.kill(pid, 0)."""
    pf = pid_file_for(agent_name)
    if not pf.exists():
        return False
    try:
        pid = int(pf.read_text().strip())
    except (ValueError, OSError):
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it — still alive
        return True


def running_daemons() -> List[str]:
    """Return names of all agent daemons that are currently alive."""
    return [name for name in DAEMON_AGENTS if is_daemon_running(name)]
