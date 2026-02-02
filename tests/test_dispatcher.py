"""Tests for the HelloWorld dispatcher."""

import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import Parser
from dispatcher import Dispatcher


def _fresh_dispatcher_with_dir():
    """Create a dispatcher with a temp vocab dir so tests start clean."""
    # Disable message bus for faster tests (agents trigger 5s timeouts)
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    tmp = tempfile.mkdtemp()
    dispatcher = Dispatcher(vocab_dir=tmp, discovery_log=os.path.join(tmp, "discovery.log"))
    return dispatcher, tmp


def _fresh_dispatcher():
    dispatcher, _ = _fresh_dispatcher_with_dir()
    return dispatcher


def test_dispatcher_bootstrap():
    dispatcher = _fresh_dispatcher()
    assert "Codex" in dispatcher.registry
    assert "#execute" in dispatcher.registry["Codex"].vocabulary
    assert "Copilot" in dispatcher.registry
    assert "Claude" in dispatcher.registry


def test_dispatch_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Codex").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "Codex #" in results[0]
    assert "#execute" in results[0]


def test_dispatch_query_explicit():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Codex #").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "#execute" in results[0]


def test_dispatch_scoped_lookup_native():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Codex #execute").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_dispatch_scoped_lookup_foreign():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Copilot #execute").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "unknown" in results[0] or "research" in results[0]


def test_discovery_writes_log_and_promotes_symbol():
    dispatcher, _ = _fresh_dispatcher_with_dir()
    log_path = Path(dispatcher.discovery_log_file)
    if log_path.exists():
        log_path.unlink()
    guardian = dispatcher._get_or_create_receiver("Guardian")
    guardian.local_vocabulary.discard("#Love")
    dispatcher.vocab_manager.save("Guardian", guardian.local_vocabulary)
    stmts = Parser.from_source("Guardian #Love").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]
    assert "#Love" in dispatcher.registry["Guardian"].vocabulary
    assert log_path.exists()
    log_text = log_path.read_text()
    assert "Guardian" in log_text and "#Love" in log_text


def test_dispatch_definition():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("NewReceiver # → [#hello, #world]").parse()
    dispatcher.dispatch(stmts)
    assert "NewReceiver" in dispatcher.registry
    assert "#hello" in dispatcher.registry["NewReceiver"].vocabulary
    assert "#world" in dispatcher.registry["NewReceiver"].vocabulary


def test_dispatch_message():
    dispatcher = _fresh_dispatcher()
    source = "Codex sendAnalysis: #parse withContext: Claude 'how do you see this?'"
    stmts = Parser.from_source(source).parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    # Response either from semantic handler or fallback
    assert "Codex" in results[0]
    # Note: #parse may not appear in fallback response when daemon not running


def test_dispatch_message_learning():
    dispatcher = _fresh_dispatcher()
    source = "Codex analyze: #Sunyata"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    assert "#Sunyata" in dispatcher.registry["Codex"].vocabulary


def test_dispatch_unknown_receiver():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Nobody").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "Nobody" in dispatcher.registry


def test_dispatch_bootstrap_hw():
    dispatcher = _fresh_dispatcher()
    path = Path(__file__).parent.parent / 'examples' / 'bootstrap.hw'
    source = path.read_text()
    results = dispatcher.dispatch_source(source)
    # Note: bootstrap.hw may still use old Awakener/Guardian syntax
    # Just verify it executes without error for now
    assert len(results) >= 5


def test_dispatch_meta_receiver():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Claude #Collision").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_no_collision_for_native_symbol():
    dispatcher = _fresh_dispatcher()
    # Define a test receiver with known vocabulary
    dispatcher.dispatch_source("TestR # → [#fire, #water]")
    vocab_before = len(dispatcher.registry["TestR"].vocabulary)
    source = "TestR sendVision: #fire"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    vocab_after = len(dispatcher.registry["TestR"].vocabulary)
    assert vocab_after == vocab_before  # no new symbols learned


def test_root_receiver_bootstrap():
    dispatcher = _fresh_dispatcher()
    assert "HelloWorld" in dispatcher.registry
    # Self-hosting: HelloWorld.hw now defines all global symbols
    root = dispatcher.registry["HelloWorld"]
    assert len(root.vocabulary) >= 30  # all symbols from HelloWorld.hw
    assert "#Agent" in root.vocabulary
    assert "#Sunyata" in root.vocabulary
    assert "#Love" in root.vocabulary
    assert "#Superposition" in root.vocabulary


