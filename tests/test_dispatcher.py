"""Tests for the HelloWorld dispatcher."""

import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import Parser
from dispatcher import Dispatcher
from conftest import (
    hw_symbols, any_native_symbol, shared_native_symbol, exclusive_native_symbol,
)


def _fresh_dispatcher_with_dir():
    """Create a dispatcher with a temp vocab dir so tests start clean."""
    # Disable message bus for faster tests (agents trigger 5s timeouts)
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    tmp = tempfile.mkdtemp()
    dispatcher = Dispatcher(vocab_dir=tmp)
    return dispatcher, tmp


def _fresh_dispatcher():
    dispatcher, _ = _fresh_dispatcher_with_dir()
    return dispatcher


def test_dispatcher_bootstrap():
    dispatcher = _fresh_dispatcher()
    assert "Codex" in dispatcher.registry
    assert hw_symbols("Codex") <= dispatcher.registry["Codex"].vocabulary
    assert "Copilot" in dispatcher.registry
    assert "Claude" in dispatcher.registry


def test_dispatch_query():
    dispatcher = _fresh_dispatcher()
    native_sym = any_native_symbol("Agent")
    stmts = Parser.from_source("Agent").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "Agent" in results[0]
    assert native_sym in results[0]


def test_dispatch_query_explicit():
    dispatcher = _fresh_dispatcher()
    native_sym = any_native_symbol("Agent")
    stmts = Parser.from_source("Agent #").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert native_sym in results[0]


def test_dispatch_scoped_lookup_native():
    dispatcher = _fresh_dispatcher()
    native_sym = any_native_symbol("Agent")
    stmts = Parser.from_source(f"Agent {native_sym}").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_dispatch_scoped_lookup_foreign():
    dispatcher = _fresh_dispatcher()
    foreign_sym = exclusive_native_symbol("Agent", "HelloWorld")
    stmts = Parser.from_source(f"Copilot {foreign_sym}").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    # Agent-exclusive symbols are inherited by Copilot (Agent is parent)
    assert "inherited" in results[0]


def test_inherited_symbol_not_promoted():
    """Inherited symbols stay inherited — they are NOT promoted to local vocab."""
    dispatcher = _fresh_dispatcher()
    codex = dispatcher.registry["Codex"]
    # #synthesize is in HelloWorld (root) — inherited by Codex via chain
    assert codex.is_inherited("#synthesize")
    assert "#synthesize" not in codex.vocabulary  # Not in local

    # Lookup returns inherited, not native
    results = dispatcher.dispatch_source("Codex #synthesize")
    assert len(results) == 1
    assert "inherited" in results[0]
    # Still not in local vocabulary after lookup
    assert "#synthesize" not in codex.vocabulary


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
    source = "Codex analyze: #unknownSymbol"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    assert "#unknownSymbol" in dispatcher.registry["Codex"].vocabulary


def test_dispatch_unknown_receiver():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Nobody").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "Nobody" in dispatcher.registry


def test_dispatch_mixed_statements():
    """Dispatcher handles vocabulary definitions, messages, and lookups."""
    dispatcher = _fresh_dispatcher()
    source = '\n'.join([
        'HelloWorld # → [#Sunyata, #Superposition]',
        'Claude # → []',
        'Claude send: #observe to: Copilot',
        'Claude #parse',
        'Codex',
    ])
    results = dispatcher.dispatch_source(source)
    assert len(results) >= 3


def test_dispatch_meta_receiver():
    """A native symbol in a receiver's .hw is native to that receiver."""
    dispatcher = _fresh_dispatcher()
    native_sym = any_native_symbol("Agent")
    stmts = Parser.from_source(f"Agent {native_sym}").parse()
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
    hw_syms = hw_symbols("HelloWorld")
    assert len(root.vocabulary) >= len(hw_syms)
    assert hw_syms <= root.vocabulary


