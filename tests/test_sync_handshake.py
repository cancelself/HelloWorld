"""Tests for the Handshake Protocol and sync receiver."""

import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import Parser
from dispatcher import Dispatcher

def test_handshake_protocol():
    """Verify that HelloWorld.#observe triggers a sync (save)."""
    tmp = tempfile.mkdtemp()
    dispatcher = Dispatcher(vocab_dir=tmp)

    # 1. Modify a receiver
    dispatcher.registry["Guardian"].add_symbol("#new_fire")

    # 2. Trigger handshake
    results = dispatcher.dispatch_source("HelloWorld.#observe")
    assert "successful" in results[0]

    # 3. Verify persistence
    path = Path(tmp) / "guardian.vocab"
    assert path.exists()
    assert "#new_fire" in path.read_text()

def test_sync_act_handler():
    """Verify Sync messages are dispatched to message bus (LLM agent)."""
    dispatcher = Dispatcher()
    results = dispatcher.dispatch_source("Sync act: #all")
    assert len(results) == 1
    # Sync is not a bootstrapped receiver — gets a fallback message
    assert "Sync" in results[0]

if __name__ == "__main__":
    test_handshake_protocol()
    test_sync_act_handler()
    print("Handshake and Sync tests passed")
