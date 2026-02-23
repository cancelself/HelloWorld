"""Tests for the HelloWorld parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import Parser
from ast_nodes import (
    VocabularyDefinitionNode, VocabularyQueryNode,
    ScopedLookupNode, MessageNode, SymbolNode,
    HeadingNode, DescriptionNode, UnaryMessageNode, SuperLookupNode,
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
    nodes = parse("Guardian # → [#fire, #vision]")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, VocabularyDefinitionNode)
    assert stmt.receiver.name == "Guardian"
    assert [s.name for s in stmt.symbols] == ["#fire", "#vision"]


def test_message_with_annotation():
    source = "Guardian sendVision: #entropy withContext: lastNightSleep 'you burned bright'"
    nodes = parse(source)
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    assert stmt.receiver.name == "Guardian"
    args = list(stmt.arguments.items())
    assert args[0][0] == "sendVision"
    assert isinstance(args[0][1], SymbolNode)
    assert args[0][1].name == "#entropy"
    assert stmt.annotation == "you burned bright"


def test_symbol_lookup():
    nodes = parse("Claude #entropy")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, ScopedLookupNode)
    assert stmt.receiver.name == "Claude"
    assert stmt.symbol.name == "#entropy"


def test_vocabulary_query_variants():
    for source in ("Guardian", "Guardian #"):
        nodes = parse(source)
        assert isinstance(nodes[0], VocabularyQueryNode)
        assert nodes[0].receiver.name == "Guardian"


def test_parse_mixed_statements():
    """Parser handles vocabulary definitions, messages, lookups, and queries."""
    source = '\n'.join([
        'HelloWorld # → [#Sunyata, #Superposition]',
        'Claude # → []',
        'Claude send: #observe to: Copilot',
        'Claude #parse',
        'Codex',
    ])
    nodes = Parser.from_source(source).parse()
    assert len(nodes) == 5
    assert isinstance(nodes[0], VocabularyDefinitionNode)
    assert isinstance(nodes[1], VocabularyDefinitionNode)
    assert isinstance(nodes[2], MessageNode)
    assert isinstance(nodes[3], ScopedLookupNode)
    assert isinstance(nodes[4], VocabularyQueryNode)


def test_parse_sunyata_example():
    source = "\n".join([
        "HelloWorld",
        "HelloWorld #sunyata",
        "Guardian #sunyata",
        "Guardian contemplate: #fire withContext: Awakener 'the flame that was never lit'",
        "Claude #sunyata",
    ])
    nodes = Parser.from_source(source).parse()
    assert len(nodes) == 5
    assert isinstance(nodes[0], VocabularyQueryNode)
    assert isinstance(nodes[1], ScopedLookupNode)
    assert isinstance(nodes[2], ScopedLookupNode)
    assert isinstance(nodes[3], MessageNode)
    assert isinstance(nodes[4], ScopedLookupNode)


def test_root_vocabulary_query():
    """Verify HelloWorld # parses as a VocabularyQueryNode for root receiver."""
    nodes = parse("HelloWorld #")
    assert len(nodes) == 1
    assert isinstance(nodes[0], VocabularyQueryNode)
    assert nodes[0].receiver.name == "HelloWorld"


def test_root_scoped_lookup():
    """Verify HelloWorld #sunyata parses as a ScopedLookupNode for root receiver."""
    nodes = parse("HelloWorld #sunyata")
    assert len(nodes) == 1
    assert isinstance(nodes[0], ScopedLookupNode)
    assert nodes[0].receiver.name == "HelloWorld"
    assert nodes[0].symbol.name == "#sunyata"


def test_missing_vocabulary_bracket_raises():
    source = "Guardian # → [#fire, #vision"
    expect_syntax_error(source, "Expect ']' after symbols")


def test_legacy_dot_lookup_parses():
    nodes = parse("Claude.#entropy")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, ScopedLookupNode)
    assert stmt.receiver.name == "Claude"


def test_bare_identifier_after_receiver_is_unary():
    """Guardian sendVision #fire → unary message (bare symbol is skipped at top level)."""
    nodes = parse("Guardian sendVision")
    assert len(nodes) == 1
    assert isinstance(nodes[0], UnaryMessageNode)
    assert nodes[0].receiver.name == "Guardian"
    assert nodes[0].message == "sendVision"


