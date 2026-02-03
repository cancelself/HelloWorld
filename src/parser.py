"""HelloWorld Parser - Converts tokens into an Abstract Syntax Tree (AST).
Managed by: Gemini
"""

from typing import List, Optional, Union, Dict
from lexer import Lexer, Token, TokenType
from ast_nodes import (
    Node, SymbolNode, ReceiverNode, LiteralNode,
    VocabularyQueryNode, ScopedLookupNode, MessageNode, VocabularyDefinitionNode,
    HeadingNode, DescriptionNode, UnaryMessageNode, SuperLookupNode
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
        # Markdown heading: # Name (receiver declaration)
        if self._match(TokenType.HEADING1):
            return self._parse_heading(1)

        # Markdown heading: ## name (symbol definition, but can appear top-level)
        if self._match(TokenType.HEADING2):
            return self._parse_heading(2)

        # Markdown list item: - text (description, can appear top-level)
        if self._match(TokenType.LIST_ITEM):
            return DescriptionNode(self._previous().value)

        if self._check(TokenType.RECEIVER):
            receiver = self._parse_receiver()

            # Scoped lookups / queries accept either legacy dot syntax or space-separated form.
            if self._check(TokenType.DOT) or self._check(TokenType.HASH) or self._check(TokenType.SYMBOL):
                suffix_node = self._parse_receiver_suffix(receiver)
                if suffix_node:
                    return suffix_node

            # Message Passing: Name action: value  OR  Unary: Name action [super]
            if self._check(TokenType.IDENTIFIER):
                if self._peek_is_keyword_message():
                    return self._parse_message(receiver)
                else:
                    return self._parse_unary_message(receiver)

            # Bare receiver: Name
            return VocabularyQueryNode(receiver)

        # Bare symbol at top level: #HelloWorld, #Claude, etc.
        if self._match(TokenType.SYMBOL):
            return SymbolNode(self._previous().value)

        # Skip tokens we don't recognize as starts of statements for now
        self._advance()
        return None

    def _parse_receiver(self) -> ReceiverNode:
        """Parse a receiver name or a namespace path: HelloWorld::Agent::Claude"""
        self._consume(TokenType.RECEIVER, "Expect receiver name")
        name = self._previous().value
        while self._match(TokenType.DOUBLE_COLON):
            self._consume(TokenType.RECEIVER, "Expect receiver name after '::'")
            name += f"::{self._previous().value}"
        return ReceiverNode(name)

    def _parse_heading(self, level: int) -> HeadingNode:
        """Parse a Markdown heading and its children (list items, sub-headings)."""
        raw = self._previous().value
        parent = None
        if level == 1 and ' : ' in raw:
            parts = raw.split(' : ', 1)
            name = parts[0].strip()
            parent = parts[1].strip()
        else:
            name = raw
        node = HeadingNode(level=level, name=name, parent=parent)

        # Collect children: list items and (for level 1) sub-headings
        while not self._is_at_end():
            if self._check(TokenType.LIST_ITEM):
                self._advance()
                node.children.append(DescriptionNode(self._previous().value))
            elif level == 1 and self._check(TokenType.HEADING2):
                self._advance()
                node.children.append(self._parse_heading(2))
            else:
                # Stop when we hit a non-child token
                break

        return node

    def _peek_is_keyword_message(self) -> bool:
        """Look ahead to determine if the current IDENTIFIER starts a keyword message.

        A keyword message has the form: identifier COLON value ...
        A unary message is just: identifier [super]
        """
        # Save position
        saved = self.pos
        try:
            # We're currently at an IDENTIFIER token — peek past it
            if not self._check(TokenType.IDENTIFIER):
                return False
            self._advance()  # consume the IDENTIFIER
            # If a COLON follows, it's a keyword message
            return self._check(TokenType.COLON)
        finally:
            self.pos = saved

    def _parse_unary_message(self, receiver: ReceiverNode) -> UnaryMessageNode:
        """Parse a unary message: Receiver identifier [super]"""
        self._advance()  # consume IDENTIFIER
        message = self._previous().value
        is_super = False
        if self._match(TokenType.SUPER):
            is_super = True
        return UnaryMessageNode(receiver, message, is_super)

    def _parse_vocabulary_definition(self, receiver: ReceiverNode) -> VocabularyDefinitionNode:
        self._consume(TokenType.LBRACKET, "Expect '[' after '→'")
        symbols = []
        if not self._check(TokenType.RBRACKET):
            while True:
                # Handle both SYMBOL tokens and bare HASH (#) as a symbol
                if self._match(TokenType.SYMBOL):
                    symbols.append(SymbolNode(self._previous().value))
                elif self._match(TokenType.HASH):
                    # Bare # is the symbol for "symbol"
                    symbols.append(SymbolNode("#"))
                else:
                    token = self._peek()
                    raise SyntaxError(f"Expect symbol in vocabulary list (line {token.line}, column {token.column})")
                
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
        if self._check(TokenType.RECEIVER):
            return self._parse_receiver()
        if self._match(TokenType.NUMBER):
            return LiteralNode(self._previous().value)
        if self._match(TokenType.STRING):
            return LiteralNode(self._previous().value)
        if self._match(TokenType.IDENTIFIER):
            return LiteralNode(self._previous().value)
        
        token = self._peek()
        raise SyntaxError(f"Unexpected token {token.type} at line {token.line}, column {token.column}")

    def _parse_receiver_suffix(self, receiver: ReceiverNode) -> Optional[Node]:
        """Parse vocabulary queries / definitions / scoped lookups after a receiver."""
        consumed_dot = self._match(TokenType.DOT)

        if self._match(TokenType.HASH):
            if self._match(TokenType.ARROW):
                return self._parse_vocabulary_definition(receiver)
            return VocabularyQueryNode(receiver)

        if self._match(TokenType.SYMBOL):
            symbol_token = self._previous()
            # If followed by `super`, it's a typedef super lookup
            if self._match(TokenType.SUPER):
                return SuperLookupNode(receiver, SymbolNode(symbol_token.value))
            return ScopedLookupNode(receiver, SymbolNode(symbol_token.value))

        if consumed_dot:
            token = self._peek()
            raise SyntaxError(f"Expect '#' or '#symbol' after '.' (line {token.line}, column {token.column})")
        return None

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
