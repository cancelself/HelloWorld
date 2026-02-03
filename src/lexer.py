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
    DOUBLE_COLON = auto()  # ::
    COLON = auto()         # :
    STRING = auto()        # 'text'
    IDENTIFIER = auto()    # unquoted text
    SUPER = auto()         # super (reserved keyword)
    NUMBER = auto()        # 123, 7.days
    NEWLINE = auto()
    HEADING1 = auto()      # # Name  (at column 1)
    HEADING2 = auto()      # ## name (at column 1)
    LIST_ITEM = auto()     # - text  (at column 1)
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

            if self._match_markdown():
                continue
            if self._match_receiver():
                continue
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

    def _match_markdown(self) -> bool:
        """Recognize Markdown structure at column 1: headings and list items."""
        if self.column != 1:
            return False

        # ## name (HEADING2 — must check before single #)
        if (self.source[self.pos:self.pos + 2] == '##'
                and self.pos + 2 < len(self.source)
                and self.source[self.pos + 2] == ' '):
            col = self.column
            self.pos += 3  # skip "## "
            self.column += 3
            start = self.pos
            while self.pos < len(self.source) and self.source[self.pos] != '\n':
                self._advance()
            value = self.source[start:self.pos].strip()
            self.tokens.append(Token(TokenType.HEADING2, value, self.line, col))
            return True

        # # Name (HEADING1 — only when followed by space then text)
        if (self.source[self.pos] == '#'
                and self.pos + 1 < len(self.source)
                and self.source[self.pos + 1] == ' '):
            col = self.column
            self.pos += 2  # skip "# "
            self.column += 2
            start = self.pos
            while self.pos < len(self.source) and self.source[self.pos] != '\n':
                self._advance()
            value = self.source[start:self.pos].strip()
            self.tokens.append(Token(TokenType.HEADING1, value, self.line, col))
            return True

        # - text (LIST_ITEM)
        if (self.source[self.pos] == '-'
                and self.pos + 1 < len(self.source)
                and self.source[self.pos + 1] == ' '):
            col = self.column
            self.pos += 2  # skip "- "
            self.column += 2
            start = self.pos
            while self.pos < len(self.source) and self.source[self.pos] != '\n':
                self._advance()
            value = self.source[start:self.pos].strip()
            self.tokens.append(Token(TokenType.LIST_ITEM, value, self.line, col))
            return True

        return False

    def _match_receiver(self) -> bool:
        """Legacy @name syntax — normalize to Capitalized bare word."""
        if self.source[self.pos] == '@':
            start = self.pos
            col = self.column
            self._advance()
            if self.pos < len(self.source) and (self.source[self.pos].isalpha() or self.source[self.pos] == '_'):
                name = self._read_identifier()
                # Normalize: @guardian → Guardian (matches bare-word convention)
                normalized = name[0].upper() + name[1:] if name else name
                self.tokens.append(Token(TokenType.RECEIVER, normalized, self.line, col))
            else:
                # Bare @ → HelloWorld (the root receiver)
                self.tokens.append(Token(TokenType.RECEIVER, 'HelloWorld', self.line, col))
            return True
        return False
    
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
            elif self.source[self.pos:self.pos + 4] == '<!--':
                # HTML comment: <!-- ... -->
                self.pos += 4
                self.column += 4
                while self.pos < len(self.source):
                    if self.source[self.pos:self.pos + 3] == '-->':
                        self.pos += 3
                        self.column += 3
                        break
                    if self.source[self.pos] == '\n':
                        self.line += 1
                        self.column = 0
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
        
        # Check for double-char tokens first
        if char == ':' and self.pos + 1 < len(self.source) and self.source[self.pos+1] == ':':
            self.tokens.append(Token(TokenType.DOUBLE_COLON, '::', self.line, self.column))
            self._advance()
            self._advance()
            return True

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
    
    # Reserved keywords that are not identifiers
    KEYWORDS = {'super': TokenType.SUPER}

    def _match_identifier(self) -> bool:
        if self.source[self.pos].isalpha() or self.source[self.pos] == '_':
            col = self.column
            name = self._read_identifier()
            # Check reserved keywords first
            if name in self.KEYWORDS:
                self.tokens.append(Token(self.KEYWORDS[name], name, self.line, col))
            # Capitalized words are receivers (Smalltalk class convention)
            elif name[0].isupper():
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
