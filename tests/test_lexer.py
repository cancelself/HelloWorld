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
    lexer = Lexer("Guardian.#")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.HASH


def test_string():
    lexer = Lexer("'you burned bright'")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "you burned bright"


def test_root_receiver():
    """Verify that HelloWorld.# tokenizes as RECEIVER DOT HASH for root receiver."""
    lexer = Lexer("HelloWorld.#")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "HelloWorld"
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.HASH


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
    source = 'Guardian "the keeper of thresholds" .#fire'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.SYMBOL
    assert tokens[2].value == "#fire"


def test_lowercase_is_identifier():
    """Lowercase words should be IDENTIFIER, not RECEIVER."""
    lexer = Lexer("sendVision")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "sendVision"


def test_at_prefix_backward_compat():
    """Legacy @name syntax normalizes to Capitalized bare word."""
    lexer = Lexer("@guardian.#fire")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "Guardian"  # normalized, no @
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.SYMBOL
    assert tokens[2].value == "#fire"


def test_bare_at_is_helloworld():
    """Bare @ normalizes to HelloWorld (the root receiver)."""
    lexer = Lexer("@.#")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "HelloWorld"
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.HASH


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
    print("All lexer tests passed")
