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
    assert len(results) == 6
    assert "Updated @awakener" in results[0]
    assert "Updated @guardian" in results[1]
    assert "[@guardian] Received" in results[2]
    assert "[@awakener] Received" in results[3]
    assert "@claude" in results[4]
    assert "@guardian.#" in results[5]


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
    test_manual_save_creates_file()
    print("All dispatcher tests passed")
