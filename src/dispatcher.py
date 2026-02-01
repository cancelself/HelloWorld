"""HelloWorld Dispatcher - Executes AST nodes and manages receiver state.
Enables Hybrid Dispatch: Structural facts via Python, Interpretive voice via LLM.
Enables Prototypal Inheritance: '@' is the parent of all receivers.
"""

from typing import Dict, List, Optional, Set, Any
import uuid
import os
from datetime import datetime

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
from global_symbols import GlobalVocabulary, is_global_symbol
from message_bus import MessageBus
from tools import ToolRegistry
from envs import EnvironmentRegistry
from message_handlers import MessageHandlerRegistry


class Receiver:
    def __init__(self, name: str, vocabulary: Set[str] = None):
        self.name = name
        self.local_vocabulary = vocabulary if vocabulary is not None else set()
    
    @property
    def vocabulary(self) -> Set[str]:
        """Returns full vocabulary: local + inherited from @.#"""
        return self.local_vocabulary | GlobalVocabulary.all_symbols()
    
    def has_symbol(self, symbol: str) -> bool:
        """Check if receiver has symbol (local or inherited)."""
        return symbol in self.local_vocabulary or is_global_symbol(symbol)
    
    def is_native(self, symbol: str) -> bool:
        """Check if symbol is in receiver's local vocabulary."""
        return symbol in self.local_vocabulary
    
    def is_inherited(self, symbol: str) -> bool:
        """Check if symbol is inherited from global namespace."""
        return is_global_symbol(symbol) and symbol not in self.local_vocabulary

    def add_symbol(self, symbol: str):
        """Add symbol to local vocabulary."""
        self.local_vocabulary.add(symbol)

    def __repr__(self):
        local = sorted(list(self.local_vocabulary))
        inherited = sorted(list(GlobalVocabulary.all_symbols()))
        return f"{self.name}.# → local{local} + inherited{inherited}"


