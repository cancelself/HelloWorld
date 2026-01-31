"""HelloWorld Dispatcher - Executes AST nodes and manages receiver state.
Enables Hybrid Dispatch: Structural facts via Python, Interpretive voice via LLM.
"""

from typing import Dict, List, Optional, Set, Any
import uuid

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
from message_bus import MessageBus
from tools import ToolRegistry


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
        self.message_bus = MessageBus()
        self.tool_registry = ToolRegistry()
        self.agents = {"@claude", "@copilot", "@gemini", "@codex"}
        self._bootstrap()

    def _bootstrap(self):
        """Initialize default receivers, loading from disk if available."""
        defaults = {
            "@awakener": ["#stillness", "#entropy", "#intention", "#sleep", "#insight", "#love"],
            "@guardian": ["#fire", "#vision", "#challenge", "#gift", "#threshold", "#love"],
            "@target": ["#sunyata"],
            "@gemini": ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta", "#search", "#sync", "#act", "#env", "#love", "#sunyata", "#superposition"],
            "@claude": ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta", "#design", "#identity", "#vocabulary", "#love"],
            "@copilot": ["#bash", "#git", "#edit", "#test", "#parse", "#dispatch", "#search", "#love"],
            "@codex": ["#execute", "#analyze", "#parse", "#runtime", "#collision", "#love"]
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
        # Support both new and old parser APIs
        if hasattr(Parser, 'from_source'):
            nodes = Parser.from_source(source).parse()
        else:
            from lexer import Lexer
            nodes = Parser(Lexer(source).tokenize()).parse()
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
        
        is_native = symbol_name in receiver.vocabulary
        
        # If it's a meta-receiver and native, try to get their interpretive voice
        if is_native and receiver_name in self.agents:
            print(f"📡 Querying {receiver_name} for interpretive voice on {symbol_name}...")
            prompt = f"{receiver_name}.{symbol_name}?"
            response = self.message_bus_send_and_wait("@meta", receiver_name, prompt)
            if response:
                return response

        if is_native:
            return f"{receiver_name}.{symbol_name} is native to this identity."
        else:
            # Handle collision
            msg = f"{receiver_name} reaches for {symbol_name}... a boundary collision occurs."
            
            # If the receiver is an LLM agent, ask them to interpret the collision
            if receiver_name in self.agents:
                print(f"📡 Asking {receiver_name} to interpret collision with {symbol_name}...")
                prompt = f"{receiver_name} handle collision: {symbol_name}"
                response = self.message_bus_send_and_wait("@meta", receiver_name, prompt)
                if response:
                    return response
            
            return msg

    def _handle_definition(self, node: VocabularyDefinitionNode) -> str:
        receiver = self._get_or_create_receiver(node.receiver.name)
        for sym in node.symbols:
            receiver.add_symbol(sym.name)
        self.vocab_manager.save(receiver.name, receiver.vocabulary)
        return f"Updated {receiver.name} vocabulary."

    def _handle_message(self, node: MessageNode) -> str:
        receiver_name = node.receiver.name
        receiver = self._get_or_create_receiver(receiver_name)
        
        # Build message string
        args_str = ", ".join([f"{k}: {self._node_val(v)}" for k, v in node.arguments.items()])
        
        # Check for Tool symbols in the message
        tool_results = []
        for key, val in node.arguments.items():
            if isinstance(val, SymbolNode):
                tool = self.tool_registry.get_tool(val.name)
                if tool and val.name in receiver.vocabulary:
                    tool_input = args_str 
                    tool_results.append(tool.execute(query=tool_input))

        # External dispatch if receiver is a known agent daemon
        if receiver_name in self.agents:
            message_content = f"{receiver_name} {args_str}"
            if node.annotation:
                message_content += f" '{node.annotation}'"
            
            print(f"📡 Dispatching to {receiver_name} for interpretive response...")
            response = self.message_bus_send_and_wait("@meta", receiver_name, message_content)
            if response:
                return response
            else:
                return f"[{receiver_name}] (no response - daemon may not be running)"

        # Internal state update: learn symbols from arguments
        learned = False
        for val in node.arguments.values():
            if isinstance(val, SymbolNode):
                if val.name not in receiver.vocabulary:
                    receiver.add_symbol(val.name)
                    learned = True
        if learned:
            self.vocab_manager.save(receiver_name, receiver.vocabulary)
        
        response_text = f"[{receiver_name}] Received message: {args_str}"
        if tool_results:
            response_text += "\n" + "\n".join(tool_results)
        if node.annotation:
            response_text += f" '{node.annotation}'"
        return response_text

    def message_bus_send_and_wait(self, sender: str, receiver: str, content: str) -> Optional[str]:
        thread_id = str(uuid.uuid4())
        self.message_bus.send(sender, receiver, content, thread_id=thread_id)
        # Timeout lowered for REPL responsiveness
        return self.message_bus.wait_for_response(receiver, thread_id, timeout=5.0)

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