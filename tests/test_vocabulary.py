"""Tests for the Vocabulary Manager (.hw format)."""

import os
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vocabulary import VocabularyManager

def test_save_load():
    test_dir = "temp_vocab_test"
    vm = VocabularyManager(test_dir)

    receiver = "TestBot"
    symbols = {"#hello", "#world", "#test"}

    vm.save(receiver, symbols)

    loaded = vm.load(receiver)
    assert loaded == symbols

    # Cleanup
    shutil.rmtree(test_dir)

def test_load_nonexistent():
    test_dir = "temp_vocab_test_2"
    vm = VocabularyManager(test_dir)
    assert vm.load("Nothing") is None
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_receiver_path_preserves_case():
    """Verify that receiver names are case-preserved in filenames."""
    test_dir = "temp_vocab_test_case"
    vm = VocabularyManager(test_dir)

    vm.save("HelloWorld", {"#Sunyata", "#Love"})
    path = os.path.join(test_dir, "HelloWorld.hw")
    assert os.path.exists(path)

    loaded = vm.load("HelloWorld")
    assert loaded == {"#Sunyata", "#Love"}

    shutil.rmtree(test_dir)

def test_save_appends_new_symbols():
    """Verify that save preserves existing content and appends new symbols."""
    test_dir = "temp_vocab_test_append"
    vm = VocabularyManager(test_dir)

    # Initial save
    vm.save("Agent", {"#hello", "#world"})

    # Save with additional symbol
    vm.save("Agent", {"#hello", "#world", "#new"})

    # Load and verify all symbols present
    loaded = vm.load("Agent")
    assert loaded == {"#hello", "#world", "#new"}

    # Verify the file has correct .hw format
    path = os.path.join(test_dir, "Agent.hw")
    content = open(path).read()
    assert "# Agent" in content
    assert "## hello" in content
    assert "## world" in content
    assert "## new" in content
    assert "(learned through dialogue)" in content

    shutil.rmtree(test_dir)

def test_save_preserves_descriptions():
    """Verify that appending new symbols doesn't destroy existing descriptions."""
    test_dir = "temp_vocab_test_preserve"
    os.makedirs(test_dir, exist_ok=True)
    vm = VocabularyManager(test_dir)

    # Write a .hw file with descriptions
    hw_path = os.path.join(test_dir, "Agent.hw")
    with open(hw_path, "w") as f:
        f.write("# Agent\n")
        f.write("- A test agent.\n")
        f.write("## alpha\n")
        f.write("- The first symbol.\n")
        f.write("## beta\n")
        f.write("- The second symbol.\n")

    # Save with existing + new symbol
    vm.save("Agent", {"#alpha", "#beta", "#gamma"})

    content = open(hw_path).read()
    # Original descriptions preserved
    assert "- A test agent." in content
    assert "- The first symbol." in content
    assert "- The second symbol." in content
    # New symbol appended
    assert "## gamma" in content

    shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_save_load()
    test_load_nonexistent()
    test_receiver_path_preserves_case()
    test_save_appends_new_symbols()
    test_save_preserves_descriptions()
    print("Vocabulary tests passed")
