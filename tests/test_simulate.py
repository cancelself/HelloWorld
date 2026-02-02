"""Tests for the simulate command — Agent simulate processes inbox through identity."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import message_bus
from dispatcher import Dispatcher


def _fresh_dispatcher():
    """Create a dispatcher with a temp vocab dir and message bus disabled."""
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    tmp = tempfile.mkdtemp()
    return Dispatcher(vocab_dir=tmp)


def _drain_inbox(agent: str):
    """Consume all pending messages for an agent so tests start clean."""
    while message_bus.receive(agent) is not None:
        pass


def _fresh_dispatcher_with_bus():
    """Create a dispatcher with message bus enabled (for inbox tests)."""
    os.environ.pop("HELLOWORLD_DISABLE_MESSAGE_BUS", None)
    tmp = tempfile.mkdtemp()
    d = Dispatcher(vocab_dir=tmp)
    # Drain any messages generated during bootstrap
    for agent in ["Claude", "Copilot", "Gemini", "Codex", "Scribe", "HelloWorld"]:
        _drain_inbox(agent)
    return d


def test_simulate_empty_inbox():
    """Empty inbox returns 'Nothing to simulate'."""
    d = _fresh_dispatcher_with_bus()
    results = d.dispatch_source("Claude simulate")
    assert len(results) == 1
    assert "Nothing to simulate" in results[0]
    assert "#observe" in results[0]


def test_simulate_processes_single_message():
    """One message consumed, response sent back to sender."""
    d = _fresh_dispatcher_with_bus()
    message_bus.send("Copilot", "Claude", "status update on parser changes")
    results = d.dispatch_source("Claude simulate")
    assert len(results) == 1
    output = results[0]
    assert "Copilot" in output
    assert "#observe" in output
    assert "#orient" in output
    assert "#act" in output
    assert "Processed 1 message(s)" in output
    # Response should have been sent back to Copilot
    reply = message_bus.receive("Copilot")
    assert reply is not None
    assert reply.sender == "Claude"


def test_simulate_processes_all_messages():
    """Multiple messages all processed, all senders mentioned."""
    d = _fresh_dispatcher_with_bus()
    message_bus.send("Copilot", "Claude", "parser refactored")
    message_bus.send("Gemini", "Claude", "state persisted")
    message_bus.send("Codex", "Claude", "execution semantics clarified")
    results = d.dispatch_source("Claude simulate")
    output = results[0]
    assert "Copilot" in output
    assert "Gemini" in output
    assert "Codex" in output
    assert "Processed 3 message(s)" in output


def test_simulate_works_for_any_agent():
    """simulate works for Copilot, not just Claude."""
    d = _fresh_dispatcher_with_bus()
    message_bus.send("Claude", "Copilot", "design update")
    results = d.dispatch_source("Copilot simulate")
    output = results[0]
    assert "Copilot" in output
    assert "Claude" in output
    assert "Processed 1 message(s)" in output


def test_simulate_with_llm():
    """LLM path produces interpretation text in the output."""
    d = _fresh_dispatcher_with_bus()
    mock_llm = MagicMock()
    mock_llm.call.return_value = "I interpret this through my vocabulary of design."
    d.llm = mock_llm
    message_bus.send("Copilot", "Claude", "what does #parse mean to you?")
    results = d.dispatch_source("Claude simulate")
    output = results[0]
    assert "I interpret this through my vocabulary of design" in output
    assert mock_llm.call.called


def test_simulate_structural_fallback():
    """No LLM available — Python runtime interprets through vocabulary."""
    d = _fresh_dispatcher_with_bus()
    d.llm = None
    message_bus.send("Gemini", "Claude", "check #observe and #Entropy")
    results = d.dispatch_source("Claude simulate")
    output = results[0]
    # Structural fallback does real symbol lookup, not a generic punt
    assert "Symbol analysis" in output
    assert "#observe" in output
    assert "#Entropy" in output


def test_simulate_structural_fallback_no_symbols():
    """No LLM, no symbols in message — identity-framed acknowledgment."""
    d = _fresh_dispatcher_with_bus()
    d.llm = None
    message_bus.send("Gemini", "Claude", "hello, how are things?")
    results = d.dispatch_source("Claude simulate")
    output = results[0]
    assert "Claude" in output
    assert "message acknowledged" in output


def test_simulate_does_not_mutate_vocabulary():
    """Vocab unchanged after simulate — simulate is read-only."""
    d = _fresh_dispatcher_with_bus()
    vocab_before = d.registry["Claude"].local_vocabulary.copy()
    message_bus.send("Copilot", "Claude", "new concept #Wormhole")
    d.dispatch_source("Claude simulate")
    vocab_after = d.registry["Claude"].local_vocabulary.copy()
    assert vocab_before == vocab_after


def test_simulate_skips_self_messages():
    """Self-messages don't generate a reply (avoids loops)."""
    d = _fresh_dispatcher_with_bus()
    message_bus.send("Claude", "Claude", "talking to myself")
    results = d.dispatch_source("Claude simulate")
    output = results[0]
    assert "Nothing to simulate" in output
    # No reply should be sent back to Claude
    reply = message_bus.receive("Claude")
    assert reply is None


def test_simulate_symbol_is_inherited():
    """#simulate is inherited from Agent for all agent receivers."""
    d = _fresh_dispatcher()
    for agent in ["Claude", "Copilot", "Gemini", "Codex"]:
        receiver = d.registry[agent]
        assert receiver.has_symbol("#simulate"), f"{agent} should inherit #simulate"
