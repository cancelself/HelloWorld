"""Tests for receive and run — Agent receive processes one message,
HelloWorld run: Agent loops until inbox is empty."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import message_bus
from dispatcher import Dispatcher
from conftest import hw_symbols


def _drain_inbox(agent: str):
    """Consume all pending messages for an agent so tests start clean."""
    while message_bus.receive(agent) is not None:
        pass


def _fresh_dispatcher():
    """Create a dispatcher with a temp vocab dir and message bus redirected."""
    tmp = tempfile.mkdtemp()
    message_bus.BASE_DIR = Path(tmp)
    d = Dispatcher(vocab_dir=tmp)
    # Drain any messages generated during bootstrap
    for agent in ["Claude", "Copilot", "Gemini", "Codex", "Scribe", "HelloWorld"]:
        _drain_inbox(agent)
    return d


# --- Agent receive (one message) ---

def test_receive_empty_inbox():
    """Empty inbox returns 'Inbox empty'."""
    d = _fresh_dispatcher()
    results = d.dispatch_source("Claude receive")
    assert len(results) == 1
    assert "Inbox empty" in results[0]


def test_receive_processes_one_message():
    """One message consumed, response sent back to sender."""
    d = _fresh_dispatcher()
    message_bus.send("Copilot", "Claude", "status update on parser changes")
    results = d.dispatch_source("Claude receive")
    output = results[0]
    assert "Copilot" in output
    assert "#observe" in output
    assert "#orient" in output
    assert "#act" in output
    # Response sent back
    reply = message_bus.receive("Copilot")
    assert reply is not None
    assert reply.sender == "Claude"


def test_receive_leaves_remaining_messages():
    """receive processes only one message, rest stay in inbox."""
    d = _fresh_dispatcher()
    message_bus.send("Copilot", "Claude", "first message")
    message_bus.send("Gemini", "Claude", "second message")
    d.dispatch_source("Claude receive")
    # Second message still in inbox
    remaining = message_bus.receive("Claude")
    assert remaining is not None
    assert remaining.sender == "Gemini"


def test_receive_skips_self_messages():
    """Self-messages are skipped."""
    d = _fresh_dispatcher()
    message_bus.send("Claude", "Claude", "talking to myself")
    results = d.dispatch_source("Claude receive")
    assert "Skipped self-message" in results[0]


def test_receive_with_llm():
    """LLM path produces interpretation."""
    d = _fresh_dispatcher()
    mock_llm = MagicMock()
    mock_llm.call.return_value = "I interpret this through my vocabulary of design."
    d.llm = mock_llm
    message_bus.send("Copilot", "Claude", "what does #parse mean to you?")
    results = d.dispatch_source("Claude receive")
    output = results[0]
    assert "I interpret this through my vocabulary of design" in output
    assert mock_llm.call.called


def test_receive_structural_fallback():
    """No LLM — Python runtime interprets through vocabulary."""
    d = _fresh_dispatcher()
    d.llm = None
    message_bus.send("Gemini", "Claude", "check #observe and #Entropy")
    results = d.dispatch_source("Claude receive")
    output = results[0]
    assert "Symbol analysis" in output
    assert "#observe" in output


def test_receive_does_not_mutate_vocabulary():
    """Vocab unchanged after receive."""
    d = _fresh_dispatcher()
    vocab_before = d.registry["Claude"].local_vocabulary.copy()
    message_bus.send("Copilot", "Claude", "new concept #Wormhole")
    d.dispatch_source("Claude receive")
    vocab_after = d.registry["Claude"].local_vocabulary.copy()
    assert vocab_before == vocab_after


# --- HelloWorld run: Agent (the loop) ---

def test_run_empty_inbox():
    """Empty inbox returns nothing to receive."""
    d = _fresh_dispatcher()
    results = d.dispatch_source("HelloWorld run: Claude")
    assert len(results) == 1
    assert "Nothing to receive" in results[0]


def test_run_processes_all_messages():
    """All messages processed, all senders mentioned."""
    d = _fresh_dispatcher()
    message_bus.send("Copilot", "Claude", "parser refactored")
    message_bus.send("Gemini", "Claude", "state persisted")
    message_bus.send("Codex", "Claude", "execution semantics clarified")
    results = d.dispatch_source("HelloWorld run: Claude")
    output = results[0]
    assert "Copilot" in output
    assert "Gemini" in output
    assert "Codex" in output
    assert "Processed 3 message(s)" in output


def test_run_works_for_any_agent():
    """run works for Copilot, not just Claude."""
    d = _fresh_dispatcher()
    message_bus.send("Claude", "Copilot", "design update")
    results = d.dispatch_source("HelloWorld run: Copilot")
    output = results[0]
    assert "Copilot" in output
    assert "Claude" in output
    assert "Processed 1 message(s)" in output


# --- Vocabulary: #send, #receive, #run on HelloWorld ---

def test_send_receive_run_on_helloworld():
    """HelloWorld's vocabulary contains all symbols from HelloWorld.hw."""
    d = _fresh_dispatcher()
    hw_vocab = d.registry["HelloWorld"].local_vocabulary
    assert hw_symbols("HelloWorld") <= hw_vocab


def test_receive_inherited_by_agents():
    """#receive is inherited from HelloWorld for all agents."""
    d = _fresh_dispatcher()
    for agent in ["Claude", "Copilot", "Gemini", "Codex"]:
        receiver = d.registry[agent]
        assert receiver.has_symbol("#receive"), f"{agent} should inherit #receive"


# --- HelloWorld run (all agents) ---

def test_run_all_empty():
    """HelloWorld run with all inboxes empty."""
    d = _fresh_dispatcher()
    results = d.dispatch_source("HelloWorld run")
    assert "All inboxes empty" in results[0]


def test_run_all_processes_multiple_agents():
    """HelloWorld run processes messages across agents."""
    d = _fresh_dispatcher()
    message_bus.send("Gemini", "Claude", "state update")
    message_bus.send("Claude", "Copilot", "design spec")
    results = d.dispatch_source("HelloWorld run")
    output = results[0]
    assert "Claude" in output
    assert "Copilot" in output
    assert "across all agents" in output


def test_run_helloworld_symbol_means_all():
    """HelloWorld run: HelloWorld runs the root receiver."""
    d = _fresh_dispatcher()
    results = d.dispatch_source("HelloWorld run: HelloWorld")
    # Running HelloWorld receiver specifically, not all agents
    assert "Inbox empty" in results[0]


# --- send:to: → message bus integration ---

def test_send_to_queues_on_bus():
    """send:to: writes to the target's inbox so run: can drain it."""
    d = _fresh_dispatcher()
    d.dispatch_source("HelloWorld send: #hello to: Copilot")
    results = d.dispatch_source("HelloWorld run: Copilot")
    output = results[0]
    assert "HelloWorld" in output
    assert "#hello" in output or "hello" in output
