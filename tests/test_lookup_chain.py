"""Tests for symbol lookup via prototypal inheritance chain."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dispatcher import Dispatcher, LookupOutcome, LookupResult
from conftest import hw_symbols, any_native_symbol, exclusive_native_symbol


def test_lookup_native_symbol():
    """Test lookup returns NATIVE for locally-held symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Agent"]
    native_sym = any_native_symbol("Agent")

    result = receiver.lookup(native_sym)

    assert result.outcome == LookupOutcome.NATIVE
    assert result.symbol == native_sym
    assert result.receiver_name == "Agent"
    assert result.is_native()
    assert not result.is_inherited()
    assert not result.is_unknown()
    assert native_sym in result.context["local_vocabulary"]


def test_lookup_inherited_symbol():
    """Test lookup returns INHERITED for symbols found in parent chain."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Codex"]

    # #synthesize is in Object, inherited via Codex → Agent → Object
    result = receiver.lookup("#synthesize")

    assert result.outcome == LookupOutcome.INHERITED
    assert result.symbol == "#synthesize"
    assert result.receiver_name == "Codex"
    assert result.is_inherited()
    assert result.is_inherited()
    assert not result.is_native()
    assert not result.is_unknown()
    assert "defined_in" in result.context
    assert result.context["defined_in"] == "Object"


def test_lookup_inherited_from_agent():
    """Test lookup returns INHERITED with correct ancestor for Agent symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Codex"]

    # #observe is in Agent.hw, inherited by Codex → Agent
    result = receiver.lookup("#observe")

    assert result.outcome == LookupOutcome.INHERITED
    assert result.context["defined_in"] == "Agent"


def test_lookup_inherited_from_object():
    """Test lookup returns INHERITED with correct ancestor for Object symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Claude"]

    # #send is in Object.hw, inherited by Claude → Agent → Object
    result = receiver.lookup("#send")

    assert result.outcome == LookupOutcome.INHERITED
    assert result.context["defined_in"] == "Object"


def test_lookup_unknown_symbol():
    """Test lookup returns UNKNOWN for symbols not in local or parent chain."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Codex"]

    result = receiver.lookup("#newSymbol")

    assert result.outcome == LookupOutcome.UNKNOWN
    assert result.symbol == "#newSymbol"
    assert result.receiver_name == "Codex"
    assert result.is_unknown()
    assert not result.is_native()
    assert not result.is_inherited()
    assert "local_vocabulary" in result.context


def test_scoped_lookup_uses_parent_chain():
    """Test _handle_scoped_lookup returns inherited for parent chain symbols."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    native_sym = any_native_symbol("Agent")

    # Native symbol on the receiver that owns it
    result = dispatcher.dispatch_source(f"Agent {native_sym}")
    assert len(result) == 1
    assert "native" in result[0]

    # Inherited symbol — stays inherited, no promotion
    codex = dispatcher.registry["Codex"]
    assert codex.is_inherited("#synthesize")
    result = dispatcher.dispatch_source("Codex #synthesize")
    assert len(result) == 1
    assert "inherited" in result[0]
    assert "#synthesize" not in codex.vocabulary  # Not promoted to local

    # Unknown symbol
    result = dispatcher.dispatch_source("Codex #newSymbol")
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
    dispatcher.dispatch_source("Codex #unknownSymbol")

    # Verify log entry
    assert log_path.exists()
    log_content = log_path.read_text()
    assert "UNKNOWN" in log_content
    assert "Codex" in log_content
    assert "#unknownSymbol" in log_content


def test_manual_symbol_addition():
    """Test that manually added symbols become native."""
    tmpdir = tempfile.mkdtemp()
    dispatcher = Dispatcher(vocab_dir=tmpdir)
    receiver = dispatcher.registry["Codex"]

    # Initially unknown
    result = receiver.lookup("#newSymbol")
    assert result.is_unknown()
    assert "#newSymbol" not in receiver.local_vocabulary

    # After manual addition, should be native
    receiver.add_symbol("#newSymbol")

    result2 = receiver.lookup("#newSymbol")
    assert result2.is_native()
    assert "#newSymbol" in receiver.local_vocabulary


def test_lookup_preserves_context():
    """Test LookupResult preserves context for interpretation."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    receiver = dispatcher.registry["Agent"]
    native_sym = any_native_symbol("Agent")

    # Native lookup includes local vocabulary
    native_result = receiver.lookup(native_sym)
    assert native_result.is_native()
    assert native_sym in native_result.context["local_vocabulary"]

    # Inherited lookup includes defined_in ancestor
    inherited_result = receiver.lookup("#synthesize")
    assert inherited_result.is_inherited()
    assert "defined_in" in inherited_result.context
    assert inherited_result.context["defined_in"] == "Object"

    # Unknown lookup includes local vocabulary for research context
    unknown_result = receiver.lookup("#brandNewSymbol")
    assert unknown_result.is_unknown()
    assert "local_vocabulary" in unknown_result.context


def test_receiver_chain():
    """Test chain() returns the full inheritance path."""
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())

    assert dispatcher.registry["Claude"].chain() == ["Claude", "Agent", "Object", "HelloWorld"]
    assert dispatcher.registry["Codex"].chain() == ["Codex", "Agent", "Object", "HelloWorld"]
    assert dispatcher.registry["Object"].chain() == ["Object", "HelloWorld"]
    assert dispatcher.registry["HelloWorld"].chain() == ["HelloWorld"]


if __name__ == "__main__":
    test_lookup_native_symbol()
    test_lookup_inherited_symbol()
    test_lookup_inherited_from_agent()
    test_lookup_inherited_from_object()
    test_lookup_unknown_symbol()
    test_scoped_lookup_uses_parent_chain()
    test_unknown_symbol_logged()
    test_manual_symbol_addition()
    test_lookup_preserves_context()
    test_receiver_chain()
    print("All lookup chain tests passed")
