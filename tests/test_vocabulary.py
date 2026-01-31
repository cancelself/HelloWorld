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

if __name__ == "__main__":
    test_save_load()
    test_load_nonexistent()
    print("✓ Vocabulary tests passed")
