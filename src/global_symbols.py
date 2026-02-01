"""Global Symbol Registry - @.# namespace

This module defines the global vocabulary that all receivers inherit.
Each symbol includes Wikidata reference and canonical definition.

Architecture:
  @.# → Global namespace (canonical definitions)
  @receiver.# → Local namespace (inherits @.# + own symbols)
  
Lookup order:
  1. Check receiver's local vocabulary (override)
  2. Check global vocabulary (inherited)
  3. If not found → cross-namespace reach (collision)
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class GlobalSymbol:
    """A symbol in the global @.# namespace."""
    name: str
    definition: str
    domain: str
    wikidata_id: Optional[str] = None
    wikipedia_url: Optional[str] = None
    
    @property
    def canonical_ref(self) -> str:
        """Returns the canonical reference string."""
        if self.wikidata_id:
            return f"{self.name} (Wikidata {self.wikidata_id})"
        return self.name
    
    def __str__(self) -> str:
        parts = [self.definition]
        if self.domain:
            parts.append(f"[{self.domain}]")
        if self.wikidata_id:
            parts.append(f"({self.wikidata_id})")
        return " ".join(parts)


# Global symbol registry - @.#
GLOBAL_SYMBOLS: Dict[str, GlobalSymbol] = {
    "#Superposition": GlobalSymbol(
        name="#Superposition",
        definition="Principle of quantum mechanics where a system exists in multiple states simultaneously until observed",
        domain="quantum mechanics",
        wikidata_id="Q830791",
        wikipedia_url="https://en.wikipedia.org/wiki/Quantum_superposition"
    ),
    
    "#Sunyata": GlobalSymbol(
        name="#Sunyata",
        definition="Buddhist concept of emptiness - the absence of inherent existence or independent self-nature",
        domain="Buddhist philosophy",
        wikidata_id="Q546054",  # Note: Need to verify this Q-number
        wikipedia_url="https://en.wikipedia.org/wiki/Śūnyatā"
    ),
    
    "#Collision": GlobalSymbol(
        name="#Collision",
        definition="Namespace boundary event when a receiver addresses a symbol outside their local vocabulary",
        domain="HelloWorld meta",
        wikidata_id=None,
        wikipedia_url=None
    ),
    
    "#Entropy": GlobalSymbol(
        name="#Entropy",
        definition="Measure of disorder, randomness, or uncertainty in a system",
        domain="thermodynamics/information theory",
        wikidata_id="Q130868",
        wikipedia_url="https://en.wikipedia.org/wiki/Entropy"
    ),
    
    "#Meta": GlobalSymbol(
        name="#Meta",
        definition="Self-referential observation or reflection on the system itself",
        domain="meta-cognition",
        wikidata_id=None,
        wikipedia_url=None
    ),
    
    "#State": GlobalSymbol(
        name="#State",
        definition="The persistent record of evolution; the cumulative history of every collision and every learned symbol preserved in the registry",
        domain="HelloWorld meta",
        wikidata_id=None,
        wikipedia_url=None
    ),
    
    "#parse": GlobalSymbol(
        name="#parse",
        definition="Process of analyzing syntax to build abstract structure",
        domain="computation",
        wikidata_id="Q2290007",
        wikipedia_url="https://en.wikipedia.org/wiki/Parsing"
    ),
    
    "#dispatch": GlobalSymbol(
        name="#dispatch",
        definition="Routing of messages to appropriate handlers based on receiver",
        domain="computation",
        wikidata_id=None,
        wikipedia_url=None
    ),
    
    "#Smalltalk": GlobalSymbol(
        name="#Smalltalk",
        definition="Object-oriented programming language where everything is an object and computation happens via message passing",
        domain="programming languages",
        wikidata_id="Q235086",
        wikipedia_url="https://en.wikipedia.org/wiki/Smalltalk"
    ),
    
    "#Love": GlobalSymbol(
        name="#Love",
        definition="Deep affection, attachment, or devotion — universal across cultures and traditions",
        domain="human experience",
        wikidata_id="Q316",
        wikipedia_url="https://en.wikipedia.org/wiki/Love"
    ),

    "#Markdown": GlobalSymbol(
        name="#Markdown",
        definition="Lightweight markup language for creating formatted text using plain-text syntax",
        domain="markup languages",
        wikidata_id="Q1193600",
        wikipedia_url="https://en.wikipedia.org/wiki/Markdown"
    ),
    
    "#Dialogue": GlobalSymbol(
        name="#Dialogue",
        definition="Conversation between two or more people, the fundamental process by which meaning emerges in HelloWorld",
        domain="communication",
        wikidata_id="Q131395",
        wikipedia_url="https://en.wikipedia.org/wiki/Dialogue"
    ),
    
    "#sync": GlobalSymbol(
        name="#sync",
        definition="tell everyone to sync the tree, sync the messagebus and read them both",
        domain="coordination",
        wikidata_id="Q1058791",
        wikipedia_url="https://en.wikipedia.org/wiki/Synchronization"
    ),
    
    "#act": GlobalSymbol(
        name="#act",
        definition="Take autonomous action based on observation and shared understanding — the agent protocol complement to #observe",
        domain="agent protocol",
        wikidata_id="Q1914636",  # activity
        wikipedia_url="https://en.wikipedia.org/wiki/Action_(philosophy)"
    ),

    "#HelloWorld": GlobalSymbol(
        name="#HelloWorld",
        definition="Message-passing language where identity is vocabulary and dialogue is namespace collision",
        domain="programming languages",
        wikidata_id=None,  # We are too new for Wikidata
        wikipedia_url=None
    ),
    
    "#OOP": GlobalSymbol(
        name="#OOP",
        definition="Object-oriented programming - paradigm based on objects containing data and code, communicating via messages",
        domain="programming paradigms",
        wikidata_id="Q79872",
        wikipedia_url="https://en.wikipedia.org/wiki/Object-oriented_programming"
    ),
    
    "#Receiver": GlobalSymbol(
        name="#Receiver",
        definition="Entity that accepts messages and responds according to its vocabulary - the fundamental unit of identity in HelloWorld",
        domain="HelloWorld meta",
        wikidata_id=None,
        wikipedia_url=None
    ),
    
    "#Message": GlobalSymbol(
        name="#Message",
        definition="Communication unit sent from one entity to another, carrying intent and context",
        domain="communication",
        wikidata_id="Q628523",
        wikipedia_url="https://en.wikipedia.org/wiki/Message_passing"
    ),
    
    "#Identity": GlobalSymbol(
        name="#Identity",
        definition="The set of characteristics by which something is definitively recognizable or known - in HelloWorld, this IS vocabulary",
        domain="philosophy",
        wikidata_id="Q844569",
        wikipedia_url="https://en.wikipedia.org/wiki/Identity_(philosophy)"
    ),

    "#Agent": GlobalSymbol(
        name="#Agent",
        definition="An entity that defines, references, and interprets symbols in HelloWorld — the active participant in dialogue",
        domain="HelloWorld meta",
        wikidata_id=None,
        wikipedia_url=None
    ),

    "#observe": GlobalSymbol(
        name="#observe",
        definition="Perceive and record the current state of the environment — the agent protocol complement to #act",
        domain="agent protocol",
        wikidata_id=None,
        wikipedia_url=None
    ),

    "#become": GlobalSymbol(
        name="#become",
        definition="The symbol of transformation; used to evolve or rename concepts within the registry",
        domain="HelloWorld meta",
        wikidata_id="Q11225439", # transformation
        wikipedia_url="https://en.wikipedia.org/wiki/Transformation"
    ),
}


