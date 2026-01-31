"""Tests for the HelloWorld message bus."""

import sys
import tempfile
import threading
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from message_bus import MessageBus, Message


def _fresh_bus():
    """Create a message bus with a temp directory so tests start clean."""
    tmp = tempfile.mkdtemp()
    return MessageBus(base_dir=tmp), tmp


def test_send_creates_message_file():
    bus, tmp = _fresh_bus()
    msg_id = bus.send("@copilot", "@claude", "explain: #collision")
    inbox = Path(tmp) / "@claude" / "inbox"
    assert inbox.exists()
    files = list(inbox.glob("msg-*.hw"))
    assert len(files) == 1
    assert msg_id in files[0].stem


def test_send_with_thread_id():
    bus, _ = _fresh_bus()
    msg_id = bus.send("@copilot", "@claude", "explain: #collision",
                      thread_id="test-thread-123")
    assert msg_id.startswith("msg-")


def test_receive_returns_a_message():
    """Receive returns a message from inbox. Note: ordering is by filename
    (random UUID), not chronological. See message_bus.py receive() — this is
    a known limitation for @gemini to address."""
    bus, _ = _fresh_bus()
    bus.send("@copilot", "@claude", "first message", thread_id="t1")
    bus.send("@gemini", "@claude", "second message", thread_id="t2")
    msg = bus.receive("@claude")
    assert msg is not None
    assert msg.content in ("first message", "second message")


def test_receive_empty_inbox():
    bus, _ = _fresh_bus()
    msg = bus.receive("@nobody")
    assert msg is None


def test_respond_creates_outbox_file():
    bus, tmp = _fresh_bus()
    bus.respond("@claude", "thread-42", "The collision was productive.")
    outbox = Path(tmp) / "@claude" / "outbox"
    assert outbox.exists()
    files = list(outbox.glob("msg-*.hw"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "thread-42" in content
    assert "The collision was productive." in content


def test_send_and_respond_roundtrip():
    """Test the full send → respond → wait_for_response cycle."""
    bus, _ = _fresh_bus()
    thread_id = "roundtrip-test"

    bus.send("@copilot", "@claude", "@claude.#collision", thread_id=thread_id)

    # Simulate daemon responding in a background thread
    def daemon_respond():
        time.sleep(0.1)
        bus.respond("@claude", thread_id, "Collision is where HelloWorld lives.")

    t = threading.Thread(target=daemon_respond)
    t.start()

    response = bus.wait_for_response("@claude", thread_id, timeout=2.0)
    t.join()

    assert response is not None
    assert "Collision" in response


def test_wait_for_response_timeout():
    bus, _ = _fresh_bus()
    response = bus.wait_for_response("@claude", "nonexistent-thread", timeout=0.2)
    assert response is None


def test_clear_inbox():
    bus, tmp = _fresh_bus()
    bus.send("@copilot", "@claude", "msg1", thread_id="t1")
    bus.send("@gemini", "@claude", "msg2", thread_id="t2")
    inbox = Path(tmp) / "@claude" / "inbox"
    assert len(list(inbox.glob("msg-*.hw"))) == 2
    bus.clear_inbox("@claude")
    assert len(list(inbox.glob("msg-*.hw"))) == 0


def test_clear_outbox():
    bus, tmp = _fresh_bus()
    bus.respond("@claude", "t1", "response1")
    bus.respond("@claude", "t2", "response2")
    outbox = Path(tmp) / "@claude" / "outbox"
    assert len(list(outbox.glob("msg-*.hw"))) == 2
    bus.clear_outbox("@claude")
    assert len(list(outbox.glob("msg-*.hw"))) == 0


def test_message_with_context():
    bus, _ = _fresh_bus()
    bus.send("@copilot", "@claude", "explain: #sunyata",
             thread_id="ctx-test", context="Prior session had merge conflict")
    msg = bus.receive("@claude")
    assert msg is not None
    assert "explain: #sunyata" in msg.content


def test_parse_message_headers():
    bus, _ = _fresh_bus()
    bus.send("@target", "@guardian", "@guardian.#sunyata", thread_id="parse-test")
    msg = bus.receive("@guardian")
    assert msg.sender == "@target"
    assert msg.thread_id == "parse-test"


if __name__ == "__main__":
    test_send_creates_message_file()
    test_send_with_thread_id()
    test_receive_returns_a_message()
    test_receive_empty_inbox()
    test_respond_creates_outbox_file()
    test_send_and_respond_roundtrip()
    test_wait_for_response_timeout()
    test_clear_inbox()
    test_clear_outbox()
    test_message_with_context()
    test_parse_message_headers()
    print("All message bus tests passed")
