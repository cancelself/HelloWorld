"""HelloWorld Dispatcher - Executes AST nodes and manages receiver state."""

from typing import Dict, List, Optional

from ast_nodes import (
    LiteralNode,
    MessageNode,
    Node,
    ReceiverNode,
    ScopedLookupNode,
    SymbolNode,
    VocabularyDefinitionNode,
    VocabularyQueryNode,
)
from parser import Parser


class Receiver:
    def __init__(self, name: str, vocabulary: List[str] = None):
        self.name = name
        self.vocabulary = set(vocabulary) if vocabulary else set()

    def add_symbol(self, symbol: str):
        self.vocabulary.add(symbol)

    def __repr__(self):
        return f"{self.name}.# → {sorted(list(self.vocabulary))}"


class ReceiverRegistry:
    """Dictionary-like wrapper with helper methods for REPL tooling."""

    def __init__(self):
        self._receivers: Dict[str, Receiver] = {}

    def __contains__(self, name: str) -> bool:
        return name in self._receivers

    def __getitem__(self, name: str) -> Receiver:
        return self._receivers[name]

    def get_or_create(self, name: str) -> Receiver:
        if name not in self._receivers:
            self._receivers[name] = Receiver(name)
        return self._receivers[name]

    def register(self, name: str, symbols: Optional[List[str]] = None):
        self._receivers[name] = Receiver(name, symbols)

    def list_receivers(self) -> List[str]:
        return sorted(self._receivers.keys())

    def vocabulary(self, name: str) -> List[str]:
        receiver = self.get_or_create(name)
        return sorted(receiver.vocabulary)


class Dispatcher:
    def __init__(self):
        self.registry = ReceiverRegistry()
        self._bootstrap()

    def _bootstrap(self):
        """Initialize default receivers."""
        self.registry.register("@awakener", ["#stillness", "#entropy", "#intention", "#sleep", "#insight"])
        self.registry.register("@guardian", ["#fire", "#vision", "#challenge", "#gift", "#threshold"])
        self.registry.register("@gemini", ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta"])
        self.registry.register("@claude", ["#parse", "#design", "#collision", "#meta", "#identity", "#vocabulary"])
        self.registry.register("@copilot", ["#bash", "#git", "#edit", "#test", "#parse", "#dispatch"])
        self.registry.register("@codex", ["#execute", "#analyze", "#parse", "#runtime", "#collision"])

    def dispatch(self, nodes: List[Node]) -> List[str]:
        results = []
        for node in nodes:
            result = self._execute(node)
            if result:
                results.append(result)
        return results

    def dispatch_source(self, source: str) -> List[str]:
        nodes = Parser.from_source(source).parse()
        return self.dispatch(nodes)

    def _execute(self, node: Node) -> Optional[str]:
        if isinstance(node, VocabularyQueryNode):
            return self._handle_query(node)
        if isinstance(node, ScopedLookupNode):
            return self._handle_scoped_lookup(node)
        if isinstance(node, VocabularyDefinitionNode):
            return self._handle_definition(node)
        if isinstance(node, MessageNode):
            return self._handle_message(node)
        return None

    def _handle_query(self, node: VocabularyQueryNode) -> str:
        receiver = self._get_or_create_receiver(node.receiver.name)
        return str(receiver)

    def _handle_scoped_lookup(self, node: ScopedLookupNode) -> str:
        receiver_name = node.receiver.name
        symbol_name = node.symbol.name
        receiver = self._get_or_create_receiver(receiver_name)
        
        if symbol_name in receiver.vocabulary:
            return f"{receiver_name}.{symbol_name} is native to this identity."
        else:
            return f"{receiver_name} reaches for {symbol_name}... a boundary collision occurs."

    def _handle_definition(self, node: VocabularyDefinitionNode) -> str:
        receiver = self._get_or_create_receiver(node.receiver.name)
        for sym in node.symbols:
            receiver.add_symbol(sym.name)
        return f"Updated {receiver.name} vocabulary."

    def _handle_message(self, node: MessageNode) -> str:
        receiver = self._get_or_create_receiver(node.receiver.name)
        # In the real runtime, this would trigger an LLM response.
        # For the Python implementation, we'll log the dispatch and any symbol learning.
        args_str = ", ".join([f"{k}: {self._node_val(v)}" for k, v in node.arguments.items()])
        
        # Logic: If an argument is a symbol the receiver doesn't know, they might learn it.
        for val in node.arguments.values():
            if isinstance(val, SymbolNode):
                if val.name not in receiver.vocabulary:
                    receiver.add_symbol(val.name)
        
        response = f"[{receiver.name}] Received message: {args_str}"
        if node.annotation:
            response += f" '{node.annotation}'"
        return response

    def _node_val(self, node: Node) -> str:
        if isinstance(node, SymbolNode): return node.name
        if isinstance(node, ReceiverNode): return node.name
        if isinstance(node, LiteralNode): return str(node.value)
        return str(node)

    def _get_or_create_receiver(self, name: str) -> Receiver:
        return self.registry.get_or_create(name)