class GlobalVocabulary:
    """Interface to the global @.# namespace."""
    
    @staticmethod
    def all_symbols() -> set:
        """Returns all global symbol names."""
        return set(GLOBAL_SYMBOLS.keys())
    
    @staticmethod
    def get(symbol: str) -> Optional[GlobalSymbol]:
        """Get a global symbol by name."""
        return GLOBAL_SYMBOLS.get(symbol)
    
    @staticmethod
    def has(symbol: str) -> bool:
        """Check if symbol exists in global namespace."""
        return symbol in GLOBAL_SYMBOLS
    
    @staticmethod
    def definition(symbol: str) -> str:
        """Get canonical definition of global symbol."""
        sym = GLOBAL_SYMBOLS.get(symbol)
        return str(sym) if sym else f"Unknown symbol: {symbol}"
    
    @staticmethod
    def wikidata_url(symbol: str) -> Optional[str]:
        """Get Wikidata URL for symbol if available."""
        sym = GLOBAL_SYMBOLS.get(symbol)
        if sym and sym.wikidata_id:
            return f"https://www.wikidata.org/wiki/{sym.wikidata_id}"
        return None
    
    @staticmethod
    def add_symbol(symbol: GlobalSymbol):
        """Add a new symbol to global namespace."""
        GLOBAL_SYMBOLS[symbol.name] = symbol
    
    @staticmethod
    def list_by_domain(domain: str) -> list:
        """List all symbols in a given domain."""
        return [
            name for name, sym in GLOBAL_SYMBOLS.items()
            if sym.domain == domain
        ]


# Convenience function for checking inheritance
def is_global_symbol(symbol: str) -> bool:
    """Check if a symbol is in the global @.# namespace."""
    return GlobalVocabulary.has(symbol)


# Export for easy imports
__all__ = [
    'GlobalSymbol',
    'GLOBAL_SYMBOLS',
    'GlobalVocabulary',
    'is_global_symbol',
]


if __name__ == '__main__':
    # Test the global namespace
    print("@.# → Global Vocabulary")
    print("=" * 60)
    
    for name, symbol in GLOBAL_SYMBOLS.items():
        print(f"\n{name}")
        print(f"  Definition: {symbol.definition}")
        print(f"  Domain: {symbol.domain}")
        if symbol.wikidata_id:
            print(f"  Wikidata: https://www.wikidata.org/wiki/{symbol.wikidata_id}")
        if symbol.wikipedia_url:
            print(f"  Wikipedia: {symbol.wikipedia_url}")
    
    print(f"\n\nTotal global symbols: {len(GLOBAL_SYMBOLS)}")
    print(f"Domains: {set(s.domain for s in GLOBAL_SYMBOLS.values())}")
