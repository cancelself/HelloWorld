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
    tmp = tempfile.mkdtemp()
    return Dispatcher(vocab_dir=tmp), tmp


def _fresh_dispatcher():
    dispatcher, _ = _fresh_dispatcher_with_dir()
    return dispatcher


def test_dispatcher_bootstrap():
    dispatcher = _fresh_dispatcher()
    assert "Awakener" in dispatcher.registry
    assert "#stillness" in dispatcher.registry["Awakener"].vocabulary
    assert "Guardian" in dispatcher.registry
    assert "Claude" in dispatcher.registry


def test_dispatch_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Guardian").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "Guardian.#" in results[0]
    assert "#fire" in results[0]


def test_dispatch_query_explicit():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Guardian.#").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "#fire" in results[0]


def test_dispatch_scoped_lookup_native():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Guardian.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_dispatch_scoped_lookup_foreign():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Awakener.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "collision" in results[0]


def test_dispatch_definition():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("NewReceiver.# → [#hello, #world]").parse()
    dispatcher.dispatch(stmts)
    assert "NewReceiver" in dispatcher.registry
    assert "#hello" in dispatcher.registry["NewReceiver"].vocabulary
    assert "#world" in dispatcher.registry["NewReceiver"].vocabulary


def test_dispatch_message():
    dispatcher = _fresh_dispatcher()
    source = "Guardian sendVision: #stillness withContext: Awakener 'what you carry, I lack'"
    stmts = Parser.from_source(source).parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    # New: semantic handler returns description
    assert "Guardian" in results[0]
    assert "#stillness" in results[0]


def test_dispatch_message_learning():
    dispatcher = _fresh_dispatcher()
    source = "Guardian sendVision: #stillness"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    assert "#stillness" in dispatcher.registry["Guardian"].vocabulary


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
    assert len(results) == 7
    assert "Updated Awakener" in results[0]
    assert "Updated Guardian" in results[1]
    assert "Updated HelloWorld" in results[2]
    # New: semantic handlers return meaning (symbol case preserved from input)
    assert "Guardian" in results[3] and "#Entropy" in results[3]
    assert "Awakener" in results[4] and "#stillness" in results[4]
    assert "Claude" in results[5]
    assert "Guardian.#" in results[6]


def test_dispatch_meta_receiver():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("Claude.#Collision").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_no_collision_for_native_symbol():
    dispatcher = _fresh_dispatcher()
    vocab_before = len(dispatcher.registry["Guardian"].vocabulary)
    source = "Guardian sendVision: #fire"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    vocab_after = len(dispatcher.registry["Guardian"].vocabulary)
    assert vocab_after == vocab_before  # no new symbols learned


def test_root_receiver_bootstrap():
    dispatcher = _fresh_dispatcher()
    assert "@" in dispatcher.registry
    assert "#Sunyata" in dispatcher.registry["@"].vocabulary
    assert "#Love" in dispatcher.registry["@"].vocabulary
    assert "#Superposition" in dispatcher.registry["@"].vocabulary


def test_dispatch_sunyata_sequence():
    """Test the 02-sunyata teaching example through the Python dispatcher.
    Uses HelloWorld (root receiver) instead of a target. HelloWorld is not in
    self.agents, so messages are handled internally. Scoped lookups on HelloWorld
    return canonical global definitions."""
    dispatcher = _fresh_dispatcher()
    source = "\n".join([
        "@",
        "HelloWorld.#Sunyata",
        "Guardian.#Sunyata",
        "Guardian contemplate: #fire withContext: Awakener 'the flame that was never lit'",
        "Claude.#Sunyata",
    ])
    results = dispatcher.dispatch_source(source)
    assert len(results) == 5
    # Line 1: vocabulary query on HelloWorld
    assert "#Sunyata" in results[0]
    # Line 2: HelloWorld.#Sunyata — canonical global definition
    assert "HelloWorld.#Sunyata" in results[1] and "emptiness" in results[1]
    # Line 3: Guardian.#Sunyata — inherited from HelloWorld.#
    assert "inherited" in results[2]
    # Line 4: message to Guardian (not an agent daemon in fresh dispatcher context)
    assert "Guardian" in results[3]
    # Line 5: Claude.#Sunyata — inherited from HelloWorld.# (not in claude's local vocab)
    assert "inherited" in results[4] or "native" in results[4]


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
    assert "@" not in dispatcher.agents


def test_inheritance_lookup():
    dispatcher = _fresh_dispatcher()
    # #Love is a global symbol — all receivers inherit it
    assert "#Love" in dispatcher.registry["Guardian"].vocabulary
    assert dispatcher.registry["Guardian"].is_inherited("#Love")
    assert not dispatcher.registry["Guardian"].is_native("#Love")