def test_dispatch_root_lookup_sequence():
    """Test root symbol lookups through the Python dispatcher.
    Uses HelloWorld (root) and agents. Scoped lookups on HelloWorld
    return canonical global definitions. Agent lookups use parent chain."""
    dispatcher = _fresh_dispatcher()
    source = "\n".join([
        "HelloWorld",
        "HelloWorld #Sunyata",
        "Codex #synthesize",
        "Claude reflect: #parse withContext: Codex 'how do we understand this?'",
        "Gemini #synthesize",
    ])
    results = dispatcher.dispatch_source(source)
    assert len(results) == 5
    # Line 1: vocabulary query on HelloWorld
    assert "HelloWorld" in results[0]
    # Line 2: HelloWorld #Sunyata — canonical global definition
    assert "HelloWorld #Sunyata" in results[1] and "absence" in results[1]
    # Line 3: Codex #synthesize — inherited from Object via chain
    assert "inherited" in results[2]
    # Line 4: message to Claude
    assert "Claude" in results[3]
    # Line 5: Gemini #synthesize — inherited from Object
    assert "Gemini #synthesize" in results[4]


def test_manual_save_creates_file():
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    target = "Scribe"
    receiver = dispatcher._get_or_create_receiver(target)
    receiver.add_symbol("#witness")
    path = Path(tmpdir) / "Scribe.hw"
    if path.exists():
        path.unlink()
    dispatcher.save(target)
    assert path.exists()


def test_root_not_in_agents():
    dispatcher = _fresh_dispatcher()
    assert "HelloWorld" not in dispatcher.agents


def test_inheritance_lookup():
    """Prototypal inheritance: symbols are found via parent chain."""
    dispatcher = _fresh_dispatcher()
    codex = dispatcher.registry["Codex"]
    # #synthesize is in HelloWorld (root) — inherited via Codex → Agent → Object → HelloWorld
    assert codex.is_inherited("#synthesize")
    assert not codex.is_native("#synthesize")
    # After lookup, it stays inherited (no promotion)
    dispatcher.dispatch_source("Codex #synthesize")
    assert not codex.is_native("#synthesize")
    assert codex.is_inherited("#synthesize")


def test_native_overrides_inherited():
    """When a symbol is in local vocab, it's native even if also in parent chain."""
    dispatcher = _fresh_dispatcher()
    # HelloWorld has #unknown natively AND Agent has #unknown natively.
    # Agent inherits from Object which inherits from HelloWorld.
    # Add #unknown to a test receiver whose parent also has it.
    dispatcher.dispatch_source("OverrideR # → [#unknown]")
    receiver = dispatcher.registry["OverrideR"]
    receiver.parent = dispatcher.registry["HelloWorld"]
    assert receiver.is_native("#unknown")
    # Native takes precedence — is_inherited returns False when also local
    assert not receiver.is_inherited("#unknown")


def test_root_vocab_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("HelloWorld #").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "HelloWorld" in results[0]
    # Root receiver shows its local symbols
    assert "#" in results[0] or "Object" in results[0]


def test_collision_for_non_global():
    dispatcher = _fresh_dispatcher()
    # A truly unknown symbol — not in any vocabulary
    stmts = Parser.from_source("Copilot #xyzNowhere").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "unknown" in results[0]


