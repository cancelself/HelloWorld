"""Tests for hw_reader — parser-free .hw file reader."""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from hw_reader import HwSymbol, HwReceiver, read_hw_file, read_hw_directory, save_hw_symbol


# Use the real vocabularies/ directory for integration tests
VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestHwSymbol:
    def test_description_combines_lines(self):
        sym = HwSymbol(name="#parse", raw_name="parse", descriptions=["Line 1.", "Line 2."])
        assert sym.description == "Line 1. Line 2."

    def test_description_none_when_empty(self):
        sym = HwSymbol(name="#parse", raw_name="parse")
        assert sym.description is None


class TestReadHwFile:
    def test_extracts_receiver_name(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "HelloWorld.hw"))
        assert receiver is not None
        assert receiver.name == "HelloWorld"

    def test_extracts_parent(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "Claude.hw"))
        assert receiver is not None
        assert receiver.parent == "Agent"

    def test_no_parent_when_absent(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "HelloWorld.hw"))
        assert receiver is not None
        assert receiver.parent is None

    def test_extracts_identity(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "Claude.hw"))
        assert receiver is not None
        assert receiver.identity is not None
        assert "HelloWorld" in receiver.identity

    def test_extracts_symbols(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "Agent.hw"))
        assert receiver is not None
        assert "#observe" in receiver.symbols
        assert "#act" in receiver.symbols
        assert "#decide" in receiver.symbols

    def test_symbol_has_description(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "Agent.hw"))
        assert receiver is not None
        desc = receiver.symbol_description("#observe")
        assert desc is not None
        assert "Perceiving" in desc

    def test_vocabulary_returns_sorted_names(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "Agent.hw"))
        assert receiver is not None
        vocab = receiver.vocabulary
        assert vocab == sorted(vocab)
        assert all(s.startswith("#") for s in vocab)

    def test_handles_bare_hash_symbol(self):
        receiver = read_hw_file(os.path.join(VOCAB_DIR, "HelloWorld.hw"))
        assert receiver is not None
        assert "#" in receiver.symbols

    def test_skips_double_quote_comments(self):
        """Double-quoted text is a Smalltalk-style comment and should be skipped."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.hw', delete=False)
        tmp.write('# TestReceiver\n')
        tmp.write('" This is a comment "\n')
        tmp.write('- Identity line\n')
        tmp.write('## observe\n')
        tmp.write('- Watch things\n')
        tmp.close()
        try:
            receiver = read_hw_file(tmp.name)
            assert receiver is not None
            assert receiver.name == "TestReceiver"
            assert "Identity line" in receiver.identity
            assert "#observe" in receiver.symbols
        finally:
            os.unlink(tmp.name)

    def test_returns_none_for_missing_file(self):
        result = read_hw_file("/nonexistent/path/fake.hw")
        assert result is None

    def test_returns_none_for_empty_file(self):
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.hw', delete=False)
        tmp.write('')
        tmp.close()
        try:
            result = read_hw_file(tmp.name)
            assert result is None
        finally:
            os.unlink(tmp.name)

    def test_helloworld_symbols_match_vocabulary_manager(self):
        """Verify hw_reader produces the same symbol set as VocabularyManager."""
        from vocabulary import VocabularyManager
        vm = VocabularyManager(VOCAB_DIR)

        receiver = read_hw_file(os.path.join(VOCAB_DIR, "HelloWorld.hw"))
        vm_symbols = vm.load("HelloWorld")

        assert receiver is not None
        assert vm_symbols is not None
        assert set(receiver.symbols.keys()) == vm_symbols


class TestReadHwDirectory:
    def test_reads_all_hw_files(self):
        receivers = read_hw_directory(VOCAB_DIR)
        assert "HelloWorld" in receivers
        assert "Claude" in receivers
        assert "Copilot" in receivers
        assert "Gemini" in receivers
        assert "Codex" in receivers

    def test_returns_empty_for_missing_dir(self):
        receivers = read_hw_directory("/nonexistent/dir")
        assert receivers == {}

    def test_returns_empty_for_dir_without_hw_files(self):
        tmpdir = tempfile.mkdtemp()
        try:
            receivers = read_hw_directory(tmpdir)
            assert receivers == {}
        finally:
            shutil.rmtree(tmpdir)


class TestSaveHwSymbol:
    def test_appends_symbol_with_description(self):
        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "Test.hw")
            with open(path, "w") as f:
                f.write("# Test\n")
                f.write("## existing\n")
                f.write("- Already here\n")

            save_hw_symbol(path, "#newSymbol", "A new symbol")

            content = open(path).read()
            assert "## newSymbol" in content
            assert "- A new symbol" in content
        finally:
            shutil.rmtree(tmpdir)

    def test_appends_symbol_without_description(self):
        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "Test.hw")
            with open(path, "w") as f:
                f.write("# Test\n")

            save_hw_symbol(path, "#learned")

            content = open(path).read()
            assert "## learned" in content
            assert "(learned through dialogue)" in content
        finally:
            shutil.rmtree(tmpdir)

    def test_appends_bare_hash_symbol(self):
        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "Test.hw")
            with open(path, "w") as f:
                f.write("# Test\n")

            save_hw_symbol(path, "#", "The symbol primitive")

            content = open(path).read()
            assert "## #\n" in content
            assert "- The symbol primitive" in content
        finally:
            shutil.rmtree(tmpdir)