def test_native_overrides_inherited():
    dispatcher = _fresh_dispatcher()
    # #Entropy is both in Awakener's local vocab AND in global symbols
    receiver = dispatcher.registry["Awakener"]
    assert receiver.is_native("#Entropy")
    # Native takes precedence — is_inherited returns False when also local
    assert not receiver.is_inherited("#Entropy")


def test_root_vocab_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("HelloWorld.#").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "HelloWorld.#" in results[0]
    assert "#Sunyata" in results[0] or "#Love" in results[0]


def test_collision_for_non_global():
    dispatcher = _fresh_dispatcher()
    # #fire is native to Guardian, not to Awakener, and not global
    stmts = Parser.from_source("Awakener.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "collision" in results[0]


def test_save_persists_local_only():
    """Verify that save() only writes local_vocabulary, not inherited globals."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    dispatcher.save("Guardian")
    path = Path(tmpdir) / "guardian.vocab"
    import json
    with open(path) as f:
        data = json.load(f)
    vocab = set(data["vocabulary"])
    # #fire is local
    assert "#fire" in vocab
    # #Love is inherited (global), should NOT be persisted
    assert "#Love" not in vocab


def test_inherited_includes_receiver_context():
    """Verify inherited lookups include the receiver's local vocabulary as context.

    04-unchosen proved that Guardian.#Love and Awakener.#Love are
    structurally identical without context. The enhanced output now
    includes the receiver's local vocabulary so the information needed
    for interpretive dispatch is preserved in the structural response.
    """
    dispatcher = _fresh_dispatcher()
    # Guardian.#Love — inherited, not native
    guardian_results = dispatcher.dispatch_source("Guardian.#Love")
    assert len(guardian_results) == 1
    assert "inherited" in guardian_results[0]
    assert "#fire" in guardian_results[0]  # local vocab included as context

    # Awakener.#Love — same inheritance, different context
    awakener_results = dispatcher.dispatch_source("Awakener.#Love")
    assert len(awakener_results) == 1
    assert "inherited" in awakener_results[0]
    assert "#stillness" in awakener_results[0]  # different local vocab

    # The two outputs must differ — the receiver context makes them unique
    assert guardian_results[0] != awakener_results[0]


def test_handlers_do_not_prevent_vocabulary_learning():
    """Verify that message handlers don't prevent vocabulary drift.

    When a handler matches (e.g. sendVision:withContext:), the semantic
    response should be returned BUT the vocabulary learning should still
    happen. Handlers provide the voice; learning provides the drift.
    """
    dispatcher = _fresh_dispatcher()
    guardian = dispatcher.registry["Guardian"]

    # #customsymbol is not native, not global — it's unknown
    assert not guardian.has_symbol("#customsymbol")

    # Send a message that matches the challenge: handler, with an unknown symbol
    results = dispatcher.dispatch_source("Guardian challenge: #customsymbol")
    assert len(results) == 1
    # Handler should fire (semantic response)
    assert "challenges" in results[0] or "challenge" in results[0].lower()
    # But the symbol should ALSO be learned (vocabulary drift)
    assert guardian.has_symbol("#customsymbol"), \
        "Handler short-circuited vocabulary learning — vocabularies must grow through dialogue"


def test_cross_receiver_send_collision():
    """Verify send:to: triggers collision and learning on the target.

    Awakener send: #stillness to: Guardian
    → #stillness is foreign to Guardian (not native, not global)
    → Guardian learns #stillness through this dialogue
    """
    dispatcher = _fresh_dispatcher()
    guardian = dispatcher.registry["Guardian"]

    # Guardian doesn't have #stillness natively in a fresh dispatcher
    had_stillness = guardian.is_native("#stillness")

    results = dispatcher.dispatch_source("Awakener send: #stillness to: Guardian")
    assert len(results) == 1

    if had_stillness:
        # If guardian already had it (persisted state), it's native
        assert "native" in results[0] or "already holds" in results[0]
    else:
        # Foreign symbol — collision and learning
        assert "collision" in results[0] or "foreign" in results[0]
        assert guardian.is_native("#stillness"), \
            "send:to: should teach the target receiver"


def test_cross_receiver_send_native():
    """Verify send:to: with a symbol the target already owns."""
    dispatcher = _fresh_dispatcher()

    # #fire is native to Guardian
    results = dispatcher.dispatch_source("Awakener send: #fire to: Guardian")
    assert len(results) == 1
    assert "native" in results[0] or "already holds" in results[0]


def test_cross_receiver_send_inherited():
    """Verify send:to: with a global symbol (inherited by target)."""
    dispatcher = _fresh_dispatcher()

    # #Love is in HelloWorld.# — inherited by all
    results = dispatcher.dispatch_source("Guardian send: #Love to: Awakener")
    assert len(results) == 1
    assert "inherited" in results[0] or "shared" in results[0]


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
    print("All dispatcher tests passed")