def test_save_persists_local_only():
    """Verify that save() only writes local_vocabulary, not inherited globals."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    dispatcher.save("Agent")
    path = Path(tmpdir) / "Agent.hw"
    assert path.exists()
    content = path.read_text()
    # Native symbols appear as ## headings in .hw file
    native_sym = any_native_symbol("Agent")
    bare_name = native_sym.lstrip("#")
    assert bare_name in content
    # #HelloWorld is in HelloWorld (parent's parent), should NOT be persisted
    assert "HelloWorld" not in content


def test_inherited_includes_receiver_context():
    """Prototypal inheritance: inherited symbols resolve with context about the defining ancestor."""
    dispatcher = _fresh_dispatcher()
    codex = dispatcher.registry["Codex"]
    # #synthesize is inherited via chain, not in local vocab
    assert codex.is_inherited("#synthesize")
    assert "#synthesize" not in codex.vocabulary

    codex_results = dispatcher.dispatch_source("Codex #synthesize")
    assert len(codex_results) == 1
    # Returns inherited, identifies the defining ancestor
    assert "inherited" in codex_results[0]
    assert "Object" in codex_results[0]  # defined in Object
    # Still not in local vocab
    assert "#synthesize" not in codex.vocabulary

    # Same for Copilot
    copilot = dispatcher.registry["Copilot"]
    assert copilot.is_inherited("#synthesize")
    copilot_results = dispatcher.dispatch_source("Copilot #synthesize")
    assert len(copilot_results) == 1
    assert "inherited" in copilot_results[0]


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

    # Create two test receivers that share a native symbol
    dispatcher.dispatch_source("SenderR # → [#spark, #flame]")
    dispatcher.dispatch_source("TargetR # → [#spark, #water]")
    results = dispatcher.dispatch_source("SenderR send: #spark to: TargetR")
    assert len(results) == 1
    assert "COLLISION" in results[0]
    assert "SenderR" in results[0] and "TargetR" in results[0]


def test_cross_receiver_send_inherited():
    """Verify send:to: with a symbol inherited via parent chain."""
    dispatcher = _fresh_dispatcher()

    # #synthesize is in HelloWorld — inherited by all via chain
    results = dispatcher.dispatch_source("Codex send: #synthesize to: Copilot")
    assert len(results) == 1
    assert "inherits" in results[0] or "shared" in results[0]


def test_collision_synthesis_both_native():
    """TRUE COLLISION: both receivers hold the symbol natively.

    Both native, meanings diverge → synthesis.
    Without LLM, synthesis falls back to structural detection.
    """
    dispatcher = _fresh_dispatcher()

    # Create two test receivers that share a native symbol
    dispatcher.dispatch_source("AlphaR # → [#light, #dark]")
    dispatcher.dispatch_source("BetaR # → [#light, #sound]")

    assert dispatcher.registry["AlphaR"].is_native("#light")
    assert dispatcher.registry["BetaR"].is_native("#light")

    results = dispatcher.dispatch_source("AlphaR send: #light to: BetaR")
    assert len(results) == 1
    result = results[0]

    # Must detect the collision
    assert "COLLISION" in result
    assert "AlphaR" in result and "BetaR" in result
    assert "#light" in result

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

    # Create two test receivers that share a native symbol for collision
    dispatcher.dispatch_source("LlmSender # → [#glow, #shade]")
    dispatcher.dispatch_source("LlmTarget # → [#glow, #drift]")

    assert dispatcher.registry["LlmSender"].is_native("#glow")
    assert dispatcher.registry["LlmTarget"].is_native("#glow")

    results = dispatcher.dispatch_source("LlmSender send: #glow to: LlmTarget")
    assert len(results) == 1
    result = results[0]

    assert "COLLISION" in result
    assert "COLLISION SYNTHESIS" in result


def test_no_collision_when_only_sender_native():
    """FOREIGN: only the sender holds the symbol — this is learning, not collision.

    Sender has the symbol, target doesn't → target learns.
    """
    dispatcher = _fresh_dispatcher()

    # Create test receivers: sender has #spark, target does not
    dispatcher.dispatch_source("ForeignSender # → [#spark, #flame]")
    dispatcher.dispatch_source("ForeignTarget # → [#water]")

    sender = dispatcher.registry["ForeignSender"]
    target = dispatcher.registry["ForeignTarget"]

    assert sender.is_native("#spark")
    assert not target.is_native("#spark")

    results = dispatcher.dispatch_source("ForeignSender send: #spark to: ForeignTarget")
    assert len(results) == 1
    result = results[0]

    # Should NOT be a collision — it's a foreign symbol event
    assert "COLLISION: both" not in result
    # Target should learn the symbol
    assert "foreign" in result or "learns" in result
    assert target.is_native("#spark")


def test_collision_logs_event():
    """Verify collision is logged with context."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()

    # Create two test receivers that share a native symbol
    dispatcher.dispatch_source("LogSender # → [#pulse, #wave]")
    dispatcher.dispatch_source("LogTarget # → [#pulse, #echo]")

    # Clear collision log
    log_path = Path(dispatcher.log_file)
    if log_path.exists():
        log_path.unlink()

    # Both hold the symbol natively → collision
    dispatcher.dispatch_source("LogSender send: #pulse to: LogTarget")

    assert log_path.exists()
    log_text = log_path.read_text()
    assert "COLLISION" in log_text
    assert "LogTarget" in log_text
    assert "#pulse" in log_text


