"""Tests for the Vocabulary Manager."""

import os
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vocabulary import VocabularyManager

def test_save_load():
    test_dir = "temp_vocab_test"
    vm = VocabularyManager(test_dir)
    
    receiver = "@test_bot"
    symbols = {"#hello", "#world", "#test"}
    
    vm.save(receiver, symbols)
    
    loaded = vm.load(receiver)
    assert loaded == symbols
    
    # Cleanup
    shutil.rmtree(test_dir)

def test_load_nonexistent():
    test_dir = "temp_vocab_test_2"
    vm = VocabularyManager(test_dir)
    assert vm.load("@nothing") is None
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_root_receiver_path():
    """Verify that @ saves to root.vocab, not .vocab."""
    test_dir = "temp_vocab_test_root"
    vm = VocabularyManager(test_dir)

    vm.save("@", {"#sunyata", "#love"})
    path = os.path.join(test_dir, "root.vocab")
    assert os.path.exists(path)
    # The hidden file .vocab should NOT be created
    assert not os.path.exists(os.path.join(test_dir, ".vocab"))

    loaded = vm.load("@")
    assert loaded == {"#sunyata", "#love"}

    shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_save_load()
    test_load_nonexistent()
    test_root_receiver_path()
    print("✓ Vocabulary tests passed")
