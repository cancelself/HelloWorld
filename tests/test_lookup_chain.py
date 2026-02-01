"""Tests for Phase 2: Symbol Lookup Chain (native/inherited/unknown)"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dispatcher import Dispatcher, LookupOutcome, LookupResult


def test_lookup_native_symbol():
    """Test lookup returns NATIVE for locally-held symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Guardian"]
    
    result = receiver.lookup("#fire")
    
    assert result.outcome == LookupOutcome.NATIVE
    assert result.symbol == "#fire"
    assert result.receiver_name == "Guardian"
    assert result.is_native()
    assert not result.is_inherited()
    assert not result.is_unknown()
    assert "#fire" in result.context["local_vocabulary"]


def test_lookup_inherited_symbol():
    """Phase 3: Test lookup returns DISCOVERABLE for global symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Guardian"]
    
    result = receiver.lookup("#Sunyata")
    
    # Phase 3: Now returns DISCOVERABLE instead of INHERITED
    assert result.outcome == LookupOutcome.DISCOVERABLE
    assert result.symbol == "#Sunyata"
    assert result.receiver_name == "Guardian"
    assert result.is_inherited()  # Backward compat alias
    assert result.is_discoverable()
    assert not result.is_native()
    assert not result.is_unknown()
    assert "global_definition" in result.context
    assert "emptiness" in result.context["global_definition"].lower()


def test_lookup_unknown_symbol():
    """Test lookup returns UNKNOWN for foreign symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Guardian"]
    
    result = receiver.lookup("#newSymbol")
    
    assert result.outcome == LookupOutcome.UNKNOWN
    assert result.symbol == "#newSymbol"
    assert result.receiver_name == "Guardian"
    assert result.is_unknown()
    assert not result.is_native()
    assert not result.is_inherited()
    assert "local_vocabulary" in result.context


def test_scoped_lookup_uses_new_API():
    """Phase 3: Test _handle_scoped_lookup discovers and activates symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    
    # Native symbol
    result = dispatcher.dispatch_source("Guardian #fire")
    assert len(result) == 1
    assert "native" in result[0]
    
    # Discoverable symbol — gets activated, becomes native
    guardian = dispatcher.registry["Guardian"]
    assert guardian.can_discover("#Sunyata")  # Before lookup
    result = dispatcher.dispatch_source("Guardian #Sunyata")
    assert len(result) == 1
    assert "native" in result[0]  # After discovery
    assert "#Sunyata" in guardian.vocabulary  # Now in local
    
    # Unknown symbol
    result = dispatcher.dispatch_source("Guardian #newSymbol")
    assert len(result) == 1
    assert "unknown" in result[0]


def test_unknown_symbol_logged():
    """Test unknown symbols are logged to collisions.log."""
    tmpdir = tempfile.mkdtemp()
    dispatcher = Dispatcher(vocab_dir=tmpdir)
    log_path = Path(dispatcher.log_file)
    
    # Clear log
    if log_path.exists():
        log_path.unlink()
    
    # Trigger unknown lookup
    dispatcher.dispatch_source("Guardian #unknownSymbol")
    
    # Verify log entry
    assert log_path.exists()
    log_content = log_path.read_text()
    assert "UNKNOWN" in log_content
    assert "Guardian" in log_content
    assert "#unknownSymbol" in log_content


def test_discovery_promotes_symbol():
    """Test that successful discovery promotes unknown symbol to local vocab.
    
    Note: This test requires LLM agent to be running, so it may not pass
    in CI. It demonstrates the intended behavior.
    """
    tmpdir = tempfile.mkdtemp()
    dispatcher = Dispatcher(vocab_dir=tmpdir)
    receiver = dispatcher.registry["Guardian"]
    
    # Initially unknown
    result = receiver.lookup("#newSymbol")
    assert result.is_unknown()
    assert "#newSymbol" not in receiver.local_vocabulary
    
    # After discovery (simulated), should be in local vocab
    # In real usage, _handle_unknown_symbol would call LLM and promote
    receiver.add_symbol("#newSymbol")
    
    result2 = receiver.lookup("#newSymbol")
    assert result2.is_native()
    assert "#newSymbol" in receiver.local_vocabulary


def test_lookup_preserves_context():
    """Phase 3: Test LookupResult preserves context for interpretation."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Claude"]
    
    # Native lookup includes local vocabulary
    native_result = receiver.lookup("#interpret")
    assert native_result.is_native()
    assert "#interpret" in native_result.context["local_vocabulary"]
    
    # Discoverable lookup includes global definition + Wikidata
    discoverable_result = receiver.lookup("#Love")
    assert discoverable_result.is_discoverable()
    assert discoverable_result.is_inherited()  # Backward compat
    assert "global_definition" in discoverable_result.context
    assert "wikidata_url" in discoverable_result.context
    
    # Unknown lookup includes local vocabulary for research context
    unknown_result = receiver.lookup("#brandNewSymbol")
    assert unknown_result.is_unknown()
    assert "local_vocabulary" in unknown_result.context


if __name__ == "__main__":
    test_lookup_native_symbol()
    test_lookup_inherited_symbol()
    test_lookup_unknown_symbol()
    test_scoped_lookup_uses_new_api()
    test_unknown_symbol_logged()
    test_discovery_promotes_symbol()
    test_lookup_preserves_context()
    print("✅ All Phase 2 lookup tests passed")
