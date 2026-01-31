"""Tests for the HelloWorld dispatcher."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import Parser
from dispatcher import Dispatcher


def test_dispatcher_bootstrap():
    dispatcher = Dispatcher()
    assert "@awakener" in dispatcher.registry
    assert "#stillness" in dispatcher.registry["@awakener"].vocabulary
    assert "@guardian" in dispatcher.registry
    assert "@claude" in dispatcher.registry


def test_dispatch_query():
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@guardian").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@guardian.# " in results[0]
    assert "#fire" in results[0]


def test_dispatch_query_explicit():
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@guardian.#").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "#fire" in results[0]


def test_dispatch_scoped_lookup_native():
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@guardian.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_dispatch_scoped_lookup_foreign():
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@awakener.#fire").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "collision" in results[0]


def test_dispatch_definition():
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@new_receiver.# \u2192 [#hello, #world]").parse()
    dispatcher.dispatch(stmts)
    assert "@new_receiver" in dispatcher.registry
    assert "#hello" in dispatcher.registry["@new_receiver"].vocabulary
    assert "#world" in dispatcher.registry["@new_receiver"].vocabulary


def test_dispatch_message():
    dispatcher = Dispatcher()
    source = "@guardian sendVision: #stillness withContext: @awakener 'what you carry, I lack'"
    stmts = Parser.from_source(source).parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@guardian" in results[0]
    assert "#stillness" in results[0]
    assert "what you carry, I lack" in results[0]


def test_dispatch_message_learning():
    dispatcher = Dispatcher()
    source = "@guardian sendVision: #stillness"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    assert "#stillness" in dispatcher.registry["@guardian"].vocabulary


def test_dispatch_unknown_receiver():
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@nobody").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "@nobody" in dispatcher.registry


def test_dispatch_bootstrap_hw():
    dispatcher = Dispatcher()
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
    dispatcher = Dispatcher()
    stmts = Parser.from_source("@claude.#collision").parse()
    results = dispatcher.dispatch(stmts)
    assert len(results) == 1
    assert "native" in results[0]


def test_no_collision_for_native_symbol():
    dispatcher = Dispatcher()
    source = "@guardian sendVision: #fire"
    stmts = Parser.from_source(source).parse()
    dispatcher.dispatch(stmts)
    vocab_before = len(dispatcher.registry["@guardian"].vocabulary)
    assert vocab_before == 5  # no new symbols learned


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
    print("All dispatcher tests passed")
