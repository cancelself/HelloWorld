"""Tests for the HelloWorld dispatcher."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dispatcher import Dispatcher, ReceiverRegistry


def test_bootstrap_registry():
    d = Dispatcher()
    assert d.registry.has("@guardian")
    assert d.registry.has("@awakener")
    assert d.registry.has("@claude")


def test_vocabulary_query():
    d = Dispatcher()
    results = d.dispatch("@guardian")
    assert len(results) == 1
    r = results[0]
    assert r.kind == "vocabulary"
    assert r.receiver == "@guardian"
    assert "#fire" in r.data["vocabulary"]
    assert "#vision" in r.data["vocabulary"]


def test_vocabulary_query_explicit():
    d = Dispatcher()
    results = d.dispatch("@guardian.#")
    assert len(results) == 1
    assert results[0].kind == "vocabulary"
    assert results[0].receiver == "@guardian"


def test_scoped_lookup_native():
    d = Dispatcher()
    results = d.dispatch("@guardian.#fire")
    assert len(results) == 1
    r = results[0]
    assert r.kind == "scoped_lookup"
    assert r.receiver == "@guardian"
    assert r.data["symbol"] == "#fire"
    assert r.data["native"] is True


def test_scoped_lookup_foreign():
    d = Dispatcher()
    results = d.dispatch("@awakener.#fire")
    assert len(results) == 1
    r = results[0]
    assert r.kind == "scoped_lookup"
    assert r.receiver == "@awakener"
    assert r.data["symbol"] == "#fire"
    assert r.data["native"] is False


def test_message_dispatch():
    d = Dispatcher()
    results = d.dispatch(
        "@guardian sendVision: #stillness withContext: @awakener 'what you carry, I lack'"
    )
    assert len(results) == 1
    r = results[0]
    assert r.kind == "message"
    assert r.receiver == "@guardian"
    assert r.data["arguments"]["sendVision"] == "#stillness"
    assert r.data["arguments"]["withContext"] == "@awakener"
    assert r.data["annotation"] == "what you carry, I lack"
    assert "#stillness" in r.data["collisions"]


def test_vocabulary_definition():
    d = Dispatcher()
    results = d.dispatch("@test.# → [#one, #two, #three]")
    assert len(results) == 1
    r = results[0]
    assert r.kind == "definition"
    assert r.receiver == "@test"
    assert d.registry.vocabulary("@test") == ["#one", "#two", "#three"]


def test_unknown_receiver():
    d = Dispatcher()
    results = d.dispatch("@nobody")
    assert len(results) == 1
    assert results[0].kind == "error"
    assert "Unknown receiver" in results[0].data["error"]


def test_bootstrap_hw_file():
    d = Dispatcher()
    path = Path(__file__).parent.parent / 'examples' / 'bootstrap.hw'
    with open(path, 'r') as f:
        source = f.read()
    results = d.dispatch(source)
    assert len(results) == 6
    assert results[0].kind == "definition"
    assert results[0].receiver == "@awakener"
    assert results[1].kind == "definition"
    assert results[1].receiver == "@guardian"
    assert results[2].kind == "message"
    assert results[2].receiver == "@guardian"
    assert results[3].kind == "message"
    assert results[3].receiver == "@awakener"
    assert results[4].kind == "scoped_lookup"
    assert results[4].receiver == "@claude"
    assert results[5].kind == "vocabulary"
    assert results[5].receiver == "@guardian"


def test_collision_detection():
    d = Dispatcher()
    results = d.dispatch("@guardian sendVision: #stillness")
    r = results[0]
    assert "#stillness" in r.data["collisions"]


def test_no_collision_for_native():
    d = Dispatcher()
    results = d.dispatch("@guardian sendVision: #fire")
    r = results[0]
    assert r.data["collisions"] == []


def test_meta_receiver():
    d = Dispatcher()
    results = d.dispatch("@claude.#collision")
    assert len(results) == 1
    r = results[0]
    assert r.kind == "scoped_lookup"
    assert r.receiver == "@claude"
    assert r.data["symbol"] == "#collision"
    assert r.data["native"] is True


if __name__ == "__main__":
    test_bootstrap_registry()
    test_vocabulary_query()
    test_vocabulary_query_explicit()
    test_scoped_lookup_native()
    test_scoped_lookup_foreign()
    test_message_dispatch()
    test_vocabulary_definition()
    test_unknown_receiver()
    test_bootstrap_hw_file()
    test_collision_detection()
    test_no_collision_for_native()
    test_meta_receiver()
    print("All dispatcher tests passed")