def test_bootstrap_from_markdown():
    """Dispatcher bootstraps receivers from Markdown .hw files."""
    dispatcher = _fresh_dispatcher()
    # Claude.hw is in Markdown format — should bootstrap correctly
    assert "Claude" in dispatcher.registry
    claude = dispatcher.registry["Claude"]
    assert hw_symbols("Claude") <= claude.vocabulary


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
    hw_syms = hw_symbols("HelloWorld")
    assert hw_syms <= hw.vocabulary
    assert len(hw.vocabulary) >= len(hw_syms)


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


def test_object_hw_receiver_added():
    """Object.hw bootstraps an Object receiver with its symbols."""
    dispatcher = _fresh_dispatcher()
    assert "Object" in dispatcher.registry
    obj = dispatcher.registry["Object"]
    assert hw_symbols("Object") <= obj.vocabulary


def test_parent_chain_bootstrap():
    """Verify parent links are correctly resolved after bootstrap."""
    dispatcher = _fresh_dispatcher()
    claude = dispatcher.registry["Claude"]
    assert claude.parent is not None
    assert claude.parent.name == "Agent"
    assert claude.parent.parent is not None
    assert claude.parent.parent.name == "Object"
    assert claude.parent.parent.parent is not None
    assert claude.parent.parent.parent.name == "HelloWorld"


def test_receiver_chain():
    """Verify chain() returns full inheritance path."""
    dispatcher = _fresh_dispatcher()
    claude = dispatcher.registry["Claude"]
    chain = claude.chain()
    assert chain == ["Claude", "Agent", "Object", "HelloWorld"]


def test_inherited_from_agent():
    """Codex inherits #observe from Agent (not native to Codex)."""
    dispatcher = _fresh_dispatcher()
    codex = dispatcher.registry["Codex"]
    # #observe is defined in Agent.hw, inherited by Codex
    assert codex.is_inherited("#observe")
    assert not codex.is_native("#observe")
    results = dispatcher.dispatch_source("Codex #observe")
    assert "inherited" in results[0]
    assert "Agent" in results[0]


def test_inherited_from_object():
    """Codex inherits #send from Object via Agent."""
    dispatcher = _fresh_dispatcher()
    codex = dispatcher.registry["Codex"]
    assert codex.is_inherited("#send")
    assert not codex.is_native("#send")
    results = dispatcher.dispatch_source("Codex #send")
    assert "inherited" in results[0]
    assert "Object" in results[0]


def test_agent_parent_is_object():
    """Agent : Object has parent link to Object."""
    dispatcher = _fresh_dispatcher()
    agent = dispatcher.registry["Agent"]
    assert agent.parent is not None
    assert agent.parent.name == "Object"


if __name__ == "__main__":
    test_dispatcher_bootstrap()
    test_dispatch_query()
    test_dispatch_query_explicit()
    test_dispatch_scoped_lookup_native()
    test_dispatch_scoped_lookup_foreign()
    test_inherited_symbol_not_promoted()
    test_dispatch_definition()
    test_dispatch_message()
    test_dispatch_message_learning()
    test_dispatch_unknown_receiver()
    test_dispatch_mixed_statements()
    test_dispatch_meta_receiver()
    test_no_collision_for_native_symbol()
    test_root_receiver_bootstrap()
    test_dispatch_root_lookup_sequence()
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
    test_parent_chain_bootstrap()
    test_receiver_chain()
    test_inherited_from_agent()
    test_inherited_from_object()
    test_markdown_parent_is_object()
    print("All dispatcher tests passed")
