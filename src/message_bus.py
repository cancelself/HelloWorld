"""HelloWorld Message Bus — three functions matching the three vocabulary verbs.

    send(sender, receiver, content)  →  HelloWorld #send
    receive(receiver)                →  HelloWorld #receive
    hello(sender)                    →  HelloWorld #hello

Messages are routed through pluggable transports.  The default is
FileTransport (runtimes/<agent>/inbox/*.hw).  Set HW_TRANSPORT=clawnet
or call set_transport() for ClawNet.
"""

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent / "runtimes"


@dataclass
class Message:
    """A HelloWorld message between agents."""
    sender: str
    content: str
    timestamp: str


# ---------------------------------------------------------------------------
# Transport ABC
# ---------------------------------------------------------------------------

class Transport(ABC):
    """Abstract base for message transports."""

    @abstractmethod
    def send(self, sender: str, receiver: str, content: str) -> str:
        """Deliver a message.  Returns a msg_id."""

    @abstractmethod
    def receive(self, receiver: str) -> Optional[Message]:
        """Read the next message for *receiver* (or None)."""

    def hello(self, sender: str) -> str:
        """Announce presence.  Default sends to HelloWorld."""
        return self.send(sender, "HelloWorld", f"{sender} #hello")


# ---------------------------------------------------------------------------
# FileTransport — the original filesystem implementation
# ---------------------------------------------------------------------------

class FileTransport(Transport):
    """Deliver messages via .hw files in runtimes/<agent>/inbox/."""

    @property
    def base_dir(self) -> Path:
        """Read BASE_DIR dynamically so monkey-patching in tests works."""
        return BASE_DIR

    def send(self, sender: str, receiver: str, content: str) -> str:
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        msg_file = _inbox(receiver) / f"{msg_id}.hw"
        msg_file.write_text(
            f"# From: {sender}\n"
            f"# Timestamp: {timestamp}\n"
            f"\n"
            f"{content}\n"
        )
        return msg_id

    def receive(self, receiver: str) -> Optional[Message]:
        inbox = _inbox(receiver)
        files = sorted(inbox.glob("msg-*.hw"), key=lambda p: p.stat().st_mtime)
        if not files:
            return None

        msg_file = files[0]
        try:
            text = msg_file.read_text()
        except FileNotFoundError:
            return None

        sender = ""
        timestamp = ""
        content_start = 0

        for i, line in enumerate(text.split("\n")):
            if line.startswith("# From:"):
                sender = line.split(":", 1)[1].strip()
            elif line.startswith("# Timestamp:"):
                timestamp = line.split(":", 1)[1].strip()
            elif not line.startswith("#") and line.strip():
                content_start = i
                break

        content = "\n".join(text.split("\n")[content_start:]).strip()

        try:
            msg_file.unlink()
        except FileNotFoundError:
            pass

        return Message(sender=sender, content=content, timestamp=timestamp)


# ---------------------------------------------------------------------------
# Transport lifecycle
# ---------------------------------------------------------------------------

_transport: Optional[Transport] = None


def _get_transport() -> Transport:
    """Return the active transport, creating it lazily."""
    global _transport
    if _transport is not None:
        return _transport

    name = os.environ.get("HW_TRANSPORT", "file").lower()
    if name == "clawnet":
        from clawnet_transport import ClawNetTransport
        _transport = ClawNetTransport()
    else:
        _transport = FileTransport()
    return _transport


def set_transport(transport: Transport) -> None:
    """Override the active transport."""
    global _transport
    _transport = transport


def reset_transport() -> None:
    """Clear the cached transport (next call to send/receive will re-init)."""
    global _transport
    _transport = None


# ---------------------------------------------------------------------------
# _inbox — file-based, module-level, unchanged
# ---------------------------------------------------------------------------

def _inbox(receiver: str) -> Path:
    """Return the inbox directory for a receiver, creating it if needed."""
    p = BASE_DIR / receiver.lstrip("@").lower() / "inbox"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Module-level API — thin delegates
# ---------------------------------------------------------------------------

def send(sender: str, receiver: str, content: str) -> str:
    """HelloWorld #send — deliver a message to a receiver's inbox."""
    return _get_transport().send(sender, receiver, content)


def receive(receiver: str) -> Optional[Message]:
    """HelloWorld #receive — read the oldest message from a receiver's inbox."""
    return _get_transport().receive(receiver)


def hello(sender: str) -> str:
    """HelloWorld #hello — announce presence."""
    return _get_transport().hello(sender)
