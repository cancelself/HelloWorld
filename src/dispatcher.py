"""HelloWorld Dispatcher - Executes AST nodes and manages receiver state."""

from typing import Dict, List, Optional, Set

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
from vocabulary import VocabularyManager


class Receiver:
    def __init__(self, name: str, vocabulary: Set[str] = None):
        self.name = name
        self.vocabulary = vocabulary if vocabulary is not None else set()

    def add_symbol(self, symbol: str):
        self.vocabulary.add(symbol)

    def __repr__(self):
        return f"{self.name}.# → {sorted(list(self.vocabulary))}"


class Dispatcher:
    def __init__(self, vocab_dir: str = "storage/vocab"):
        self.registry: Dict[str, Receiver] = {}
        self.vocab_manager = VocabularyManager(vocab_dir)
        self._bootstrap()

    def _bootstrap(self):
        """Initialize default receivers, loading from disk if available."""
        defaults = {
            "@awakener": ["#stillness", "#entropy", "#intention", "#sleep", "#insight"],
            "@guardian": ["#fire", "#vision", "#challenge", "#gift", "#threshold"],
            "@gemini": ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta"],
            "@claude": ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta", "#design", "#identity", "#vocabulary"],
            "@copilot": ["#bash", "#git", "#edit", "#test", "#parse", "#dispatch"],
            "@codex": ["#execute", "#analyze", "#parse", "#runtime", "#collision"],
            "@target": ["#sunyata"]
        }
        
        for name, initial_vocab in defaults.items():
            persisted = self.vocab_manager.load(name)
            if persisted:
                self.registry[name] = Receiver(name, persisted)
            else:
                self.registry[name] = Receiver(name, set(initial_vocab))
                self.vocab_manager.save(name, self.registry[name].vocabulary)

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

    def list_receivers(self) -> List[str]:
        return sorted(self.registry.keys())

    def vocabulary(self, receiver: str) -> List[str]:
        return sorted(self._get_or_create_receiver(receiver).vocabulary)

    def save(self, receiver: Optional[str] = None):
        """Persist vocabularies for one receiver or all receivers."""
        if receiver:
            rec = self._get_or_create_receiver(receiver)
            self.vocab_manager.save(receiver, rec.vocabulary)
            return
        for name, rec in self.registry.items():
            self.vocab_manager.save(name, rec.vocabulary)

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
        self.vocab_manager.save(receiver.name, receiver.vocabulary)
        return f"Updated {receiver.name} vocabulary."

    def _handle_message(self, node: MessageNode) -> str:
        receiver_name = node.receiver.name
        receiver = self._get_or_create_receiver(receiver_name)
        args_str = ", ".join([f"{k}: {self._node_val(v)}" for k, v in node.arguments.items()])
        
        # Check if this is a meta-receiver (AI agent)
        META_RECEIVERS = ['@claude', '@gemini', '@copilot', '@codex']
        if receiver_name in META_RECEIVERS:
            # Try to invoke via message bus
            try:
                from message_bus import send_to_agent
                
                # Build message content
                message_content = f"{receiver_name} {args_str}"
                if node.annotation:
                    message_content += f" '{node.annotation}'"
                
                # Send and wait for response
                response = send_to_agent('@dispatcher', receiver_name, 
                                        message_content, timeout=5.0)
                
                if response:
                    return f"[{receiver_name}] {response}"
                else:
                    return f"[{receiver_name}] (no response - daemon may not be running)"
            except Exception as e:
                # Fall back to local handling if message bus fails
                pass
        
        # Logic: If an argument is a symbol the receiver doesn't know, they learn it.
        learned = False
        for val in node.arguments.values():
            if isinstance(val, SymbolNode):
                if val.name not in receiver.vocabulary:
                    receiver.add_symbol(val.name)
                    learned = True
        
        if learned:
            self.vocab_manager.save(receiver.name, receiver.vocabulary)
        
        response = f"[{receiver_name}] Received message: {args_str}"
        if node.annotation:
            response += f" '{node.annotation}'"
        return response

    def _node_val(self, node: Node) -> str:
        if isinstance(node, SymbolNode): return node.name
        if isinstance(node, ReceiverNode): return node.name
        if isinstance(node, LiteralNode): return str(node.value)
        return str(node)

    def _get_or_create_receiver(self, name: str) -> Receiver:
        if name not in self.registry:
            persisted = self.vocab_manager.load(name)
            self.registry[name] = Receiver(name, persisted if persisted else set())
        return self.registry[name]
