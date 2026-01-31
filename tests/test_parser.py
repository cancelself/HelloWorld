"""Tests for the HelloWorld parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import Parser
from ast_nodes import (
    VocabularyDefinitionNode, VocabularyQueryNode,
    ScopedLookupNode, MessageNode, SymbolNode,
)


def parse(source: str):
    return Parser.from_source(source).parse()


def expect_syntax_error(source: str, snippet: str):
    try:
        Parser.from_source(source).parse()
    except SyntaxError as exc:
        assert snippet in str(exc)
        return
    raise AssertionError("Expected SyntaxError")


def test_vocabulary_definition():
    nodes = parse("@guardian.# \u2192 [#fire, #vision]")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, VocabularyDefinitionNode)
    assert stmt.receiver.name == "@guardian"
    assert [s.name for s in stmt.symbols] == ["#fire", "#vision"]


def test_message_with_annotation():
    source = "@guardian sendVision: #entropy withContext: lastNightSleep 'you burned bright'"
    nodes = parse(source)
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    assert stmt.receiver.name == "@guardian"
    args = list(stmt.arguments.items())
    assert args[0][0] == "sendVision"
    assert isinstance(args[0][1], SymbolNode)
    assert args[0][1].name == "#entropy"
    assert stmt.annotation == "you burned bright"


def test_symbol_lookup():
    nodes = parse("@claude.#entropy")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, ScopedLookupNode)
    assert stmt.receiver.name == "@claude"
    assert stmt.symbol.name == "#entropy"


def test_vocabulary_query_variants():
    for source in ("@guardian", "@guardian.#"):
        nodes = parse(source)
        assert isinstance(nodes[0], VocabularyQueryNode)
        assert nodes[0].receiver.name == "@guardian"


def test_parse_bootstrap_example():
    bootstrap = Path(__file__).parent.parent / "examples" / "bootstrap.hw"
    nodes = Parser.from_source(bootstrap.read_text()).parse()
    assert len(nodes) == 7
    assert isinstance(nodes[0], VocabularyDefinitionNode)
    assert isinstance(nodes[1], VocabularyDefinitionNode)
    assert isinstance(nodes[2], VocabularyDefinitionNode)
    assert isinstance(nodes[3], MessageNode)
    assert isinstance(nodes[4], MessageNode)
    assert isinstance(nodes[5], ScopedLookupNode)
    assert isinstance(nodes[6], VocabularyQueryNode)


def test_parse_sunyata_example():
    source = "\n".join([
        "@target",
        "@target.#sunyata",
        "@guardian.#sunyata",
        "@target contemplate: #fire withContext: @guardian 'the flame that was never lit'",
        "@claude.#sunyata",
    ])
    nodes = Parser.from_source(source).parse()
    assert len(nodes) == 5
    assert isinstance(nodes[0], VocabularyQueryNode)
    assert isinstance(nodes[1], ScopedLookupNode)
    assert isinstance(nodes[2], ScopedLookupNode)
    assert isinstance(nodes[3], MessageNode)
    assert isinstance(nodes[4], ScopedLookupNode)


def test_missing_vocabulary_bracket_raises():
    source = "@guardian.# → [#fire, #vision"
    expect_syntax_error(source, "Expect ']' after symbols")


def test_missing_keyword_colon_raises():
    source = "@guardian sendVision #fire"
    expect_syntax_error(source, "Expect ':' after keyword 'sendVision'")


if __name__ == "__main__":
    test_vocabulary_definition()
    test_message_with_annotation()
    test_symbol_lookup()
    test_vocabulary_query_variants()
    test_parse_bootstrap_example()
    test_parse_sunyata_example()
    test_missing_vocabulary_bracket_raises()
    test_missing_keyword_colon_raises()
    print("All parser tests passed")
