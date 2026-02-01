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
    assert "@awakener" in dispatcher.registry
    assert "#stillness" in dispatcher.registry["@awakener"].vocabulary
    assert "@guardian" in dispatcher.registry
    assert "@claude" in dispatcher.registry


def test_dispatch_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@guardian").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@guardian.#" in results[0]
    assert "#fire" in results[0]


def test_dispatch_query_explicit():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@guardian.#").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "#fire" in results[0]


def test_dispatch_scoped_lookup_native():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@guardian.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_dispatch_scoped_lookup_foreign():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@awakener.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "collision" in results[0]


def test_dispatch_definition():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@new_receiver.# \u2192 [#hello, #world]").parse()
    dispatcher.dispatch(stmts)
    assert "@new_receiver" in dispatcher.registry
    assert "#hello" in dispatcher.registry["@new_receiver"].vocabulary
    assert "#world" in dispatcher.registry["@new_receiver"].vocabulary


def test_dispatch_message():
    dispatcher = _fresh_dispatcher()
    source = "@guardian sendVision: #stillness withContext: @awakener 'what you carry, I lack'"
    stmts = Parser.from_source(source).parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@guardian" in results[0]
    assert "#stillness" in results[0]
    assert "what you carry, I lack" in results[0]


def test_dispatch_message_learning():
    dispatcher = _fresh_dispatcher()
    source = "@guardian sendVision: #stillness"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    assert "#stillness" in dispatcher.registry["@guardian"].vocabulary


def test_dispatch_unknown_receiver():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@nobody").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@nobody" in dispatcher.registry


def test_dispatch_bootstrap_hw():
    dispatcher = _fresh_dispatcher()
    path = Path(__file__).parent.parent / 'examples' / 'bootstrap.hw'
    source = path.read_text()
    results = dispatcher.dispatch_source(source)
    assert len(results) == 7
    assert "Updated @awakener" in results[0]
    assert "Updated @guardian" in results[1]
    assert "Updated @" in results[2]
    assert "[@guardian] Received" in results[3]
    assert "[@awakener] Received" in results[4]
    assert "@claude" in results[5]
    assert "@guardian.#" in results[6]


def test_dispatch_meta_receiver():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@claude.#collision").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_no_collision_for_native_symbol():
    dispatcher = _fresh_dispatcher()
    vocab_before = len(dispatcher.registry["@guardian"].vocabulary)
    source = "@guardian sendVision: #fire"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    vocab_after = len(dispatcher.registry["@guardian"].vocabulary)
    assert vocab_after == vocab_before  # no new symbols learned


def test_root_receiver_bootstrap():
    dispatcher = _fresh_dispatcher()
    assert "@" in dispatcher.registry
    assert "#sunyata" in dispatcher.registry["@"].vocabulary
    assert "#love" in dispatcher.registry["@"].vocabulary
    assert "#superposition" in dispatcher.registry["@"].vocabulary


def test_dispatch_sunyata_sequence():
    """Test the 02-sunyata teaching example through the Python dispatcher.
    Uses @ (root receiver) instead of @target. @ is not in self.agents,
    so messages are handled internally. Scoped lookups on @ return
    canonical global definitions."""
    dispatcher = _fresh_dispatcher()
    source = "\n".join([
        "@",
        "@.#sunyata",
        "@guardian.#sunyata",
        "@guardian contemplate: #fire withContext: @awakener 'the flame that was never lit'",
        "@claude.#sunyata",
    ])
    results = dispatcher.dispatch_source(source)
    assert len(results) == 5
    # Line 1: vocabulary query on @
    assert "#sunyata" in results[0]
    # Line 2: @.#sunyata — canonical global definition
    assert "@.#sunyata" in results[1] and "emptiness" in results[1]
    # Line 3: @guardian.#sunyata — inherited from @.#
    assert "inherited" in results[2]
    # Line 4: message to @guardian (not an agent daemon in fresh dispatcher context)
    assert "@guardian" in results[3]
    # Line 5: @claude.#sunyata — inherited from @.# (not in claude's local vocab)
    assert "inherited" in results[4] or "native" in results[4]


def test_manual_save_creates_file():
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    target = "@scribe"
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
    # #love is a global symbol — all receivers inherit it
    assert "#love" in dispatcher.registry["@guardian"].vocabulary
    assert dispatcher.registry["@guardian"].is_inherited("#love")
    assert not dispatcher.registry["@guardian"].is_native("#love")


def test_native_overrides_inherited():
    dispatcher = _fresh_dispatcher()
    # #entropy is both in @awakener's local vocab AND in global symbols
    receiver = dispatcher.registry["@awakener"]
    assert receiver.is_native("#entropy")
    # Native takes precedence — is_inherited returns False when also local
    assert not receiver.is_inherited("#entropy")


def test_root_vocab_query():
    dispatcher = _fresh_dispatcher()
    stmts = Parser.from_source("@.#").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@.#" in results[0]
    assert "#sunyata" in results[0] or "#love" in results[0]


def test_collision_for_non_global():
    dispatcher = _fresh_dispatcher()
    # #fire is native to @guardian, not to @awakener, and not global
    stmts = Parser.from_source("@awakener.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "collision" in results[0]


def test_save_persists_local_only():
    """Verify that save() only writes local_vocabulary, not inherited globals."""
    dispatcher, tmpdir = _fresh_dispatcher_with_dir()
    dispatcher.save("@guardian")
    path = Path(tmpdir) / "guardian.vocab"
    import json
    with open(path) as f:
        data = json.load(f)
    vocab = set(data["vocabulary"])
    # #fire is local
    assert "#fire" in vocab
    # #love is inherited (global), should NOT be persisted
    assert "#love" not in vocab


def test_inherited_includes_receiver_context():
    """Verify inherited lookups include the receiver's local vocabulary as context.

    04-unchosen proved that @guardian.#love and @awakener.#love are
    structurally identical without context. The enhanced output now
    includes the receiver's local vocabulary so the information needed
    for interpretive dispatch is preserved in the structural response.
    """
    dispatcher = _fresh_dispatcher()
    # @guardian.#love — inherited, not native
    guardian_results = dispatcher.dispatch_source("@guardian.#love")
    assert len(guardian_results) == 1
    assert "inherited" in guardian_results[0]
    assert "#fire" in guardian_results[0]  # local vocab included as context

    # @awakener.#love — same inheritance, different context
    awakener_results = dispatcher.dispatch_source("@awakener.#love")
    assert len(awakener_results) == 1
    assert "inherited" in awakener_results[0]
    assert "#stillness" in awakener_results[0]  # different local vocab

    # The two outputs must differ — the receiver context makes them unique
    assert guardian_results[0] != awakener_results[0]


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
