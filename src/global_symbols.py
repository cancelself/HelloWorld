"""Global Symbol Registry - HelloWorld # namespace

Loads global symbols from vocabularies/HelloWorld.hw at import time.
Falls back to a minimal hardcoded set if the file is missing or unparseable.
"""

import os
import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class GlobalSymbol:
    """A symbol in the global HelloWorld # namespace."""
    name: str
    definition: str
    domain: str
    wikidata_id: Optional[str] = None
    wikipedia_url: Optional[str] = None

    def __str__(self) -> str:
        parts = [self.definition]
        if self.domain:
            parts.append(f"[{self.domain}]")
        if self.wikidata_id:
            parts.append(f"({self.wikidata_id})")
        return " ".join(parts)


# Regex for parsing inline metadata from description text
_DOMAIN_RE = re.compile(r'\[([^\]]+)\]\s*$')
_WIKIDATA_RE = re.compile(r'\(Q(\d+)\)')


def _parse_description(text: str):
    """Extract definition, domain, and wikidata_id from a description line.

    Convention: "Description text [domain] (Q12345)"
    """
    domain = ""
    wikidata_id = None

    # Extract (Q-number) first — it may follow the [domain]
    wikidata_match = _WIKIDATA_RE.search(text)
    if wikidata_match:
        wikidata_id = f"Q{wikidata_match.group(1)}"
        text = text[:wikidata_match.start()].rstrip()

    # Extract [domain]
    domain_match = _DOMAIN_RE.search(text)
    if domain_match:
        domain = domain_match.group(1)
        text = text[:domain_match.start()].rstrip()

    return text, domain, wikidata_id


def _load_from_hw(path: str) -> Dict[str, GlobalSymbol]:
    """Load global symbols from a .hw vocabulary file.

    Parses the file using the HelloWorld parser and walks the AST:
    - Level-1 HeadingNode is the root receiver (HelloWorld)
    - Level-2 HeadingNode children are symbol definitions
    - DescriptionNode children of each heading carry the definition text
    """
    from parser import Parser
    from ast_nodes import HeadingNode, DescriptionNode

    text = open(path, 'r').read()
    nodes = Parser.from_source(text).parse()

    symbols: Dict[str, GlobalSymbol] = {}

    for node in nodes:
        if not isinstance(node, HeadingNode) or node.level != 1:
            continue

        # The level-1 heading is the root receiver name
        root_name = node.name  # "HelloWorld"

        for child in node.children:
            if isinstance(child, DescriptionNode):
                # Root description — create the #HelloWorld symbol
                definition, domain, wikidata_id = _parse_description(child.text)
                sym_name = f"#{root_name}"
                symbols[sym_name] = GlobalSymbol(
                    name=sym_name,
                    definition=definition,
                    domain=domain or "programming languages",
                    wikidata_id=wikidata_id,
                )

            elif isinstance(child, HeadingNode) and child.level == 2:
                # Level-2 heading — symbol name
                raw_name = child.name  # e.g. "#", "Object", "parse"
                if raw_name == "#":
                    sym_name = "#"
                else:
                    sym_name = f"#{raw_name}"

                # Get description from first DescriptionNode child
                desc_text = ""
                for gc in child.children:
                    if isinstance(gc, DescriptionNode):
                        desc_text = gc.text
                        break

                definition, domain, wikidata_id = _parse_description(desc_text)
                symbols[sym_name] = GlobalSymbol(
                    name=sym_name,
                    definition=definition,
                    domain=domain,
                    wikidata_id=wikidata_id,
                )

    return symbols


def _fallback_symbols() -> Dict[str, GlobalSymbol]:
    """Empty fallback. All symbols must live in .hw files."""
    return {}


def _init_symbols() -> Dict[str, GlobalSymbol]:
    """Load symbols from .hw file with fallback."""
    # Resolve path relative to this file: src/ -> repo root -> vocabularies/
    hw_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "vocabularies",
        "HelloWorld.hw",
    )
    try:
        symbols = _load_from_hw(hw_path)
        if symbols:
            return symbols
    except Exception:
        pass
    return _fallback_symbols()


GLOBAL_SYMBOLS: Dict[str, GlobalSymbol] = _init_symbols()


class GlobalVocabulary:
    """Interface to the global HelloWorld # namespace."""

    @staticmethod
    def all_symbols() -> set:
        return set(GLOBAL_SYMBOLS.keys())

    @staticmethod
    def get(symbol: str) -> Optional[GlobalSymbol]:
        return GLOBAL_SYMBOLS.get(symbol)

    @staticmethod
    def has(symbol: str) -> bool:
        return symbol in GLOBAL_SYMBOLS

    @staticmethod
    def definition(symbol: str) -> str:
        sym = GLOBAL_SYMBOLS.get(symbol)
        return str(sym) if sym else f"Unknown symbol: {symbol}"

    @staticmethod
    def wikidata_url(symbol: str) -> Optional[str]:
        sym = GLOBAL_SYMBOLS.get(symbol)
        if sym and sym.wikidata_id:
            return f"https://www.wikidata.org/wiki/{sym.wikidata_id}"
        return None


def is_global_symbol(symbol: str) -> bool:
    """Check if a symbol is in the global HelloWorld # namespace."""
    return GlobalVocabulary.has(symbol)


def reload_symbols(hw_path: Optional[str] = None) -> None:
    """Re-load global symbols (useful after editing the .hw file)."""
    global GLOBAL_SYMBOLS
    if hw_path:
        try:
            GLOBAL_SYMBOLS.clear()
            GLOBAL_SYMBOLS.update(_load_from_hw(hw_path))
            return
        except Exception:
            pass
    GLOBAL_SYMBOLS.clear()
    GLOBAL_SYMBOLS.update(_init_symbols())


__all__ = ['GlobalSymbol', 'GLOBAL_SYMBOLS', 'GlobalVocabulary', 'is_global_symbol', 'reload_symbols']
