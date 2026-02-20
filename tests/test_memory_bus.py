"""Tests for the HelloWorld memory bus — all subprocess calls mocked."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import message_bus
from memory_bus import MemoryBus, MemoryResult, QMDNotFoundError, _slugify

_original_base = message_bus.BASE_DIR


def _use_tmp():
    """Point message_bus.BASE_DIR at a temp directory."""
    tmp = Path(tempfile.mkdtemp())
    message_bus.BASE_DIR = tmp
    return tmp


def _restore():
    message_bus.BASE_DIR = _original_base


# --- store ---


def test_store_creates_markdown():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        path = mem.store("Agent prefers brevity.", title="style-note")
        assert path.exists()
        text = path.read_text()
        assert "---" in text
        assert "title: style-note" in text
        assert "created:" in text
        assert "Agent prefers brevity." in text
    finally:
        _restore()


def test_store_with_tags():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        path = mem.store("tagged content", title="tagged", tags=["social", "pref"])
        text = path.read_text()
        assert "tags:" in text
        assert "  - social" in text
        assert "  - pref" in text
    finally:
        _restore()


def test_store_generates_slug():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        path = mem.store("some content without a title")
        assert path.name.startswith("mem-")
        assert path.suffix == ".md"
    finally:
        _restore()


def test_store_handles_collision():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        p1 = mem.store("first", title="same-title")
        p2 = mem.store("second", title="same-title")
        assert p1 != p2
        assert p1.exists()
        assert p2.exists()
    finally:
        _restore()


# --- get ---


def test_get_reads_local_file():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        path = mem.store("hello memory", title="get-test")
        content = mem.get(path.name)
        assert "hello memory" in content
    finally:
        _restore()


# --- recall ---


def test_recall_with_mocked_qmd():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        mem._qmd_bin = "/usr/local/bin/qmd"
        mem._collection_registered = True

        qmd_output = json.dumps([
            {
                "path": "/tmp/memory/note.md",
                "score": 0.95,
                "snippet": "severith prefers short messages",
                "title": "severith-style",
                "docid": "doc-123",
            }
        ])

        mock_update = MagicMock(returncode=0)
        mock_search = MagicMock(returncode=0, stdout=qmd_output)

        with patch("memory_bus.subprocess.run", side_effect=[mock_update, mock_search]):
            results = mem.recall("how does severith communicate")

        assert len(results) == 1
        assert isinstance(results[0], MemoryResult)
        assert results[0].score == 0.95
        assert results[0].title == "severith-style"
        assert results[0].docid == "doc-123"
    finally:
        _restore()


def test_recall_empty_results():
    _use_tmp()
    try:
        mem = MemoryBus("claude")
        mem._qmd_bin = "/usr/local/bin/qmd"
        mem._collection_registered = True

        mock_update = MagicMock(returncode=0)
        mock_search = MagicMock(returncode=0, stdout="[]")

        with patch("memory_bus.subprocess.run", side_effect=[mock_update, mock_search]):
            results = mem.recall("nonexistent topic")

        assert results == []
    finally:
        _restore()


def test_recall_invalid_mode():
    mem = MemoryBus("claude")
    try:
        mem.recall("anything", mode="badmode")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "badmode" in str(e)


# --- available ---


def test_available_when_qmd_missing():
    mem = MemoryBus("claude")
    with patch("memory_bus.shutil.which", return_value=None):
        mem._qmd_bin = None  # Reset cache
        assert mem.available() is False


def test_available_when_qmd_present():
    mem = MemoryBus("claude")
    with patch("memory_bus.shutil.which", return_value="/usr/local/bin/qmd"):
        mem._qmd_bin = None  # Reset cache
        assert mem.available() is True


# --- slugify ---


def test_slugify():
    assert _slugify("Hello World!") == "hello-world"
    assert _slugify("  spaces  and   more  ") == "spaces-and-more"
    assert _slugify("special@#chars$%") == "specialchars"
    assert _slugify("already-slugged") == "already-slugged"


# --- per-agent isolation ---


def test_memory_dir_per_agent():
    tmp = _use_tmp()
    try:
        claude_mem = MemoryBus("claude")
        copilot_mem = MemoryBus("copilot")

        claude_mem.store("claude knows this", title="claude-fact")
        copilot_mem.store("copilot knows this", title="copilot-fact")

        assert (tmp / "claude" / "memory" / "claude-fact.md").exists()
        assert (tmp / "copilot" / "memory" / "copilot-fact.md").exists()

        # Each agent reads only its own memory
        assert "claude knows this" in claude_mem.get("claude-fact.md")
        assert "copilot knows this" in copilot_mem.get("copilot-fact.md")
    finally:
        _restore()


def test_memory_dir_created():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("newagent")
        mem_dir = mem.memory_dir
        assert mem_dir.exists()
        assert mem_dir == tmp / "newagent" / "memory"
    finally:
        _restore()


def test_at_prefix_stripped():
    """Agent names with @ prefix should be normalized."""
    tmp = _use_tmp()
    try:
        mem = MemoryBus("@Claude")
        mem.store("test", title="at-test")
        assert (tmp / "claude" / "memory" / "at-test.md").exists()
    finally:
        _restore()


if __name__ == "__main__":
    test_store_creates_markdown()
    test_store_with_tags()
    test_store_generates_slug()
    test_store_handles_collision()
    test_get_reads_local_file()
    test_recall_with_mocked_qmd()
    test_recall_empty_results()
    test_recall_invalid_mode()
    test_available_when_qmd_missing()
    test_available_when_qmd_present()
    test_slugify()
    test_memory_dir_per_agent()
    test_memory_dir_created()
    test_at_prefix_stripped()
    print("All memory bus tests passed")
