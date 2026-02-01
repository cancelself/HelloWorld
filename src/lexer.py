"""HelloWorld Lexer - Tokenizes HelloWorld source code."""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    RECEIVER = auto()      # Capitalized bare word (e.g. Guardian, Claude)
    SYMBOL = auto()        # #name
    DOT = auto()           # .
    HASH = auto()          # #
    ARROW = auto()         # →
    LBRACKET = auto()      # [
    RBRACKET = auto()      # ]
    COMMA = auto()         # ,
    COLON = auto()         # :
    STRING = auto()        # 'text'
    IDENTIFIER = auto()    # unquoted text
    NUMBER = auto()        # 123, 7.days
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            
            if self.pos >= len(self.source):
                break
            
            if self._match_symbol():
                continue
            if self._match_arrow():
                continue
            if self._match_string():
                continue
            if self._match_number():
                continue
            if self._match_punctuation():
                continue
            if self._match_identifier():
                continue
            
            raise SyntaxError(f"Unexpected character '{self.source[self.pos]}' at line {self.line}, column {self.column}")
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            if self.source[self.pos] in ' \t':
                self._advance()
            elif self.source[self.pos] == '\n':
                self._advance()
                self.line += 1
                self.column = 1
            elif self.source[self.pos] == '"':
                # Smalltalk-style "double-quote" comments
                self._advance()
                while self.pos < len(self.source) and self.source[self.pos] != '"':
                    if self.source[self.pos] == '\n':
                        self.line += 1
                        self.column = 0
                    self._advance()
                if self.pos < len(self.source):
                    self._advance()  # consume closing "
            elif (
                self.source[self.pos] == '#'
                and self.pos + 1 < len(self.source)
                and self.source[self.pos + 1] == ' '
                and self.column == 1
            ):
                # Legacy line comments: # text
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self._advance()
            else:
                break
    
    def _match_symbol(self) -> bool:
        if self.source[self.pos] == '#':
            start = self.pos
            col = self.column
            self._advance()
            if self.pos < len(self.source) and self.source[self.pos] not in ' \t\n.,:[]→':
                name = self._read_identifier()
                self.tokens.append(Token(TokenType.SYMBOL, f'#{name}', self.line, col))
            else:
                self.tokens.append(Token(TokenType.HASH, '#', self.line, col))
            return True
        return False
    
    def _match_arrow(self) -> bool:
        if self.source[self.pos] == '→':
            self.tokens.append(Token(TokenType.ARROW, '→', self.line, self.column))
            self._advance()
            return True
        return False
    
    def _match_string(self) -> bool:
        if self.source[self.pos] == "'":
            col = self.column
            self._advance()
            start = self.pos
            while self.pos < len(self.source) and self.source[self.pos] != "'":
                self._advance()
            value = self.source[start:self.pos]
            if self.pos < len(self.source):
                self._advance()
            self.tokens.append(Token(TokenType.STRING, value, self.line, col))
            return True
        return False
    
    def _match_number(self) -> bool:
        if self.source[self.pos].isdigit():
            col = self.column
            start = self.pos
            while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
                self._advance()
            if self.pos < len(self.source) and self.source[self.pos].isalpha():
                while self.pos < len(self.source) and self.source[self.pos].isalnum():
                    self._advance()
            value = self.source[start:self.pos]
            self.tokens.append(Token(TokenType.NUMBER, value, self.line, col))
            return True
        return False
    
    def _match_punctuation(self) -> bool:
        char = self.source[self.pos]
        token_map = {
            '.': TokenType.DOT,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
        }
        if char in token_map:
            self.tokens.append(Token(token_map[char], char, self.line, self.column))
            self._advance()
            return True
        return False
    
    def _match_identifier(self) -> bool:
        if self.source[self.pos].isalpha() or self.source[self.pos] == '_':
            col = self.column
            name = self._read_identifier()
            # Capitalized words are receivers (Smalltalk class convention)
            if name[0].isupper():
                self.tokens.append(Token(TokenType.RECEIVER, name, self.line, col))
            else:
                self.tokens.append(Token(TokenType.IDENTIFIER, name, self.line, col))
            return True
        return False
    
    def _read_identifier(self) -> str:
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] in '_—'):
            self._advance()
        return self.source[start:self.pos]
    
    def _advance(self):
        self.pos += 1
        self.column += 1
