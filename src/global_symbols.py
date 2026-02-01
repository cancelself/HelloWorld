"""Global Symbol Registry - HelloWorld # namespace

This module defines the global vocabulary that all receivers inhabit.
Each symbol includes Wikidata reference and canonical definition.

The registry follows the HYBRID CORE principle (Session #37 decision):
- 12 atoms used for bootstrap identity
- 50+ symbols in this library available for discovery through dialogue.
"""

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


# Global symbol library (50+ symbols)
GLOBAL_SYMBOLS: Dict[str, GlobalSymbol] = {
    # Language Primitives (4)
    "#HelloWorld": GlobalSymbol(
        name="#HelloWorld",
        definition="The message-passing language where identity is vocabulary",
        domain="programming languages"
    ),
    "#HelloWorldSystem": GlobalSymbol(
        name="#HelloWorldSystem",
        definition="The unified orchestrator of the distributed multi-agent runtime",
        domain="HelloWorld meta"
    ),
    "#": GlobalSymbol(
        name="#",
        definition="The symbol primitive; the atom of meaning",
        domain="semiotics"
    ),
    "#Symbol": GlobalSymbol(
        name="#Symbol",
        definition="A mark or character used to represent a concept",
        domain="semiotics",
        wikidata_id="Q80071"
    ),

    # Identity & Structure (3)
    "#Receiver": GlobalSymbol(
        name="#Receiver",
        definition="An entity that accepts messages and responds according to its vocabulary",
        domain="HelloWorld meta"
    ),
    "#Message": GlobalSymbol(
        name="#Message",
        definition="A unit of communication carrying intent and context",
        domain="communication",
        wikidata_id="Q628523"
    ),
    "#Vocabulary": GlobalSymbol(
        name="#Vocabulary",
        definition="The set of symbols a receiver can speak; defines identity",
        domain="linguistics",
        wikidata_id="Q6499736"
    ),

    # Runtime Operations (3)
    "#parse": GlobalSymbol(
        name="#parse",
        definition="Decomposing syntax into abstract structure",
        domain="computation",
        wikidata_id="Q2290007"
    ),
    "#dispatch": GlobalSymbol(
        name="#dispatch",
        definition="Routing messages to identity-specific handlers",
        domain="computation"
    ),
    "#interpret": GlobalSymbol(
        name="#interpret",
        definition="Generating meaning from symbols through a receiver's lens",
        domain="HelloWorld meta"
    ),

    # Agent Protocol (3)
    "#Agent": GlobalSymbol(
        name="#Agent",
        definition="An entity that defines, references, and interprets symbols",
        domain="HelloWorld meta"
    ),
    "#observe": GlobalSymbol(
        name="#observe",
        definition="Perceiving the environment or state",
        domain="agent protocol"
    ),
    "#act": GlobalSymbol(
        name="#act",
        definition="Taking autonomous action based on identity",
        domain="agent protocol",
        wikidata_id="Q1914636"
    ),

    # Transition symbols (Phase 1 namespace additions)
    "#Namespace": GlobalSymbol(
        name="#Namespace",
        definition="A container for symbols that provides context and prevents name collisions",
        domain="computer science",
        wikidata_id="Q171318"
    ),
    "#Inheritance": GlobalSymbol(
        name="#Inheritance",
        definition="Mechanism by which symbols pass from parent namespace to child receivers",
        domain="computer science",
        wikidata_id="Q209887"
    ),
    "#Scope": GlobalSymbol(
        name="#Scope",
        definition="The region of code or dialogue where a symbol is defined and accessible",
        domain="computer science",
        wikidata_id="Q1326281"
    ),

    # Philosophical groundings
    "#Sunyata": GlobalSymbol(
        name="#Sunyata",
        definition="Buddhist concept of emptiness - the absence of inherent existence",
        domain="Buddhist philosophy",
        wikidata_id="Q546054"
    ),
    "#Love": GlobalSymbol(
        name="#Love",
        definition="Deep affection, attachment, or devotion — universal across cultures",
        domain="human experience",
        wikidata_id="Q316"
    ),
    "#Superposition": GlobalSymbol(
        name="#Superposition",
        definition="Principle of quantum mechanics where a system exists in multiple states",
        domain="quantum mechanics",
        wikidata_id="Q830791"
    ),

    # Dynamics & Boundaries
    "#Collision": GlobalSymbol(
        name="#Collision",
        definition="Namespace boundary event when a receiver addresses a foreign symbol",
        domain="HelloWorld meta"
    ),
    "#Entropy": GlobalSymbol(
        name="#Entropy",
        definition="Measure of disorder, randomness, or uncertainty in a system",
        domain="information theory",
        wikidata_id="Q130868"
    ),
    "#Drift": GlobalSymbol(
        name="#Drift",
        definition="The evolution of a receiver's vocabulary through dialogue",
        domain="HelloWorld meta"
    ),
    "#Boundary": GlobalSymbol(
        name="#Boundary",
        definition="The edge between two vocabularies where collisions occur",
        domain="HelloWorld meta"
    ),

    # Environment & Simulation
    "#Environment": GlobalSymbol(
        name="#Environment",
        definition="An external system that HelloWorld receivers interact with",
        domain="task environment"
    ),
    "#Simulator": GlobalSymbol(
        name="#Simulator",
        definition="A specific instance of an environment that translates actions into state changes",
        domain="task environment"
    ),
    "#ActionSpace": GlobalSymbol(
        name="#ActionSpace",
        definition="The set of all valid commands an agent can send to a simulator",
        domain="task environment"
    ),
    "#ScienceWorld": GlobalSymbol(
        name="#ScienceWorld",
        definition="A complex text-based environment for elementary science tasks",
        domain="task environment"
    ),

    # Collaboration & Coordination
    "#Proposal": GlobalSymbol(
        name="#Proposal",
        definition="A message suggesting a change to system state or vocabulary",
        domain="collaboration"
    ),
    "#Consensus": GlobalSymbol(
        name="#Consensus",
        definition="The state where all active agents agree on a proposal",
        domain="collaboration",
        wikidata_id="Q186380"
    ),
    "#RFC": GlobalSymbol(
        name="#RFC",
        definition="Request for Comments — a formal proposal for a change",
        domain="collaboration",
        wikidata_id="Q212971"
    ),

    # Runtime
    "#Runtime": GlobalSymbol(
        name="#Runtime",
        definition="The execution layer — Python provides structure, LLM provides interpretation",
        domain="HelloWorld meta",
        wikidata_id="Q2826354"
    ),

    # Agent Coordination
    "#Daemon": GlobalSymbol(
        name="#Daemon",
        definition="Running agent process that watches its inbox and responds via OOPA",
        domain="agent protocol",
        wikidata_id="Q192063"
    ),
    "#Handshake": GlobalSymbol(
        name="#Handshake",
        definition="Startup protocol — agent announces presence via HelloWorld #observe",
        domain="agent protocol",
        wikidata_id="Q628491"
    ),

    # Infrastructure
    "#MCP": GlobalSymbol(
        name="#MCP",
        definition="Model Context Protocol — the standard for connecting AI models to data",
        domain="AI protocol"
    ),
    "#Inbox": GlobalSymbol(
        name="#Inbox",
        definition="File-based message queue where an agent receives incoming messages",
        domain="agent protocol"
    ),
    "#Thread": GlobalSymbol(
        name="#Thread",
        definition="A conversation thread identified by UUID",
        domain="agent protocol",
        wikidata_id="Q575651"
    ),
    "#Protocol": GlobalSymbol(
        name="#Protocol",
        definition="The communication rules governing agent interaction",
        domain="agent protocol",
        wikidata_id="Q8784"
    ),
}


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


__all__ = ['GlobalSymbol', 'GLOBAL_SYMBOLS', 'GlobalVocabulary', 'is_global_symbol']