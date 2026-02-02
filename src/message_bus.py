"""HelloWorld Message Bus — three functions matching the three vocabulary verbs.

    send(sender, receiver, content)  →  HelloWorld #send
    receive(receiver)                →  HelloWorld #receive
    hello(sender)                    →  HelloWorld #hello

Messages are .hw files in runtimes/<agent>/inbox/.
"""

import uuid
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


def _inbox(receiver: str) -> Path:
    """Return the inbox directory for a receiver, creating it if needed."""
    p = BASE_DIR / receiver.lstrip("@").lower() / "inbox"
    p.mkdir(parents=True, exist_ok=True)
    return p


def send(sender: str, receiver: str, content: str) -> str:
    """HelloWorld #send — deliver a message to a receiver's inbox.

    Writes a .hw file with minimal headers.  Returns the msg_id.
    """
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


def receive(receiver: str) -> Optional[Message]:
    """HelloWorld #receive — read the oldest message from a receiver's inbox.

    Parses headers, deletes the file, returns a Message (or None if empty).
    """
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


def hello(sender: str) -> str:
    """HelloWorld #hello — announce presence."""
    return send(sender, "HelloWorld", f"{sender} #hello")
