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
    message_bus.reset_transport()
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


# ---------------------------------------------------------------------------
# SQLiteTransport tests
# ---------------------------------------------------------------------------

def test_sqlite_send_and_receive():
    """SQLiteTransport round-trips messages."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        msg_id = t.send("Copilot", "Claude", "explain: #collision")
        assert msg_id.startswith("msg-")
        msg = t.receive("claude")
        assert msg is not None
        assert msg.sender == "Copilot"
        assert msg.content == "explain: #collision"


def test_sqlite_fifo_order():
    """SQLiteTransport delivers in FIFO order."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        t.send("A", "claude", "first")
        t.send("B", "claude", "second")
        assert t.receive("claude").content == "first"
        assert t.receive("claude").content == "second"
        assert t.receive("claude") is None


def test_sqlite_empty_inbox():
    """SQLiteTransport returns None for empty inbox."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        assert t.receive("nobody") is None


def test_sqlite_at_prefix_stripped():
    """SQLiteTransport normalizes @ prefix on receiver."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        t.send("A", "@Claude", "test")
        msg = t.receive("Claude")
        assert msg is not None
        assert msg.content == "test"


def test_sqlite_hello():
    """SQLiteTransport hello() sends to helloworld receiver."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        t.hello("Claude")
        msg = t.receive("helloworld")
        assert msg is not None
        assert "Claude #hello" in msg.content


# ---------------------------------------------------------------------------
# #address routing tests — receiver@context
# ---------------------------------------------------------------------------

def test_sqlite_address_routing():
    """claude@purdy and claude@cancelself are different inboxes."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        t.send("claude@cancelself", "claude@purdy", "hello from cancelself")
        t.send("claude@purdy", "claude@cancelself", "hello from purdy")

        msg = t.receive("claude@purdy")
        assert msg is not None
        assert msg.sender == "claude@cancelself"
        assert msg.content == "hello from cancelself"

        msg = t.receive("claude@cancelself")
        assert msg is not None
        assert msg.sender == "claude@purdy"
        assert msg.content == "hello from purdy"


def test_sqlite_address_vs_plain():
    """claude@purdy and plain claude are separate inboxes."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        t.send("A", "claude@purdy", "qualified msg")
        t.send("B", "claude", "unqualified msg")

        # Plain claude should not see qualified messages
        msg = t.receive("claude")
        assert msg is not None
        assert msg.content == "unqualified msg"

        # Qualified claude@purdy gets its own message
        msg = t.receive("claude@purdy")
        assert msg is not None
        assert msg.content == "qualified msg"


def test_sqlite_address_case_insensitive():
    """Address routing is case-insensitive."""
    with tempfile.TemporaryDirectory() as tmp:
        t = message_bus.SQLiteTransport(db_path=str(Path(tmp) / "test.db"))
        t.send("A", "Claude@Purdy", "test")
        msg = t.receive("claude@purdy")
        assert msg is not None
        assert msg.content == "test"


def test_file_address_routing():
    """FileTransport routes claude@purdy to a distinct inbox dir."""
    tmp = _use_tmp()
    try:
        message_bus.send("A", "claude@purdy", "qualified")
        message_bus.send("B", "claude", "unqualified")

        inbox_qualified = tmp / "claude@purdy" / "inbox"
        inbox_plain = tmp / "claude" / "inbox"
        assert inbox_qualified.exists()
        assert inbox_plain.exists()
        assert len(list(inbox_qualified.glob("msg-*.hw"))) == 1
        assert len(list(inbox_plain.glob("msg-*.hw"))) == 1
    finally:
        _restore()


def test_default_is_file_transport():
    """With no env var, _get_transport() returns FileTransport."""
    message_bus.reset_transport()
    transport = message_bus._get_transport()
    assert isinstance(transport, message_bus.FileTransport)


def test_set_transport_overrides_default():
    """set_transport() overrides the auto-detected transport."""
    _use_tmp()
    try:
        sentinel = message_bus.FileTransport()
        message_bus.set_transport(sentinel)
        assert message_bus._get_transport() is sentinel
    finally:
        _restore()


def test_reset_transport():
    """reset_transport() clears the cached transport."""
    _use_tmp()
    try:
        sentinel = message_bus.FileTransport()
        message_bus.set_transport(sentinel)
        message_bus.reset_transport()
        assert message_bus._get_transport() is not sentinel
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
    test_default_is_file_transport()
    test_set_transport_overrides_default()
    test_reset_transport()
    print("All message bus tests passed")