class Dispatcher:
    def __init__(self, vocab_dir: str = "storage/vocab"):
        self.registry: Dict[str, Receiver] = {}
        self.vocab_manager = VocabularyManager(vocab_dir)
        self.message_bus_enabled = os.environ.get("HELLOWORLD_DISABLE_MESSAGE_BUS") != "1"
        self.message_bus = MessageBus() if self.message_bus_enabled else None
        self.tool_registry = ToolRegistry()
        self.env_registry = EnvironmentRegistry()
        self.message_handler_registry = MessageHandlerRegistry()
        self.log_file = "collisions.log"
        # '@' is the root parent
        self.agents = {"@claude", "@copilot", "@gemini", "@codex"}
        self._bootstrap()

    def _log_collision(self, receiver: str, symbol: str, context: Optional[str] = None):
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] COLLISION: {receiver} reached for {symbol}"
        if context:
            log_entry += f" in context of {context}"
        log_entry += "\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def _bootstrap(self):
        """Initialize default receivers with inheritance support."""
        # The parent receiver '@' carries the global grounding
        defaults = {
            "@": ["#sunyata", "#love", "#superposition", "#"],
            "@awakener": ["#stillness", "#entropy", "#intention", "#sleep", "#insight"],
            "@guardian": ["#fire", "#vision", "#challenge", "#gift", "#threshold"],
            "@gemini": ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta", "#search", "#sync", "#act", "#env", "#love", "#sunyata", "#superposition", "#eval", "#config"],
            "@claude": ["#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta", "#design", "#identity", "#vocabulary"],
            "@copilot": ["#bash", "#git", "#edit", "#test", "#parse", "#dispatch", "#search"],
            "@codex": ["#execute", "#analyze", "#parse", "#runtime", "#collision"]
        }
        
        for name, initial_vocab in defaults.items():
            persisted = self.vocab_manager.load(name)
            if persisted:
                self.registry[name] = Receiver(name, persisted)
            else:
                self.registry[name] = Receiver(name, set(initial_vocab))
                self.vocab_manager.save(name, self.registry[name].local_vocabulary)

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
            self.vocab_manager.save(receiver, rec.local_vocabulary)
            return
        for name, rec in self.registry.items():
            self.vocab_manager.save(name, rec.local_vocabulary)

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
        
        # Special case: @.#symbol queries global definition
        if receiver_name == "@":
            global_def = GlobalVocabulary.definition(symbol_name)
            wikidata = GlobalVocabulary.wikidata_url(symbol_name)
            result = f"@.{symbol_name} → {global_def}"
            if wikidata:
                result += f"\n  Wikidata: {wikidata}"
            return result
        
        receiver = self._get_or_create_receiver(receiver_name)
        is_native = receiver.is_native(symbol_name)
        is_inherited = receiver.is_inherited(symbol_name)
        
        # If meta-receiver, try interpretive voice
        if (
            (is_native or is_inherited)
            and receiver_name in self.agents
            and self.message_bus_enabled
            and self.message_bus
        ):
            print(f"📡 Querying {receiver_name} for {symbol_name}...")
            # Mode 3: Inherited-Interpretive — include local vocabulary as context
            local_vocab = sorted(list(receiver.local_vocabulary))
            context = f"Local Vocabulary: {local_vocab}" if is_inherited else None
            prompt = f"{receiver_name}.{symbol_name}?"
            response = self.message_bus_send_and_wait("@meta", receiver_name, prompt, context=context)
            if response:
                return response
        
        if is_native:
            return f"{receiver_name}.{symbol_name} is native to this identity."
        elif is_inherited:
            global_def = GlobalVocabulary.definition(symbol_name)
            local_ctx = sorted(receiver.local_vocabulary)
            return f"{receiver_name}.{symbol_name} inherited from @.# → {global_def}\n  [{receiver_name}.# = {local_ctx}]"
        else:
            self._log_collision(receiver_name, symbol_name)
            
            # If the receiver is an LLM agent, ask them to interpret the collision
            if receiver_name in self.agents and self.message_bus_enabled and self.message_bus:
                print(f"📡 Asking {receiver_name} to interpret collision with {symbol_name}...")
                local_vocab = sorted(list(receiver.local_vocabulary))
                context = f"Local Vocabulary: {local_vocab}"
                prompt = f"handle collision: {symbol_name}"
                response = self.message_bus_send_and_wait("@meta", receiver_name, prompt, context=context)
                if response:
                    return response
            
            return f"{receiver_name} reaches for {symbol_name}... a boundary collision occurs."
    def _handle_definition(self, node: VocabularyDefinitionNode) -> str:
        receiver = self._get_or_create_receiver(node.receiver.name)
        for sym in node.symbols:
            receiver.add_symbol(sym.name)
        self.vocab_manager.save(receiver.name, receiver.local_vocabulary)
        return f"Updated {receiver.name} vocabulary."

    def _handle_message(self, node: MessageNode) -> str:
        receiver_name = node.receiver.name
        receiver = self._get_or_create_receiver(receiver_name)
        parent = self._get_or_create_receiver("@")
        
        # Build message string
        args_str = ", ".join([f"{k}: {self._node_val(v)}" for k, v in node.arguments.items()])
        
        # First, try registered message handlers (semantic layer)
        handler_response = self.message_handler_registry.handle(receiver_name, node)
        if handler_response:
            return handler_response
        
        # Check for Environment interaction: @receiver action: #env with: "scienceworld"
        if "#env" in args_str:
            env_name = node.arguments.get("with", LiteralNode("scienceworld")).value
            env = self.env_registry.get_env(str(env_name))
            if env:
                # Map HelloWorld action to env step
                # e.g., @gemini action: #step args: "look"
                action = node.arguments.get("action", SymbolNode("#look")).name
                observation = env.step(action)
                return f"[{receiver_name} @ {env_name}] {observation}"

        # Check for Tool symbols in the message
        tool_results = []
        for key, val in node.arguments.items():
            if isinstance(val, SymbolNode):
                # Tools can be inherited from '@' or be native
                tool = self.tool_registry.get_tool(val.name)
                if tool and (val.name in receiver.vocabulary or val.name in parent.vocabulary):
                    tool_input = args_str 
                    tool_results.append(tool.execute(query=tool_input))

        # External dispatch if receiver is a known agent daemon
        if receiver_name in self.agents and self.message_bus_enabled and self.message_bus:
            message_content = f"{receiver_name} {args_str}"
            if node.annotation:
                message_content += f" '{node.annotation}'"
            
            print(f"📡 Dispatching to {receiver_name} for interpretive response...")
            local_vocab = sorted(list(receiver.local_vocabulary))
            context = f"Local Vocabulary: {local_vocab}"
            response = self.message_bus_send_and_wait("@meta", receiver_name, message_content, context=context)
            if response:
                return response
            else:
                return f"[{receiver_name}] (no response - daemon may not be running)"

        # Internal state update: learn symbols from arguments
        learned = False
        for val in node.arguments.values():
            if isinstance(val, SymbolNode):
                if not receiver.has_symbol(val.name):
                    receiver.add_symbol(val.name)
                    self._log_collision(receiver_name, val.name, context="message_args")
                    learned = True
        if learned:
            self.vocab_manager.save(receiver_name, receiver.local_vocabulary)
        
        response_text = f"[{receiver_name}] Received message: {args_str}"
        if tool_results:
            response_text += "\n" + "\n".join(tool_results)
        if node.annotation:
            response_text += f" '{node.annotation}'"
        return response_text

    def message_bus_send_and_wait(self, sender: str, receiver: str, content: str, context: Optional[str] = None) -> Optional[str]:
        if not self.message_bus_enabled or not self.message_bus:
            return None
        thread_id = str(uuid.uuid4())
        self.message_bus.send(sender, receiver, content, thread_id=thread_id, context=context)
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