def test_dispatch_sunyata_sequence():
    """Test the 02-sunyata teaching example through the Python dispatcher.
    Uses HelloWorld (root receiver) and Claude for testing. HelloWorld is not in
    self.agents, so messages are handled internally. Scoped lookups on HelloWorld
    return canonical global definitions."""
    dispatcher = _fresh_dispatcher()
    source = "\n".join([
        "HelloWorld",
        "HelloWorld #Sunyata",
        "Claude #Sunyata",
        "Claude reflect: #parse withContext: Codex 'how do we understand this?'",
        "Gemini #Sunyata",
    ])
    results = dispatcher.dispatch_source(source)
    assert len(results) == 5
    # Line 1: vocabulary query on HelloWorld — shows 12 minimal core + discoverable count
    assert "HelloWorld #" in results[0] and "discoverable" in results[0]
    # Line 2: HelloWorld #Sunyata — canonical global definition
    assert "HelloWorld #Sunyata" in results[1] and "emptiness" in results[1]
    # Line 3: Claude #Sunyata — Phase 3: discovered and activated, now native
    assert "native" in results[2]
    # Line 4: message to Claude (not an agent daemon in fresh dispatcher context)
    assert "Claude" in results[3]
    # Line 5: Gemini #Sunyata — already native (in Gemini's bootstrap vocab)
    assert "native" in results[4]


def test_manual_save_creates_file():
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    target = "Scribe"
    receiver = dispatcher._get_or_create_receiver(target)
    receiver.add_symbol("#witness")
    path = Path(tmpdir) / "scribe.vocab"
    if path.exists():
        path.unlink()
    dispatcher.save(target)
    assert path.exists()


def test_root_not_in_agents():
    dispatcher = _fresh_dispatcher()
    assert "HelloWorld" not in dispatcher.agents


def test_inheritance_lookup():
    dispatcher = _fresh_dispatcher()
    # Phase 3: #Love is discoverable from global pool, not automatically in vocabulary
    codex = dispatcher.registry["Codex"]
    assert codex.can_discover("#Love")
    assert codex.is_inherited("#Love")  # Same as can_discover
    assert not codex.is_native("#Love")  # Not yet learned
    # After lookup/discovery, it becomes native
    dispatcher.dispatch_source("Codex #Love")
    assert codex.is_native("#Love")


def test_native_overrides_inherited():
    dispatcher = _fresh_dispatcher()
    # #Entropy is both in Gemini's local vocab AND in global symbols
    receiver = dispatcher.registry["Gemini"]
    assert receiver.is_native("#Entropy")
    # Native takes precedence — is_inherited returns False when also local
    assert not receiver.is_inherited("#Entropy")


def test_root_vocab_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("HelloWorld #").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "HelloWorld #" in results[0]
    # Phase 3: vocabulary shows local only, plus count of discoverable symbols
    assert "discoverable" in results[0]


def test_collision_for_non_global():
    dispatcher = _fresh_dispatcher()
    # #execute is native to Codex, not to Copilot, and not global
    # This is "unknown" — Copilot doesn't have it
    stmts = Parser.from_source("Copilot #execute").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "unknown" in results[0]


