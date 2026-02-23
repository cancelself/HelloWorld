"""Tests for the HelloWorld memory bus — all subprocess calls mocked."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import message_bus
from memory_bus import (
    MemoryBus, MemoryEntry, MemoryIndex, MemoryResult,
    QMDNotFoundError, _parse_frontmatter, _slugify,
)

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


# --- _parse_frontmatter ---


def test_parse_frontmatter_basic():
    text = "---\ntitle: test\ncreated: 2026-01-01T00:00:00Z\n---\n\nBody here.\n"
    meta, content = _parse_frontmatter(text)
    assert meta["title"] == "test"
    assert meta["created"] == "2026-01-01T00:00:00Z"
    assert "Body here." in content


def test_parse_frontmatter_with_tags():
    text = "---\ntitle: tagged\ntags:\n  - alpha\n  - beta\n---\n\ncontent\n"
    meta, content = _parse_frontmatter(text)
    assert meta["tags"] == ["alpha", "beta"]
    assert "content" in content


def test_parse_frontmatter_no_frontmatter():
    text = "Just plain text, no frontmatter."
    meta, content = _parse_frontmatter(text)
    assert meta == {}
    assert content == text


def test_parse_frontmatter_empty():
    meta, content = _parse_frontmatter("")
    assert meta == {}


def test_parse_frontmatter_updated_field():
    text = "---\ntitle: t\ncreated: 2026-01-01\nupdated: 2026-02-01\n---\n\nbody\n"
    meta, content = _parse_frontmatter(text)
    assert meta["updated"] == "2026-02-01"


# --- MemoryIndex ---


def _make_hw_file(directory, name, title, created, tags=None, content="body"):
    """Helper to write a .hw file with frontmatter."""
    lines = ["---", f"title: {title}", f"created: {created}"]
    if tags:
        lines.append("tags:")
        for t in tags:
            lines.append(f"  - {t}")
    lines.append("---")
    lines.append("")
    lines.append(content)
    path = directory / name
    path.write_text("\n".join(lines) + "\n")
    return path


def test_memory_index_all():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "alpha", "2026-01-01")
        _make_hw_file(mem_dir, "b.hw", "beta", "2026-01-02")
        idx = MemoryIndex(mem_dir)
        assert len(idx.all()) == 2
    finally:
        _restore()


def test_memory_index_titles():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "alpha", "2026-01-01")
        _make_hw_file(mem_dir, "b.hw", "beta", "2026-01-02")
        idx = MemoryIndex(mem_dir)
        titles = idx.titles()
        assert "alpha" in titles
        assert "beta" in titles
    finally:
        _restore()


def test_memory_index_by_tag():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "alpha", "2026-01-01", tags=["cycle", "ooda-r"])
        _make_hw_file(mem_dir, "b.hw", "beta", "2026-01-02", tags=["agent"])
        _make_hw_file(mem_dir, "c.hw", "gamma", "2026-01-03", tags=["cycle", "agent"])
        idx = MemoryIndex(mem_dir)

        # Single tag
        cycle = idx.by_tag("cycle")
        assert len(cycle) == 2
        assert {e.title for e in cycle} == {"alpha", "gamma"}

        # AND match — both tags required
        both = idx.by_tag("cycle", "agent")
        assert len(both) == 1
        assert both[0].title == "gamma"
    finally:
        _restore()


def test_memory_index_by_title_substring():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "ciel-dialogue", "2026-01-01")
        _make_hw_file(mem_dir, "b.hw", "severith-notes", "2026-01-02")
        _make_hw_file(mem_dir, "c.hw", "ciel-update", "2026-01-03")
        idx = MemoryIndex(mem_dir)
        results = idx.by_title("ciel")
        assert len(results) == 2
        assert {e.title for e in results} == {"ciel-dialogue", "ciel-update"}
    finally:
        _restore()


def test_memory_index_by_title_glob():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "cycle-feb21", "2026-02-21")
        _make_hw_file(mem_dir, "b.hw", "cycle-feb22", "2026-02-22")
        _make_hw_file(mem_dir, "c.hw", "severith", "2026-01-01")
        idx = MemoryIndex(mem_dir)
        results = idx.by_title("cycle-*")
        assert len(results) == 2
    finally:
        _restore()


def test_memory_index_recent():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "oldest", "2026-01-01")
        _make_hw_file(mem_dir, "b.hw", "middle", "2026-01-15")
        _make_hw_file(mem_dir, "c.hw", "newest", "2026-02-01")
        idx = MemoryIndex(mem_dir)
        top2 = idx.recent(2)
        assert len(top2) == 2
        assert top2[0].title == "newest"
        assert top2[1].title == "middle"
    finally:
        _restore()


def test_memory_index_refresh():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.hw", "first", "2026-01-01")
        idx = MemoryIndex(mem_dir)
        assert len(idx.all()) == 1

        _make_hw_file(mem_dir, "b.hw", "second", "2026-01-02")
        # Still cached
        assert len(idx.all()) == 1
        # After refresh
        idx.refresh()
        assert len(idx.all()) == 2
    finally:
        _restore()


def test_memory_index_empty_dir():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("empty_agent")
        idx = MemoryIndex(mem.memory_dir)
        assert idx.all() == []
        assert idx.titles() == []
        assert idx.by_tag("anything") == []
        assert idx.recent() == []
    finally:
        _restore()


def test_memory_index_reads_md_files():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem_dir = mem.memory_dir
        _make_hw_file(mem_dir, "a.md", "markdown-note", "2026-01-01")
        idx = MemoryIndex(mem_dir)
        assert len(idx.all()) == 1
        assert idx.all()[0].title == "markdown-note"
    finally:
        _restore()


# --- MemoryBus.index property ---


def test_memory_bus_index_property():
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        mem.store("test content", title="index-test", tags=["test"])
        entries = mem.index.by_tag("test")
        assert len(entries) == 1
        assert entries[0].title == "index-test"
    finally:
        _restore()


def test_memory_bus_index_lazy():
    """index property should return the same MemoryIndex instance."""
    tmp = _use_tmp()
    try:
        mem = MemoryBus("idx_agent")
        idx1 = mem.index
        idx2 = mem.index
        assert idx1 is idx2
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
    test_parse_frontmatter_basic()
    test_parse_frontmatter_with_tags()
    test_parse_frontmatter_no_frontmatter()
    test_parse_frontmatter_empty()
    test_parse_frontmatter_updated_field()
    test_memory_index_all()
    test_memory_index_titles()
    test_memory_index_by_tag()
    test_memory_index_by_title_substring()
    test_memory_index_by_title_glob()
    test_memory_index_recent()
    test_memory_index_refresh()
    test_memory_index_empty_dir()
    test_memory_index_reads_md_files()
    test_memory_bus_index_property()
    test_memory_bus_index_lazy()
    print("All memory bus tests passed")
