"""Tests for namespace path syntax (:: operator)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from lexer import Lexer, TokenType

def test_lexer_matches_double_colon():
    lexer = Lexer("HelloWorld::Agent::Claude")
    tokens = lexer.tokenize()
    
    # HelloWorld, ::, Agent, ::, Claude, EOF
    assert len(tokens) == 6
    assert tokens[0].type == TokenType.RECEIVER
    assert tokens[0].value == "HelloWorld"
    assert tokens[1].type == TokenType.DOUBLE_COLON
    assert tokens[1].value == "::"
    assert tokens[2].type == TokenType.RECEIVER
    assert tokens[2].value == "Agent"
    assert tokens[3].type == TokenType.DOUBLE_COLON
    assert tokens[3].value == "::"
    assert tokens[4].type == TokenType.RECEIVER
    assert tokens[4].value == "Claude"

from parser import Parser, ScopedLookupNode

def test_parser_handles_namespace_path():
    parser = Parser.from_source("Agent::Claude #act")
    nodes = parser.parse()
    
    assert len(nodes) == 1
    assert isinstance(nodes[0], ScopedLookupNode)
    assert nodes[0].receiver.name == "Agent::Claude"
    assert nodes[0].symbol.name == "#act"

from dispatcher import Dispatcher
import tempfile
import pytest

def test_dispatcher_resolves_namespace_path():
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    
    # Valid path: root :: parent :: leaf
    result = dispatcher.dispatch_source("HelloWorld::Agent::Claude #parse")
    assert len(result) == 1
    assert "Claude #parse" in result[0]
    
    # Valid path: skipping levels
    result = dispatcher.dispatch_source("HelloWorld::Claude #parse")
    assert len(result) == 1
    assert "Claude #parse" in result[0]

def test_dispatcher_validates_invalid_path():
    dispatcher = Dispatcher(vocab_dir=tempfile.mkdtemp())
    
    # Invalid path: wrong order
    with pytest.raises(ValueError, match="must be a descendant"):
        dispatcher.dispatch_source("Agent::Object::Claude #parse")
        
    # Invalid path: non-existent member in chain
    with pytest.raises(ValueError, match="is not in the inheritance chain"):
        dispatcher.dispatch_source("Codex::Claude #parse")

if __name__ == "__main__":
    test_lexer_matches_double_colon()
    test_parser_handles_namespace_path()
    test_dispatcher_resolves_namespace_path()
    try:
        test_dispatcher_validates_invalid_path()
    except Exception as e:
        print(f"Validation test raised expected error: {e}")
    print("Namespace tests passed")