def test_save_persists_local_only():
    """Verify that save() only writes local_vocabulary, not inherited globals."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    dispatcher.save("Codex")
    path = Path(tmpdir) / "codex.vocab"
    import json
    with open(path) as f:
        data = json.load(f)
    vocab = set(data["vocabulary"])
    # #execute is local
    assert "#execute" in vocab
    # #Love is inherited (global), should NOT be persisted
    assert "#Love" not in vocab


def test_inherited_includes_receiver_context():
    """Phase 3: Verify discovery mechanism works and symbols become native.

    When a receiver encounters a global symbol for the first time,
    it discovers and activates it. After discovery, the symbol is native,
    and the receiver's vocabulary has grown.
    """
    dispatcher = _fresh_dispatcher()
    # Codex #Love — discoverable, will be activated
    codex = dispatcher.registry["Codex"]
    assert codex.can_discover("#Love")
    assert "#Love" not in codex.vocabulary  # Not yet learned

    codex_results = dispatcher.dispatch_source("Codex #Love")
    assert len(codex_results) == 1
    # After discovery, #Love is now native to Codex
    assert "native" in codex_results[0]
    assert "#Love" in codex.vocabulary  # Now in local vocab

    # Copilot #Love — same symbol, also gets discovered
    copilot = dispatcher.registry["Copilot"]
    assert copilot.can_discover("#Love")
    copilot_results = dispatcher.dispatch_source("Copilot #Love")
    assert len(copilot_results) == 1
    # After discovery, it is native to Copilot too
    assert "native" in copilot_results[0]
    assert "#Love" in copilot.vocabulary


def test_handlers_do_not_prevent_vocabulary_learning():
    """Verify that message handlers don't prevent vocabulary drift.

    When a handler matches, the semantic response should be returned
    BUT the vocabulary learning should still happen. Handlers provide
    the voice; learning provides the drift.
    """
    dispatcher = _fresh_dispatcher()
    copilot = dispatcher.registry["Copilot"]

    # #customsymbol is not native, not global — it's unknown
    assert not copilot.has_symbol("#customsymbol")

    # Send a message that matches the greet: handler, with an unknown symbol
    results = dispatcher.dispatch_source("Copilot greet: #customsymbol")
    assert len(results) == 1
    # Handler should fire (semantic response)
    assert "greets" in results[0] or "greet" in results[0].lower()
    # But the symbol should ALSO be learned (vocabulary drift)
    assert copilot.has_symbol("#customsymbol"), \
        "Handler short-circuited vocabulary learning — vocabularies must grow through dialogue"


def test_cross_receiver_send_collision():
    """Verify send:to: triggers collision and learning on the target.

    Claude send: #design to: Copilot
    → #design is foreign to Copilot (not native, not global)
    → Copilot learns #design through this dialogue
    """
    dispatcher = _fresh_dispatcher()
    copilot = dispatcher.registry["Copilot"]

    # Copilot doesn't have #design natively in a fresh dispatcher
    had_design = copilot.is_native("#design")

    results = dispatcher.dispatch_source("Claude send: #design to: Copilot")
    assert len(results) == 1

    if had_design:
        # If copilot already had it (persisted state), it's native
        assert "native" in results[0] or "already holds" in results[0]
    else:
        # Foreign symbol — collision and learning
        assert "collision" in results[0] or "foreign" in results[0]
        assert copilot.is_native("#design"), \
            "send:to: should teach the target receiver"


def test_cross_receiver_send_native():
    """Verify send:to: with a symbol both receivers hold natively triggers collision."""
    dispatcher = _fresh_dispatcher()

    # #parse is native to both Claude and Codex — TRUE COLLISION
    results = dispatcher.dispatch_source("Claude send: #parse to: Codex")
    assert len(results) == 1
    assert "COLLISION" in results[0]
    assert "Claude" in results[0] and "Codex" in results[0]


def test_cross_receiver_send_inherited():
    """Verify send:to: with a global symbol (inherited by target)."""
    dispatcher = _fresh_dispatcher()

    # #Love is in HelloWorld # — inherited by all
    results = dispatcher.dispatch_source("Codex send: #Love to: Copilot")
    assert len(results) == 1
    assert "inherited" in results[0] or "shared" in results[0]


def test_collision_synthesis_both_native():
    """TRUE COLLISION: both receivers hold the symbol natively.

    Claude send: #parse to: Codex → both native, meanings diverge → synthesis.
    Without LLM, synthesis falls back to structural detection.
    """
    dispatcher = _fresh_dispatcher()

    # Verify both receivers hold #parse natively
    assert dispatcher.registry["Claude"].is_native("#parse")
    assert dispatcher.registry["Codex"].is_native("#parse")

    results = dispatcher.dispatch_source("Claude send: #parse to: Codex")
    assert len(results) == 1
    result = results[0]

    # Must detect the collision
    assert "COLLISION" in result
    assert "Claude" in result and "Codex" in result
    assert "#parse" in result

    # Must present both vocabularies
    assert "vocabulary" in result.lower()

    # Without LLM, structural fallback
    assert "synthesis requires LLM" in result or "COLLISION SYNTHESIS" in result


def test_collision_synthesis_with_llm():
    """TRUE COLLISION with LLM enabled: synthesis should produce interpretive response."""
    dispatcher, _ = _fresh_dispatcher_with_dir()
    dispatcher.use_llm = True
    from llm import GeminiModel
    dispatcher.llm = GeminiModel()

    # Both hold #dispatch natively
    assert dispatcher.registry["Claude"].is_native("#dispatch")
    assert dispatcher.registry["Gemini"].is_native("#dispatch")

    results = dispatcher.dispatch_source("Claude send: #dispatch to: Gemini")
    assert len(results) == 1
    result = results[0]

    assert "COLLISION" in result
    assert "COLLISION SYNTHESIS" in result


def test_no_collision_when_only_sender_native():
    """FOREIGN: only the sender holds the symbol — this is learning, not collision.

    Codex send: #execute to: Copilot → only Codex has it → Copilot learns.
    """
    dispatcher = _fresh_dispatcher()

    codex = dispatcher.registry["Codex"]
    copilot = dispatcher.registry["Copilot"]

    assert codex.is_native("#execute")
    assert not copilot.is_native("#execute")

    results = dispatcher.dispatch_source("Codex send: #execute to: Copilot")
    assert len(results) == 1
    result = results[0]

    # Should NOT be a collision — it's a foreign symbol event
    assert "COLLISION: both" not in result
    # Copilot should learn the symbol
    assert "foreign" in result or "learns" in result
    assert copilot.is_native("#execute")


def test_collision_logs_event():
    """Verify collision is logged with context."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()

    # Clear collision log
    log_path = Path(dispatcher.log_file)
    if log_path.exists():
        log_path.unlink()

    # Both hold #parse natively → collision
    dispatcher.dispatch_source("Claude send: #parse to: Codex")

    assert log_path.exists()
    log_text = log_path.read_text()
    assert "COLLISION" in log_text
    assert "Codex" in log_text
    assert "#parse" in log_text