def test_parse_heading1():
    """# Name parses as a HeadingNode with level 1."""
    nodes = parse("# Claude\n")
    assert len(nodes) == 1
    assert isinstance(nodes[0], HeadingNode)
    assert nodes[0].level == 1
    assert nodes[0].name == "Claude"


def test_parse_heading2_under_heading1():
    """## name under # Name becomes a child HeadingNode."""
    source = "# Claude\n## parse\n## Collision\n"
    nodes = parse(source)
    assert len(nodes) == 1
    h1 = nodes[0]
    assert isinstance(h1, HeadingNode) and h1.level == 1
    assert len(h1.children) == 2
    assert isinstance(h1.children[0], HeadingNode) and h1.children[0].level == 2
    assert h1.children[0].name == "parse"
    assert h1.children[1].name == "Collision"


def test_parse_list_items_as_descriptions():
    """- text lines become DescriptionNode children of headings."""
    source = "# Claude\n- Language designer.\n## parse\n- Decomposing syntax.\n"
    nodes = parse(source)
    assert len(nodes) == 1
    h1 = nodes[0]
    # First child is a description, second is a heading2 with its own description
    assert isinstance(h1.children[0], DescriptionNode)
    assert h1.children[0].text == "Language designer."
    h2 = h1.children[1]
    assert isinstance(h2, HeadingNode) and h2.level == 2
    assert len(h2.children) == 1
    assert isinstance(h2.children[0], DescriptionNode)
    assert h2.children[0].text == "Decomposing syntax."


def test_parse_full_markdown_receiver():
    """Parse a complete Markdown receiver definition."""
    source = (
        "# Claude\n"
        "- Language designer.\n"
        "## parse\n"
        "- Decomposing syntax.\n"
        "## Collision\n"
        "- Namespace collision.\n"
    )
    nodes = parse(source)
    assert len(nodes) == 1
    h1 = nodes[0]
    assert h1.name == "Claude"
    # 1 description + 2 heading2 children
    assert len(h1.children) == 3
    symbols = [c for c in h1.children if isinstance(c, HeadingNode)]
    assert [s.name for s in symbols] == ["parse", "Collision"]


def test_parse_markdown_and_smalltalk_mixed():
    """Markdown receiver defs and Smalltalk messages coexist in one file."""
    source = (
        "# Claude\n"
        "## parse\n"
        'Claude ask: #parse about: #dispatch\n'
    )
    nodes = parse(source)
    assert len(nodes) == 2
    assert isinstance(nodes[0], HeadingNode)
    assert isinstance(nodes[1], MessageNode)


def test_parse_helloworld_hw():
    """vocabularies/HelloWorld.hw self-hosts: parses its own definition."""
    hw_path = Path(__file__).parent.parent / "vocabularies" / "HelloWorld.hw"
    nodes = Parser.from_source(hw_path.read_text()).parse()
    assert len(nodes) == 1
    h1 = nodes[0]
    assert isinstance(h1, HeadingNode)
    assert h1.name == "HelloWorld"
    # All symbol headings from expanded HelloWorld.hw
    symbols = [c for c in h1.children if isinstance(c, HeadingNode) and c.level == 2]
    assert len(symbols) >= 3


def test_parse_html_comment_ignored():
    """HTML comments are skipped, surrounding content parsed normally."""
    source = "<!-- bootstrap -->\nGuardian\n"
    nodes = parse(source)
    assert len(nodes) == 1
    assert isinstance(nodes[0], VocabularyQueryNode)


def test_parse_heading_with_parent():
    """# Claude : Agent parses as HeadingNode with parent='Agent'."""
    nodes = parse("# Claude : Agent\n")
    assert len(nodes) == 1
    h1 = nodes[0]
    assert isinstance(h1, HeadingNode)
    assert h1.level == 1
    assert h1.name == "Claude"
    assert h1.parent == "Agent"


