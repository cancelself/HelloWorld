"""HelloWorld AST Nodes."""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict

@dataclass
class Node:
    pass

@dataclass
class SymbolNode(Node):
    name: str  # e.g., "#fire"

@dataclass
class ReceiverNode(Node):
    name: str  # e.g., "Guardian"

@dataclass
class LiteralNode(Node):
    value: Union[str, float, int]

@dataclass
class VocabularyQueryNode(Node):
    receiver: ReceiverNode

@dataclass
class ScopedLookupNode(Node):
    receiver: ReceiverNode
    symbol: SymbolNode

@dataclass
class MessageNode(Node):
    receiver: ReceiverNode
    arguments: Dict[str, Node] = field(default_factory=dict)
    annotation: Optional[str] = None

@dataclass
class VocabularyDefinitionNode(Node):
    receiver: ReceiverNode
    symbols: List[SymbolNode]
