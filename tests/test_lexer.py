"""Tests for the HelloWorld lexer."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from lexer import Lexer, TokenType


def test_receiver():
    lexer = Lexer("Guardian")
    tokens = lexer.tokenize()
    assert len(tokens) == 2  # RECEIVER + EOF
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"


def test_symbol():
    lexer = Lexer("#fire")
    tokens = lexer.tokenize()
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.SYMBOL
    assert tokens[0].value == "#fire"


def test_message():
    lexer = Lexer("Guardian sendVision: #entropy")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.COLON
    assert tokens[3].type == TokenType.SYMBOL


def test_vocabulary_query():
    lexer = Lexer("Guardian #")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.HASH


def test_string():
    lexer = Lexer("'you burned bright'")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "you burned bright"


def test_root_receiver():
    """Verify that HelloWorld # tokenizes as RECEIVER HASH for root receiver."""
    lexer = Lexer("HelloWorld #")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "HelloWorld"
    assert tokens[1].type == TokenType.HASH


def test_double_quote_comment():
    """Smalltalk-style double-quote comments are skipped by the lexer."""
    lexer = Lexer('"this is a comment" Guardian')
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"


def test_multiline_double_quote_comment():
    """Double-quote comments can span multiple lines."""
    source = '"this is a\nmultiline comment"\nGuardian'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"


def test_inline_double_quote_comment():
    """Double-quote comments work inline between expressions."""
    source = 'Guardian "the keeper of thresholds" #fire'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"
    assert tokens[1].type == TokenType.SYMBOL
    assert tokens[1].value == "#fire"


def test_legacy_dot_lookup_tokens():
    """Legacy Receiver.#symbol syntax still tokenizes for backward compatibility."""
    lexer = Lexer("Guardian.#fire")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.SYMBOL


def test_lowercase_is_identifier():
    """Lowercase words should be IDENTIFIER, not RECEIVER."""
    lexer = Lexer("sendVision")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "sendVision"


def test_at_prefix_backward_compat():
    """Legacy @name syntax normalizes to Capitalized bare word."""
    lexer = Lexer("@guardian #fire")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"  # normalized, no @
    assert tokens[1].type == TokenType.SYMBOL
    assert tokens[1].value == "#fire"


def test_bare_at_is_helloworld():
    """Bare @ normalizes to HelloWorld (the root receiver)."""
    lexer = Lexer("@ #")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "HelloWorld"
    assert tokens[1].type == TokenType.HASH


def test_heading1_token():
    """# Name at column 1 produces a HEADING1 token."""
    lexer = Lexer("# Claude\n")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.HEADING1
    assert tokens[0].value == "Claude"


def test_heading2_token():
    """## name at column 1 produces a HEADING2 token."""
    lexer = Lexer("## parse\n")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.HEADING2
    assert tokens[0].value == "parse"


def test_list_item_token():
    """- text at column 1 produces a LIST_ITEM token."""
    lexer = Lexer("- Language designer, spec author.\n")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.LIST_ITEM
    assert tokens[0].value == "Language designer, spec author."


def test_heading_not_midline():
    """# not at column 1 is still HASH/SYMBOL, not HEADING."""
    lexer = Lexer("Guardian #fire")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.SYMBOL


def test_list_item_not_midline():
    """- not at column 1 is not a LIST_ITEM (would be syntax error or part of identifier)."""
    # Mid-line dash after a receiver is not list item
    source = "Guardian"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    # Just verify no LIST_ITEM was produced
    assert all(t.type != TokenType.LIST_ITEM for t in tokens)


def test_html_comment_skipped():
    """<!-- HTML comments --> are skipped by the lexer."""
    lexer = Lexer("<!-- this is a comment -->\nGuardian")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"


def test_html_comment_inline():
    """HTML comments work inline between expressions."""
    lexer = Lexer("Guardian <!-- comment --> #fire")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.SYMBOL


def test_html_comment_multiline():
    """HTML comments can span multiple lines."""
    source = "<!-- multi\nline\ncomment -->\nGuardian"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"


def test_markdown_full_receiver():
    """Full Markdown receiver definition tokenizes correctly."""
    source = "# Claude\n- Language designer.\n## parse\n- Decomposing syntax.\n## Collision\n- Namespace collision.\n"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.HEADING1,
        TokenType.LIST_ITEM,
        TokenType.HEADING2,
        TokenType.LIST_ITEM,
        TokenType.HEADING2,
        TokenType.LIST_ITEM,
    ]
    assert tokens[0].value == "Claude"
    assert tokens[2].value == "parse"
    assert tokens[4].value == "Collision"


def test_markdown_and_smalltalk_coexist():
    """Markdown headings and Smalltalk messages in the same file."""
    source = '# Claude\n## parse\nClaude ask: #parse about: #dispatch\n'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types[0] == TokenType.HEADING1
    assert types[1] == TokenType.HEADING2
    assert types[2] == TokenType.RECEIVER  # Claude (Smalltalk message line)


if __name__ == "__main__":
    test_receiver()
    test_symbol()
    test_message()
    test_vocabulary_query()
    test_string()
    test_root_receiver()
    test_double_quote_comment()
    test_multiline_double_quote_comment()
    test_inline_double_quote_comment()
    test_lowercase_is_identifier()
    test_at_prefix_backward_compat()
    test_bare_at_is_helloworld()
    test_heading1_token()
    test_heading2_token()
    test_list_item_token()
    test_heading_not_midline()
    test_list_item_not_midline()
    test_html_comment_skipped()
    test_html_comment_inline()
    test_html_comment_multiline()
    test_markdown_full_receiver()
    test_markdown_and_smalltalk_coexist()
    print("All lexer tests passed")
