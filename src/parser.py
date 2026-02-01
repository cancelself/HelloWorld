"""HelloWorld Parser - Converts tokens into an Abstract Syntax Tree (AST).
Managed by: Gemini
"""

from typing import List, Optional, Union, Dict
from lexer import Lexer, Token, TokenType
from ast_nodes import (
    Node, SymbolNode, ReceiverNode, LiteralNode, 
    VocabularyQueryNode, ScopedLookupNode, MessageNode, VocabularyDefinitionNode
)

# Compatibility exports for tests
Message = MessageNode
SymbolLookup = ScopedLookupNode
VocabularyDefinition = VocabularyDefinitionNode
VocabularyQuery = VocabularyQueryNode

# ValueType is used in old test API
from enum import Enum, auto

class ValueType(Enum):
    SYMBOL = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    RECEIVER = auto()

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    @classmethod
    def from_source(cls, source: str) -> 'Parser':
        """Create a Parser from source code."""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        return cls(tokens)

    def parse(self) -> List[Node]:
        nodes = []
        while not self._is_at_end():
            node = self._parse_statement()
            if node:
                nodes.append(node)
        return nodes

    def _parse_statement(self) -> Optional[Node]:
        if self._match(TokenType.RECEIVER):
            receiver_token = self._previous()
            receiver = ReceiverNode(receiver_token.value)

            # Check for query or definition: @name.
            if self._match(TokenType.DOT):
                if self._match(TokenType.HASH):
                    # Definition or Vocabulary Query: @name.#
                    if self._match(TokenType.ARROW):
                        # Definition: @name.# → [#symbol, ...]
                        return self._parse_vocabulary_definition(receiver)
                    else:
                        # Query: @name.#
                        return VocabularyQueryNode(receiver)
                elif self._match(TokenType.SYMBOL):
                    # Scoped Lookup: @name.#symbol
                    symbol_token = self._previous()
                    return ScopedLookupNode(receiver, SymbolNode(symbol_token.value))
            
            # Message Passing: @name action: value
            if self._check(TokenType.IDENTIFIER):
                return self._parse_message(receiver)
            
            # Bare receiver: @name
            return VocabularyQueryNode(receiver)

        # Skip tokens we don't recognize as starts of statements for now
        self._advance()
        return None

    def _parse_vocabulary_definition(self, receiver: ReceiverNode) -> VocabularyDefinitionNode:
        self._consume(TokenType.LBRACKET, "Expect '[' after '→'")
        symbols = []
        if not self._check(TokenType.RBRACKET):
            while True:
                self._consume(TokenType.SYMBOL, "Expect symbol in vocabulary list")
                symbols.append(SymbolNode(self._previous().value))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RBRACKET, "Expect ']' after symbols")
        return VocabularyDefinitionNode(receiver, symbols)

    def _parse_message(self, receiver: ReceiverNode) -> MessageNode:
        arguments = {}
        while self._match(TokenType.IDENTIFIER):
            key = self._previous().value
            self._consume(TokenType.COLON, f"Expect ':' after keyword '{key}'")
            value = self._parse_value()
            arguments[key] = value
        
        annotation = None
        if self._match(TokenType.STRING):
            annotation = self._previous().value
            
        return MessageNode(receiver, arguments, annotation)

    def _parse_value(self) -> Node:
        if self._match(TokenType.SYMBOL):
            return SymbolNode(self._previous().value)
        if self._match(TokenType.RECEIVER):
            return ReceiverNode(self._previous().value)
        if self._match(TokenType.NUMBER):
            return LiteralNode(self._previous().value)
        if self._match(TokenType.STRING):
            return LiteralNode(self._previous().value)
        if self._match(TokenType.IDENTIFIER):
            return LiteralNode(self._previous().value)
        
        token = self._peek()
        raise SyntaxError(f"Unexpected token {token.type} at line {token.line}, column {token.column}")

    # Helper methods
    def _match(self, *types: TokenType) -> bool:
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False

    def _consume(self, type: TokenType, message: str):
        if self._check(type):
            return self._advance()
        token = self._peek()
        raise SyntaxError(f"{message} (line {token.line}, column {token.column})")

    def _check(self, type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]
