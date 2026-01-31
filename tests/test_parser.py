"""Tests for the HelloWorld parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import (  # noqa: E402
    Message,
    Parser,
    SymbolLookup,
    ValueType,
    VocabularyDefinition,
    VocabularyQuery,
)


def parse(source: str):
    return Parser.from_source(source).parse()


def test_vocabulary_definition():
    statements = parse("@guardian.# → [#fire, #vision]")
    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, VocabularyDefinition)
    assert stmt.receiver == "@guardian"
    assert stmt.symbols == ["#fire", "#vision"]


def test_message_with_annotation():
    source = "@guardian sendVision: #entropy withContext: lastNightSleep 'you burned bright'"
    statements = parse(source)
    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, Message)
    assert stmt.receiver == "@guardian"
    assert len(stmt.keywords) == 2
    assert stmt.keywords[0].name == "sendVision"
    assert stmt.keywords[0].value.kind == ValueType.SYMBOL
    assert stmt.keywords[0].value.value == "#entropy"
    assert stmt.keywords[1].value.kind == ValueType.IDENTIFIER
    assert stmt.keywords[1].value.value == "lastNightSleep"
    assert stmt.annotation == "you burned bright"


def test_symbol_lookup():
    statements = parse("@claude.#entropy")
    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, SymbolLookup)
    assert stmt.receiver == "@claude"
    assert stmt.symbol == "#entropy"


def test_vocabulary_query_variants():
    for source in ("@guardian", "@guardian.#"):
        statements = parse(source)
        assert isinstance(statements[0], VocabularyQuery)
        assert statements[0].receiver == "@guardian"


def test_parse_bootstrap_example():
    bootstrap = Path(__file__).parent.parent / "examples" / "bootstrap.hw"
    statements = Parser.from_source(bootstrap.read_text()).parse()
    assert len(statements) == 6
    assert isinstance(statements[0], VocabularyDefinition)
    assert isinstance(statements[1], VocabularyDefinition)
    assert isinstance(statements[2], Message)
    assert isinstance(statements[3], Message)
    assert isinstance(statements[4], SymbolLookup)
    assert isinstance(statements[5], VocabularyQuery)


if __name__ == "__main__":
    test_vocabulary_definition()
    test_message_with_annotation()
    test_symbol_lookup()
    test_vocabulary_query_variants()
    test_parse_bootstrap_example()
    print("✓ All parser tests passed")
