"""Tests for hw_tools — MCP tool functions for vocabulary operations."""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from hw_tools import HwTools


VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestVocabularyLookup:
    def setup_method(self):
        self.tools = HwTools(vocab_dir=VOCAB_DIR)

    def test_native_symbol(self):
        result = self.tools.vocabulary_lookup("Agent", "#observe")
        assert result["outcome"] == "native"
        assert result["receiver"] == "Agent"

    def test_inherited_symbol(self):
        """Agent inherits from HelloWorld. #send is in HelloWorld."""
        result = self.tools.vocabulary_lookup("Agent", "#send")
        assert result["outcome"] == "inherited"

    def test_unknown_symbol(self):
        result = self.tools.vocabulary_lookup("Claude", "#nonexistent")
        assert result["outcome"] == "unknown"

    def test_unknown_receiver(self):
        result = self.tools.vocabulary_lookup("FakeReceiver", "#parse")
        assert result["outcome"] == "unknown"
        assert "not found" in result["context"]


class TestVocabularyList:
    def setup_method(self):
        self.tools = HwTools(vocab_dir=VOCAB_DIR)

    def test_lists_symbols(self):
        result = self.tools.vocabulary_list("Agent")
        assert result["receiver"] == "Agent"
        assert "#observe" in result["symbols"]
        assert result["count"] > 0

    def test_returns_sorted_symbols(self):
        result = self.tools.vocabulary_list("Agent")
        assert result["symbols"] == sorted(result["symbols"])

    def test_missing_receiver_returns_empty(self):
        result = self.tools.vocabulary_list("FakeReceiver")
        assert result["symbols"] == []
        assert result["count"] == 0


class TestVocabularySave:
    def test_saves_new_symbol(self):
        tmpdir = tempfile.mkdtemp()
        try:
            # Create a minimal .hw file
            path = os.path.join(tmpdir, "Test.hw")
            with open(path, "w") as f:
                f.write("# Test\n## existing\n- Already here\n")

            tools = HwTools(vocab_dir=tmpdir)
            result = tools.vocabulary_save("Test", "#newSym", "A description")
            assert result["status"] == "saved"

            # Verify it was written
            content = open(path).read()
            assert "## newSym" in content
        finally:
            shutil.rmtree(tmpdir)

    def test_skips_existing_symbol(self):
        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "Test.hw")
            with open(path, "w") as f:
                f.write("# Test\n## existing\n- Already here\n")

            tools = HwTools(vocab_dir=tmpdir)
            result = tools.vocabulary_save("Test", "#existing")
            assert result["status"] == "already_exists"
        finally:
            shutil.rmtree(tmpdir)


class TestCollisionLog:
    def test_logs_collision(self):
        tmpdir = tempfile.mkdtemp()
        try:
            tools = HwTools(vocab_dir=tmpdir)
            tools.log_file = os.path.join(tmpdir, "collisions.log")

            result = tools.collision_log("Codex", "#parse", "collision", "with Claude")
            assert result["logged"] is True
            assert "COLLISION" in result["entry"]
            assert "Codex" in result["entry"]
            assert "#parse" in result["entry"]

            # Verify file was written
            content = open(tools.log_file).read()
            assert "COLLISION" in content
        finally:
            shutil.rmtree(tmpdir)


class TestReceiversList:
    def test_lists_all_receivers(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        result = tools.receivers_list()
        names = [r["name"] for r in result["receivers"]]
        assert "HelloWorld" in names
        assert "Claude" in names
        assert "Copilot" in names

    def test_includes_symbol_counts(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        result = tools.receivers_list()
        for r in result["receivers"]:
            assert "symbol_count" in r
            assert r["symbol_count"] >= 0


class TestMemoryStore:
    def test_store_without_memory_returns_error(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        result = tools.memory_store("Claude", "test content")
        assert result["stored"] is False
        assert "not available" in result["error"]

    def test_store_with_memory(self):
        tmpdir = tempfile.mkdtemp()
        try:
            from unittest.mock import MagicMock
            mock_memory = MagicMock()
            mock_memory.store.return_value = Path(tmpdir) / "test.md"

            tools = HwTools(vocab_dir=VOCAB_DIR, memory=mock_memory)
            result = tools.memory_store("Claude", "test content", title="test", tags="a,b")
            assert result["stored"] is True
            assert "test.md" in result["path"]
            mock_memory.store.assert_called_once_with(
                "test content", title="test", tags=["a", "b"]
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_store_empty_tags_passes_none(self):
        from unittest.mock import MagicMock
        mock_memory = MagicMock()
        mock_memory.store.return_value = Path("/tmp/mem.md")

        tools = HwTools(vocab_dir=VOCAB_DIR, memory=mock_memory)
        tools.memory_store("Claude", "content", title="t", tags="")
        mock_memory.store.assert_called_once_with("content", title="t", tags=None)

    def test_store_empty_title_passes_none(self):
        from unittest.mock import MagicMock
        mock_memory = MagicMock()
        mock_memory.store.return_value = Path("/tmp/mem.md")

        tools = HwTools(vocab_dir=VOCAB_DIR, memory=mock_memory)
        tools.memory_store("Claude", "content", title="", tags="")
        mock_memory.store.assert_called_once_with("content", title=None, tags=None)


class TestMemoryRecall:
    def test_recall_without_memory_returns_empty(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        result = tools.memory_recall("Claude", "test query")
        assert result["found"] == 0
        assert result["results"] == []

    def test_recall_without_qmd_returns_note(self):
        from unittest.mock import MagicMock
        mock_memory = MagicMock()
        mock_memory.available.return_value = False

        tools = HwTools(vocab_dir=VOCAB_DIR, memory=mock_memory)
        result = tools.memory_recall("Claude", "test query")
        assert result["found"] == 0
        assert result["note"] == "QMD not installed"

    def test_recall_with_results(self):
        from unittest.mock import MagicMock
        from memory_bus import MemoryResult
        mock_memory = MagicMock()
        mock_memory.available.return_value = True
        mock_memory.recall.return_value = [
            MemoryResult(path="/a.md", score=0.9, snippet="hello", title="t1", docid="d1"),
        ]

        tools = HwTools(vocab_dir=VOCAB_DIR, memory=mock_memory)
        result = tools.memory_recall("Claude", "hello", n=3)
        assert result["found"] == 1
        assert result["results"][0]["title"] == "t1"
        assert result["results"][0]["snippet"] == "hello"
        assert result["results"][0]["score"] == 0.9
        mock_memory.recall.assert_called_once_with("hello", n=3)

    def test_recall_handles_exception(self):
        from unittest.mock import MagicMock
        mock_memory = MagicMock()
        mock_memory.available.return_value = True
        mock_memory.recall.side_effect = RuntimeError("qmd crashed")

        tools = HwTools(vocab_dir=VOCAB_DIR, memory=mock_memory)
        result = tools.memory_recall("Claude", "query")
        assert result["found"] == 0
        assert "qmd crashed" in result["error"]


class TestAllTools:
    def test_returns_nine_tools(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        all_tools = tools.all_tools()
        assert len(all_tools) == 9
        assert all(callable(t) for t in all_tools)

    def test_tool_names(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        names = [t.__name__ for t in tools.all_tools()]
        assert "memory_store" in names
        assert "memory_recall" in names