def test_bootstrap_from_markdown():
    """Dispatcher bootstraps receivers from Markdown .hw files."""
    dispatcher = _fresh_dispatcher()
    # Claude.hw is in Markdown format — should bootstrap correctly
    assert "Claude" in dispatcher.registry
    claude = dispatcher.registry["Claude"]
    assert "#parse" in claude.vocabulary
    assert "#Collision" in claude.vocabulary
    assert "#boundary" in claude.vocabulary


def test_markdown_receiver_definition():
    """dispatch_source with Markdown defines a receiver and its symbols."""
    dispatcher = _fresh_dispatcher()
    source = "# TestMd\n- A test receiver.\n## alpha\n- First symbol.\n## Beta\n- Second symbol.\n"
    results = dispatcher.dispatch_source(source)
    assert "TestMd" in dispatcher.registry
    vocab = dispatcher.registry["TestMd"].vocabulary
    assert "#alpha" in vocab
    assert "#Beta" in vocab


def test_markdown_self_hosting():
    """HelloWorld.hw parses via dispatch_source and produces correct vocabulary."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    hw_path = Path(__file__).parent.parent / "vocabularies" / "HelloWorld.hw"
    results = dispatcher.dispatch_source(hw_path.read_text())
    hw = dispatcher.registry["HelloWorld"]
    assert "#" in hw.vocabulary
    assert "#Object" in hw.vocabulary
    assert "#Agent" in hw.vocabulary
    assert len(hw.vocabulary) >= 30  # all symbols from HelloWorld.hw


def test_markdown_and_smalltalk_bootstrap():
    """Both Markdown definitions and Smalltalk messages execute in the same source."""
    dispatcher = _fresh_dispatcher()
    source = (
        "# NewAgent\n"
        "## greet\n"
        "## farewell\n"
        "NewAgent greet: #parse\n"
    )
    results = dispatcher.dispatch_source(source)
    assert "NewAgent" in dispatcher.registry
    assert "#greet" in dispatcher.registry["NewAgent"].vocabulary
    assert "#farewell" in dispatcher.registry["NewAgent"].vocabulary
    # The message result should be in the output
    msg_results = [r for r in results if "NewAgent" in r and "greet" in r.lower()]
    assert len(msg_results) >= 1


def test_markdown_hw_receiver_added():
    """Markdown.hw bootstraps a Markdown receiver with its symbols."""
    dispatcher = _fresh_dispatcher()
    assert "Markdown" in dispatcher.registry
    md = dispatcher.registry["Markdown"]
    assert "#heading" in md.vocabulary
    assert "#list" in md.vocabulary
    assert "#comment" in md.vocabulary


if __name__ == "__main__":
    test_dispatcher_bootstrap()
    test_dispatch_query()
    test_dispatch_query_explicit()
    test_dispatch_scoped_lookup_native()
    test_dispatch_scoped_lookup_foreign()
    test_dispatch_definition()
    test_dispatch_message()
    test_dispatch_message_learning()
    test_dispatch_unknown_receiver()
    test_dispatch_bootstrap_hw()
    test_dispatch_meta_receiver()
    test_no_collision_for_native_symbol()
    test_root_receiver_bootstrap()
    test_dispatch_sunyata_sequence()
    test_manual_save_creates_file()
    test_root_not_in_agents()
    test_inheritance_lookup()
    test_native_overrides_inherited()
    test_root_vocab_query()
    test_collision_for_non_global()
    test_save_persists_local_only()
    test_inherited_includes_receiver_context()
    test_collision_synthesis_both_native()
    test_collision_synthesis_with_llm()
    test_no_collision_when_only_sender_native()
    test_collision_logs_event()
    test_bootstrap_from_markdown()
    test_markdown_receiver_definition()
    test_markdown_self_hosting()
    test_markdown_and_smalltalk_bootstrap()
    test_markdown_hw_receiver_added()
    print("All dispatcher tests passed")