def test_parse_heading_without_parent():
    """# HelloWorld parses as HeadingNode with parent=None."""
    nodes = parse("# HelloWorld\n")
    assert len(nodes) == 1
    h1 = nodes[0]
    assert isinstance(h1, HeadingNode)
    assert h1.level == 1
    assert h1.name == "HelloWorld"
    assert h1.parent is None


def test_parse_heading_with_parent_and_children():
    """# Claude : Agent with child headings still collects children."""
    source = "# Claude : Agent\n## parse\n## synthesize\n"
    nodes = parse(source)
    assert len(nodes) == 1
    h1 = nodes[0]
    assert h1.name == "Claude"
    assert h1.parent == "Agent"
    assert len(h1.children) == 2
    assert h1.children[0].name == "parse"
    assert h1.children[1].name == "synthesize"


def test_heading2_no_parent():
    """## headings never have parent parsing (only level 1)."""
    source = "# Root\n## child : something\n"
    nodes = parse(source)
    assert len(nodes) == 1
    h1 = nodes[0]
    child = h1.children[0]
    assert isinstance(child, HeadingNode) and child.level == 2
    # Level 2 headings preserve the full name including " : something"
    assert child.parent is None


def test_symbol_keyed_message_single():
    """Receiver #symbol: 'value' parses as a MessageNode with symbol key."""
    nodes = parse("Cancelself #observe: 'copy-paste was the first killer GUI feature'")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    assert stmt.receiver.name == "Cancelself"
    assert "#observe" in stmt.arguments
    assert stmt.arguments["#observe"].value == "copy-paste was the first killer GUI feature"


def test_symbol_keyed_message_multiple():
    """Multiple symbol-keyed arguments in one message."""
    nodes = parse("Cancelself #observe: 'X was true' #perhaps: 'Y is true'")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    args = stmt.arguments
    assert "#observe" in args
    assert "#perhaps" in args
    assert args["#observe"].value == "X was true"
    assert args["#perhaps"].value == "Y is true"


def test_symbol_keyed_message_at_syntax():
    """@ receiver syntax works with symbol-keyed messages."""
    nodes = parse("@cancelself #observe: 'text'")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    assert stmt.receiver.name == "Cancelself"
    assert "#observe" in stmt.arguments


def test_symbol_keyed_message_with_annotation():
    """Symbol-keyed message can have a trailing annotation string."""
    nodes = parse("Agent #observe: 'the sky' 'first light'")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    assert stmt.arguments["#observe"].value == "the sky"
    assert stmt.annotation == "first light"


def test_symbol_keyed_mixed_with_identifier():
    """Symbol keys and identifier keys can coexist in one message."""
    nodes = parse("Agent #observe: 'the sky' to: Claude")
    assert len(nodes) == 1
    stmt = nodes[0]
    assert isinstance(stmt, MessageNode)
    assert "#observe" in stmt.arguments
    assert "to" in stmt.arguments


def test_symbol_lookup_still_works():
    """Receiver #symbol without colon still parses as ScopedLookupNode."""
    nodes = parse("Claude #observe")
    assert len(nodes) == 1
    assert isinstance(nodes[0], ScopedLookupNode)
    assert nodes[0].symbol.name == "#observe"


def test_symbol_super_lookup_still_works():
    """Receiver #symbol super still parses as SuperLookupNode."""
    nodes = parse("Claude #observe super")
    assert len(nodes) == 1
    assert isinstance(nodes[0], SuperLookupNode)


if __name__ == "__main__":
    test_vocabulary_definition()
    test_message_with_annotation()
    test_symbol_lookup()
    test_vocabulary_query_variants()
    test_parse_mixed_statements()
    test_parse_sunyata_example()
    test_root_vocabulary_query()
    test_root_scoped_lookup()
    test_missing_vocabulary_bracket_raises()
    test_missing_keyword_colon_raises()
    test_parse_heading1()
    test_parse_heading2_under_heading1()
    test_parse_list_items_as_descriptions()
    test_parse_full_markdown_receiver()
    test_parse_markdown_and_smalltalk_mixed()
    test_parse_helloworld_hw()
    test_parse_html_comment_ignored()
    print("All parser tests passed")
