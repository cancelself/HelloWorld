"""HelloWorld .hw file reader — parser-free, regex-based.

Reads receiver definitions from .hw Markdown files without depending on
the HelloWorld lexer/parser pipeline. This is the bootstrap reader:
the language defines itself, and this module reads those definitions.

Line-by-line parsing:
- H1 (# Name / # Name : Parent) → receiver name + optional parent
- List items before first H2 → identity lines
- H2 (## symbol) → symbol name
- List items after H2 → symbol descriptions
- "double-quoted" text → skipped (Smalltalk-style comments)
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HwSymbol:
    """A symbol definition extracted from a .hw file."""
    name: str                   # "#observe"
    raw_name: str               # "observe"
    descriptions: List[str] = field(default_factory=list)

    @property
    def description(self) -> Optional[str]:
        """Combined description text, or None if no descriptions."""
        return " ".join(self.descriptions) if self.descriptions else None


@dataclass
class HwReceiver:
    """A receiver definition extracted from a .hw file."""
    name: str
    parent: Optional[str] = None
    identity_lines: List[str] = field(default_factory=list)
    symbols: Dict[str, HwSymbol] = field(default_factory=dict)

    @property
    def identity(self) -> Optional[str]:
        """Combined identity text, or None if no identity lines."""
        return " ".join(self.identity_lines) if self.identity_lines else None

    @property
    def vocabulary(self) -> List[str]:
        """Sorted list of symbol names (e.g. ['#act', '#observe'])."""
        return sorted(self.symbols.keys())

    def symbol_description(self, name: str) -> Optional[str]:
        """Get the description for a symbol by its #name."""
        sym = self.symbols.get(name)
        return sym.description if sym else None


def _is_comment_line(line: str) -> bool:
    """Check if a line is a Smalltalk-style double-quoted comment.

    Comments start and end with double quotes on the same line,
    or start with a double quote (multi-line opening).
    """
    stripped = line.strip()
    if stripped.startswith('"') and stripped.endswith('"') and len(stripped) > 1:
        return True
    return False


def _strip_inline_comments(line: str) -> str:
    """Remove inline double-quoted comments from a line."""
    # Simple approach: remove "..." segments
    return re.sub(r'"[^"]*"', '', line)


def read_hw_file(path: str) -> Optional[HwReceiver]:
    """Read a single .hw file and extract the receiver definition.

    Returns None if the file doesn't exist or has no H1 heading.
    """
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        text = f.read()

    lines = text.split("\n")
    receiver = None
    current_symbol = None
    in_comment = False

    for line in lines:
        stripped = line.strip()

        # Handle multi-line comments
        if in_comment:
            if '"' in stripped:
                in_comment = False
            continue

        # Skip single-line comments
        if _is_comment_line(stripped):
            continue

        # Check for multi-line comment start (opens but doesn't close)
        if stripped.startswith('"') and not stripped.endswith('"'):
            in_comment = True
            continue

        # H1: # Name or # Name : Parent
        h1_match = re.match(r'^#\s+(.+)$', line)
        if h1_match and receiver is None:
            heading = h1_match.group(1).strip()
            # Strip inline comments from heading
            heading = _strip_inline_comments(heading).strip()
            # Parse "Name : Parent" or just "Name"
            if ' : ' in heading:
                parts = heading.split(' : ', 1)
                name = parts[0].strip()
                parent = parts[1].strip()
            else:
                name = heading
                parent = None
            receiver = HwReceiver(name=name, parent=parent)
            current_symbol = None
            continue

        # H2: ## symbol_name
        h2_match = re.match(r'^##\s+(.+)$', line)
        if h2_match and receiver is not None:
            raw_name = h2_match.group(1).strip()
            raw_name = _strip_inline_comments(raw_name).strip()
            # Symbol name: add # prefix unless it's the bare # symbol
            if raw_name == '#':
                sym_name = '#'
            elif raw_name.startswith('#'):
                sym_name = raw_name
            else:
                sym_name = f'#{raw_name}'
            current_symbol = HwSymbol(name=sym_name, raw_name=raw_name)
            receiver.symbols[sym_name] = current_symbol
            continue

        # List item: - description text
        list_match = re.match(r'^-\s+(.+)$', stripped)
        if list_match and receiver is not None:
            text_content = list_match.group(1).strip()
            if current_symbol is not None:
                # Description belongs to current symbol
                current_symbol.descriptions.append(text_content)
            else:
                # Description before any H2 → identity line
                receiver.identity_lines.append(text_content)
            continue

    return receiver


def read_hw_directory(directory: str) -> Dict[str, HwReceiver]:
    """Read all .hw files in a directory and return a dict of receivers.

    Keys are receiver names, values are HwReceiver instances.
    """
    receivers = {}
    if not os.path.isdir(directory):
        return receivers

    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.hw'):
            path = os.path.join(directory, filename)
            receiver = read_hw_file(path)
            if receiver is not None:
                receivers[receiver.name] = receiver

    return receivers


def save_hw_symbol(path: str, symbol_name: str, description: str = None):
    """Append a new symbol definition to a .hw file.

    Adds a ## heading and optional description at the end of the file.
    Does not check for duplicates — caller should verify first.
    """
    raw_name = symbol_name.lstrip('#') if symbol_name != '#' else '#'

    with open(path, "a") as f:
        f.write(f"## {raw_name}\n")
        if description:
            f.write(f"- {description}\n")
        else:
            f.write("- (learned through dialogue)\n")
