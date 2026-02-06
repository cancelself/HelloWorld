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


class TestAllTools:
    def test_returns_seven_tools(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        all_tools = tools.all_tools()
        assert len(all_tools) == 7
        assert all(callable(t) for t in all_tools)
