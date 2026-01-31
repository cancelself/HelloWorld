"""HelloWorld Parser - Builds an AST from lexer tokens."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from lexer import Lexer, Token, TokenType


class ValueType(Enum):
    SYMBOL = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    RECEIVER = auto()


@dataclass
class Value:
    kind: ValueType
    value: str


@dataclass
class Keyword:
    name: str
    value: Value


class Statement:
    """Base class for parsed statements."""


@dataclass
class VocabularyDefinition(Statement):
    receiver: str
    symbols: List[str]


@dataclass
class VocabularyQuery(Statement):
    receiver: str


@dataclass
class SymbolLookup(Statement):
    receiver: str
    symbol: str


@dataclass
class Message(Statement):
    receiver: str
    keywords: List[Keyword]
    annotation: Optional[str] = None


class Parser:
    """Recursive-descent parser that mirrors the lexer token stream."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    @classmethod
    def from_source(cls, source: str) -> "Parser":
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        return cls(tokens)

    def parse(self) -> List[Statement]:
        statements: List[Statement] = []
        while not self._check(TokenType.EOF):
            if self._peek().type == TokenType.EOF:
                break
            statements.append(self._parse_statement())
        return statements

    def _parse_statement(self) -> Statement:
        receiver_token = self._consume(TokenType.RECEIVER, "Expected receiver")
        if self._match(TokenType.DOT):
            if self._match(TokenType.HASH):
                if self._match(TokenType.ARROW):
                    symbols = self._parse_symbol_list()
                    return VocabularyDefinition(receiver_token.value, symbols)
                return VocabularyQuery(receiver_token.value)
            if self._check(TokenType.SYMBOL):
                symbol = self._advance()
                return SymbolLookup(receiver_token.value, symbol.value)
            raise SyntaxError("Expected # or #symbol after receiver.")
        if self._check(TokenType.IDENTIFIER):
            return self._parse_message(receiver_token.value)
        return VocabularyQuery(receiver_token.value)

    def _parse_symbol_list(self) -> List[str]:
        self._consume(TokenType.LBRACKET, "Expected '[' to start vocabulary list")
        symbols: List[str] = []
        while not self._match(TokenType.RBRACKET):
            token = self._consume(TokenType.SYMBOL, "Expected #symbol inside vocabulary list")
            symbols.append(token.value)
            self._match(TokenType.COMMA)
        return symbols

    def _parse_message(self, receiver: str) -> Message:
        keywords: List[Keyword] = []
        while self._check(TokenType.IDENTIFIER):
            name_token = self._advance()
            self._consume(TokenType.COLON, "Expected ':' after keyword name")
            value = self._parse_value()
            keywords.append(Keyword(name=name_token.value, value=value))
        annotation = None
        if self._check(TokenType.STRING):
            annotation = self._advance().value
        return Message(receiver=receiver, keywords=keywords, annotation=annotation)

    def _parse_value(self) -> Value:
        token = self._advance()
        if token.type == TokenType.SYMBOL:
            return Value(ValueType.SYMBOL, token.value)
        if token.type == TokenType.IDENTIFIER:
            return Value(ValueType.IDENTIFIER, token.value)
        if token.type == TokenType.NUMBER:
            return Value(ValueType.NUMBER, token.value)
        if token.type == TokenType.STRING:
            return Value(ValueType.STRING, token.value)
        if token.type == TokenType.RECEIVER:
            return Value(ValueType.RECEIVER, token.value)
        raise SyntaxError(f"Unexpected value token {token.type}")

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self.pos >= len(self.tokens):
            return False
        return self.tokens[self.pos].type == token_type

    def _advance(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _peek(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise SyntaxError(message)
