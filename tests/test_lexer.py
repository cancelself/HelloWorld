"""Tests for the HelloWorld lexer."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from lexer import Lexer, TokenType


def test_receiver():
    lexer = Lexer("@guardian")
    tokens = lexer.tokenize()
    assert len(tokens) == 2  # RECEIVER + EOF
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "@guardian"


def test_symbol():
    lexer = Lexer("#fire")
    tokens = lexer.tokenize()
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.SYMBOL
    assert tokens[0].value == "#fire"


def test_message():
    lexer = Lexer("@guardian sendVision: #entropy")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.COLON
    assert tokens[3].type == TokenType.SYMBOL


def test_vocabulary_query():
    lexer = Lexer("@guardian.#")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.HASH


def test_string():
    lexer = Lexer("'you burned bright'")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "you burned bright"


if __name__ == "__main__":
    test_receiver()
    test_symbol()
    test_message()
    test_vocabulary_query()
    test_string()
    print("✓ All lexer tests passed")
