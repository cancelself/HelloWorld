"""Tests for the HelloWorld message bus (function API)."""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import message_bus
from message_bus import Message

# Store original BASE_DIR so we can restore it
_original_base = message_bus.BASE_DIR


def _use_tmp():
    """Point message_bus at a temp directory so tests start clean."""
    tmp = Path(tempfile.mkdtemp())
    message_bus.BASE_DIR = tmp
    return tmp


def _restore():
    message_bus.BASE_DIR = _original_base


def test_send_creates_message_file():
    tmp = _use_tmp()
    try:
        msg_id = message_bus.send("Copilot", "Claude", "explain: #collision")
        inbox = tmp / "claude" / "inbox"
        assert inbox.exists()
        files = list(inbox.glob("msg-*.hw"))
        assert len(files) == 1
        assert msg_id in files[0].stem
    finally:
        _restore()


def test_receive_returns_a_message():
    _use_tmp()
    try:
        message_bus.send("Copilot", "Claude", "first message")
        message_bus.send("Gemini", "Claude", "second message")
        msg = message_bus.receive("Claude")
        assert msg is not None
        assert msg.content == "first message"
    finally:
        _restore()


def test_receive_fifo_and_removes_message():
    tmp = _use_tmp()
    try:
        message_bus.send("Copilot", "Claude", "first message")
        message_bus.send("Gemini", "Claude", "second message")

        msg = message_bus.receive("Claude")
        assert msg is not None
        assert msg.content == "first message"

        inbox = tmp / "claude" / "inbox"
        remaining = list(inbox.glob("msg-*.hw"))
        assert len(remaining) == 1  # First message removed

        msg2 = message_bus.receive("Claude")
        assert msg2 is not None
        assert msg2.content == "second message"
    finally:
        _restore()


def test_receive_empty_inbox():
    _use_tmp()
    try:
        msg = message_bus.receive("Nobody")
        assert msg is None
    finally:
        _restore()


def test_hello_sends_to_helloworld():
    tmp = _use_tmp()
    try:
        msg_id = message_bus.hello("Claude")
        inbox = tmp / "helloworld" / "inbox"
        assert inbox.exists()
        files = list(inbox.glob("msg-*.hw"))
        assert len(files) == 1
        # Consume and check content
        msg = message_bus.receive("HelloWorld")
        assert msg is not None
        assert "Claude #hello" in msg.content
    finally:
        _restore()


def test_parse_message_headers():
    _use_tmp()
    try:
        message_bus.send("Target", "Guardian", "Guardian #sunyata")
        msg = message_bus.receive("Guardian")
        assert msg.sender == "Target"
        assert msg.timestamp  # non-empty
    finally:
        _restore()


def test_message_dataclass_fields():
    msg = Message(sender="Claude", content="hello", timestamp="2026-01-01T00:00:00Z")
    assert msg.sender == "Claude"
    assert msg.content == "hello"
    assert msg.timestamp == "2026-01-01T00:00:00Z"


def test_at_prefix_stripped():
    """Receiver names with @ prefix should be normalized."""
    tmp = _use_tmp()
    try:
        message_bus.send("Copilot", "@Claude", "test")
        inbox = tmp / "claude" / "inbox"
        assert inbox.exists()
        files = list(inbox.glob("msg-*.hw"))
        assert len(files) == 1
    finally:
        _restore()


if __name__ == "__main__":
    test_send_creates_message_file()
    test_receive_returns_a_message()
    test_receive_fifo_and_removes_message()
    test_receive_empty_inbox()
    test_hello_sends_to_helloworld()
    test_parse_message_headers()
    test_message_dataclass_fields()
    test_at_prefix_stripped()
    print("All message bus tests passed")
