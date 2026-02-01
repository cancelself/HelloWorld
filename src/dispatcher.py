"""HelloWorld Dispatcher - Executes AST nodes and manages receiver state.
Enables Hybrid Dispatch: Structural facts via Python, Interpretive voice via LLM.
Enables Prototypal Inheritance: HelloWorld is the parent of all receivers.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
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


class LookupOutcome(Enum):
    """Three-outcome model for symbol lookup (Phase 2 + Phase 3)."""
    NATIVE = "native"
    INHERITED = "inherited"  # Alias for DISCOVERABLE (backward compat)
    DISCOVERABLE = "discoverable"  # Phase 3: Global symbol not yet activated
    UNKNOWN = "unknown"


@dataclass
class LookupResult:
    """Structured result of symbol lookup.
    
    Phase 3 discovery model:
    - native: receiver owns the symbol locally (already learned)
    - discoverable/inherited: symbol in global pool, not yet in local (can learn)
    - unknown: not in local OR global — truly new
    
    Context preserves information needed for interpretation or learning.
    """
    outcome: LookupOutcome
    symbol: str
    receiver_name: str
    context: Optional[Dict[str, Any]] = None
    
    def is_native(self) -> bool:
        return self.outcome == LookupOutcome.NATIVE
    
    def is_inherited(self) -> bool:
        """Check if discoverable (backward compat name)."""
        return self.outcome in (LookupOutcome.INHERITED, LookupOutcome.DISCOVERABLE)
    
    def is_discoverable(self) -> bool:
        return self.outcome in (LookupOutcome.INHERITED, LookupOutcome.DISCOVERABLE)
    
    def is_unknown(self) -> bool:
        return self.outcome == LookupOutcome.UNKNOWN


class Receiver:
    def __init__(self, name: str, vocabulary: Set[str] = None):
        self.name = name
        self.local_vocabulary = vocabulary if vocabulary is not None else set()
    
    @property
    def vocabulary(self) -> Set[str]:
        """Phase 3: Returns local vocabulary ONLY (not global pool).
        
        Global symbols are discoverable, not inherited. Receivers must activate
        symbols through dialogue before they enter local vocabulary.
        """
        return self.local_vocabulary.copy()
    
    def can_discover(self, symbol: str) -> bool:
        """Check if symbol is discoverable from global pool."""
        return is_global_symbol(symbol) and symbol not in self.local_vocabulary
    
    def has_symbol(self, symbol: str) -> bool:
        """Check if receiver has symbol (local or discoverable)."""
        return symbol in self.local_vocabulary or is_global_symbol(symbol)
    
    def is_native(self, symbol: str) -> bool:
        """Check if symbol is in receiver's local vocabulary."""
        return symbol in self.local_vocabulary
    
    def is_inherited(self, symbol: str) -> bool:
        """Check if symbol is discoverable (Phase 3: same as can_discover)."""
        return self.can_discover(symbol)
    
    def is_discoverable(self, symbol: str) -> bool:
        """Check if symbol can be discovered from global pool."""
        return self.can_discover(symbol)

    def add_symbol(self, symbol: str):
        """Add symbol to local vocabulary."""
        self.local_vocabulary.add(symbol)
    
    def discover(self, symbol: str) -> bool:
        """Discover a symbol: promote from global pool to local vocabulary.
        
        Phase 3 learning mechanism. Returns True if discovery happened.
        """
        if self.can_discover(symbol):
            self.local_vocabulary.add(symbol)
            return True
        return False
    
    def lookup(self, symbol: str) -> LookupResult:
        """Perform symbol lookup and return structured result.
        
        Phase 3 three outcomes:
        1. NATIVE — symbol in local vocabulary (already learned)
        2. DISCOVERABLE — symbol in global pool, not yet local (can learn)
        3. UNKNOWN — symbol not found anywhere (truly new)
        
        Returns LookupResult with context for downstream handlers.
        """
        if self.is_native(symbol):
            return LookupResult(
                outcome=LookupOutcome.NATIVE,
                symbol=symbol,
                receiver_name=self.name,
                context={"local_vocabulary": sorted(self.local_vocabulary)}
            )
        elif self.can_discover(symbol):
            global_def = GlobalVocabulary.definition(symbol)
            wikidata_url = GlobalVocabulary.wikidata_url(symbol)
            return LookupResult(
                outcome=LookupOutcome.DISCOVERABLE,
                symbol=symbol,
                receiver_name=self.name,
                context={
                    "local_vocabulary": sorted(self.local_vocabulary),
                    "global_definition": global_def,
                    "wikidata_url": wikidata_url
                }
            )
        else:
            return LookupResult(
                outcome=LookupOutcome.UNKNOWN,
                symbol=symbol,
                receiver_name=self.name,
                context={"local_vocabulary": sorted(self.local_vocabulary)}
            )

    def __repr__(self):
        local = sorted(list(self.local_vocabulary))
        discoverable_count = len([s for s in GlobalVocabulary.all_symbols() if self.can_discover(s)])
        return f"{self.name} # → local{local} + {discoverable_count} discoverable"


class Dispatcher:
    def __init__(self, vocab_dir: str = "storage/vocab", discovery_log: Optional[str] = None):
        self.registry: Dict[str, Receiver] = {}
        self.vocab_manager = VocabularyManager(vocab_dir)
        self.message_bus_enabled = os.environ.get("HELLOWORLD_DISABLE_MESSAGE_BUS") != "1"
        self.message_bus = MessageBus() if self.message_bus_enabled else None
        self.tool_registry = ToolRegistry()
        self.env_registry = EnvironmentRegistry()
        self.message_handler_registry = MessageHandlerRegistry()
        self.log_file = "collisions.log"
        self.discovery_log_file = discovery_log or os.path.join("storage", "discovery.log")
        os.makedirs(os.path.dirname(self.discovery_log_file), exist_ok=True)
        # HelloWorld is the root parent
        self.agents = {"Claude", "Copilot", "Gemini", "Codex", "Scribe"}
        self._bootstrap()

    def _log_collision(self, receiver: str, symbol: str, context: Optional[str] = None):
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] COLLISION: {receiver} reached for {symbol}"
        if context:
            log_entry += f" in context of {context}"
        log_entry += "\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def _log_discovery(self, receiver: str, symbol: str):
        """Record the moment a receiver discovers and activates a global symbol."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] DISCOVERY: {receiver} learned {symbol} from Global Library\n"
        os.makedirs(os.path.dirname(self.discovery_log_file), exist_ok=True)
        with open(self.discovery_log_file, "a") as f:
            f.write(log_entry)

    def _bootstrap(self):
        """Initialize default receivers with inheritance support.
        
        Self-hosting (Session #44): Bootstrap from vocabularies/*.hw files.
        The language defines its own receivers using HelloWorld syntax.
        
        Priority:
        1. Persisted vocabularies (storage/vocab/*.vocab) — preserves learned state
        2. Self-hosting definitions (vocabularies/*.hw) — language-defined defaults
        3. Fallback: HelloWorld receiver must always exist
        """
        from pathlib import Path
        
        # Load .hw definitions if they exist
        vocab_dir = Path("vocabularies")
        if vocab_dir.exists():
            for hw_file in sorted(vocab_dir.glob("*.hw")):
                receiver_name = hw_file.stem
                persisted = self.vocab_manager.load(receiver_name)
                if not persisted:
                    # No persisted state — load from .hw file
                    self.dispatch_source(hw_file.read_text())
        
        # Fallback: HelloWorld must always exist (minimal core)
        if "HelloWorld" not in self.registry:
            minimal_core = [
                "#HelloWorld", "#", "#Symbol", "#Receiver", "#Message", "#Vocabulary",
                "#parse", "#dispatch", "#interpret", "#Agent", "#observe", "#act"
            ]
            self.registry["HelloWorld"] = Receiver("HelloWorld", set(minimal_core))

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
        
        # Special case: HelloWorld #symbol queries global definition
        if receiver_name == "HelloWorld":
            if symbol_name == "#observe":
                print("🤝 Handshake Protocol (HelloWorld #observe) initiated. Synchronizing system state...")
                self.save() # Sync local state to disk
                return "HelloWorld #observe → Handshake successful. All agents: sync the tree, sync the messagebus and read them both."

            if symbol_name == "#HelloWorld":
                return "HelloWorld #HelloWorld → Hello MCP World! The Model Context Protocol is grounded and the registry is live."

            if symbol_name == "#State":
                # System-wide state summary
                lines = ["HelloWorld #State → The current state of the distributed registry:"]
                for name, rec in sorted(self.registry.items()):
                    lines.append(f"  - {name}: {len(rec.local_vocabulary)} native symbols")
                
                # Add discovery metrics if log exists
                if os.path.exists("storage/discovery.log"):
                    with open("storage/discovery.log") as f:
                        count = len(f.readlines())
                    lines.append(f"\nDiscovery Velocity: {count} symbols activated since session start.")
                
                return "\n".join(lines)

            global_def = GlobalVocabulary.definition(symbol_name)
            wikidata = GlobalVocabulary.wikidata_url(symbol_name)
            result = f"HelloWorld {symbol_name} → {global_def}"
            if wikidata:
                result += f"\n  Wikidata: {wikidata}"
            return result
        
        receiver = self._get_or_create_receiver(receiver_name)
        lookup = receiver.lookup(symbol_name)
        
        # Phase 3: Discovery! If symbol is discoverable, activate it first
        if lookup.is_discoverable():
            print(f"✨ {receiver_name} discovering {symbol_name} from Global Pool...")
            receiver.discover(symbol_name)
            self._log_discovery(receiver_name, symbol_name)
            # After discovery, it is now NATIVE
            self.save(receiver_name)
            lookup = receiver.lookup(symbol_name)
        
        # If meta-receiver with known symbol, try interpretive voice
        if (
            lookup.is_native()
            and receiver_name in self.agents
            and self.message_bus_enabled
            and self.message_bus
        ):
            print(f"📡 Querying {receiver_name} for {symbol_name}...")
            local_vocab = sorted(list(receiver.local_vocabulary))
            context = f"Local Vocabulary: {local_vocab}"
            prompt = f"{receiver_name} {symbol_name}?"
            response = self.message_bus_send_and_wait("HelloWorld", receiver_name, prompt, context=context)
            if response:
                return response
        
        # Structural response based on lookup outcome
        if lookup.is_native():
            return f"{receiver_name} {symbol_name} is native to this identity."
        else:
            return self._handle_unknown_symbol(receiver_name, receiver, symbol_name, lookup)

    def _handle_cross_receiver_send(self, sender_name: str, sender, node: MessageNode) -> str:
        """Handle send:to: — deliver a symbol from one receiver to another.

        This is where 'dialogue is namespace collision' becomes real.
        The sent symbol is checked against the target's vocabulary:
        - native: target already owns it
        - inherited: target inherits it from HelloWorld #
        - collision: symbol is foreign — boundary event, target learns it
        """
        symbol_val = node.arguments.get("send")
        target_val = node.arguments.get("to")

        symbol_name = symbol_val.name if hasattr(symbol_val, 'name') else str(symbol_val)
        # Handle ReceiverNode or string
        if hasattr(target_val, 'name'):
            target_name = target_val.name
        else:
            target_name = str(target_val)

        target = self._get_or_create_receiver(target_name)

        lines = [f"{sender_name} sends {symbol_name} to {target_name}"]

        if target.is_native(symbol_name):
            lines.append(f"  {target_name} already holds {symbol_name} (native)")
        elif target.is_inherited(symbol_name):
            lines.append(f"  {target_name} inherits {symbol_name} from HelloWorld # (shared ground)")
        else:
            # Collision — the symbol is foreign to the target
            self._log_collision(target_name, symbol_name)
            target.add_symbol(symbol_name)
            self.vocab_manager.save(target_name, target.local_vocabulary)
            lines.append(f"  {symbol_name} is foreign to {target_name} — boundary collision")
            lines.append(f"  {target_name} learns {symbol_name} (vocabulary drift)")
            lines.append(f"  [{target_name} # = {sorted(target.local_vocabulary)}]")

        if node.annotation:
            lines.append(f"  '{node.annotation}'")

        return "\n".join(lines)

    def _handle_definition(self, node: VocabularyDefinitionNode) -> str:
        receiver = self._get_or_create_receiver(node.receiver.name)
        for sym in node.symbols:
            receiver.add_symbol(sym.name)
        self.vocab_manager.save(receiver.name, receiver.local_vocabulary)
        return f"Updated {receiver.name} vocabulary."

    def _learn_symbols_from_message(self, receiver_name: str, receiver, node: MessageNode):
        """Learn unknown symbols from message arguments (vocabulary drift).

        Called before handler dispatch so vocabulary grows through dialogue
        regardless of whether a semantic handler matches.
        
        Phase 3: Also triggers discovery from Global Library.
        """
        learned = False
        for val in node.arguments.values():
            if isinstance(val, SymbolNode):
                symbol_name = val.name
                
                # Check for Discovery (Phase 3)
                if receiver.can_discover(symbol_name):
                    print(f"✨ {receiver_name} discovering {symbol_name} from Global Library...")
                    receiver.discover(symbol_name)
                    self._log_discovery(receiver_name, symbol_name)
                    learned = True
                
                # Traditional Drift (Phase 2 - Collision)
                elif not receiver.has_symbol(symbol_name):
                    receiver.add_symbol(symbol_name)
                    self._log_collision(receiver_name, symbol_name, context="message_args")
                    learned = True
                    
        if learned:
            self.vocab_manager.save(receiver_name, receiver.local_vocabulary)

    def _handle_message(self, node: MessageNode) -> str:
        receiver_name = node.receiver.name
        receiver = self._get_or_create_receiver(receiver_name)
        parent = self._get_or_create_receiver("HelloWorld")

        # Build message string
        args_str = ", ".join([f"{k}: {self._node_val(v)}" for k, v in node.arguments.items()])

        # Always learn symbols first — vocabularies grow through dialogue
        self._learn_symbols_from_message(receiver_name, receiver, node)

        # Cross-receiver delivery: send:to: triggers collision on target
        keywords = list(node.arguments.keys())
        if keywords == ["send", "to"]:
            # First execute the root handler for the side effect/logging
            root_response = self.message_handler_registry.handle("HelloWorld", node, parent)
            if root_response:
                print(root_response)
            return self._handle_cross_receiver_send(receiver_name, receiver, node)

        # SEMANTIC LAYER: Try registered message handlers first for ALL receivers
        handler_response = self.message_handler_registry.handle(receiver_name, node, receiver)
        if handler_response:
            return handler_response
        
        # Check for Environment interaction: @receiver action: #env with: "scienceworld"
        if "#env" in args_str:
            env_name = node.arguments.get("with", LiteralNode("scienceworld")).value
            env = self.env_registry.get_env(str(env_name))
            if env:
                # Map HelloWorld action to env step
                # e.g., @gemini action: #step args: "look"
                action_node = node.arguments.get("action", SymbolNode("#look"))
                action = self._node_val(action_node)
                observation = env.step(action)
                return f"[{receiver_name} @ {env_name}] {observation}"

        # Check for Tool symbols in the message
        tool_results = []
        for key, val in node.arguments.items():
            if isinstance(val, SymbolNode):
                # Tools can be inherited from "HelloWorld" or be native
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
            response = self.message_bus_send_and_wait("HelloWorld", receiver_name, message_content, context=context)
            if response:
                return response
            else:
                return f"[{receiver_name}] (no response - daemon may not be running)"

        response_text = f"[{receiver_name}] Received message: {args_str}"
        if tool_results:
            response_text += "\n" + "\n".join(tool_results)
        if node.annotation:
            response_text += f" '{node.annotation}'"
        return response_text

    def _handle_unknown_symbol(
        self, 
        receiver_name: str, 
        receiver: Receiver, 
        symbol_name: str,
        lookup: Optional[LookupResult] = None
    ) -> str:
        """Handle UNKNOWN lookup outcome — trigger discovery, not collision.
        
        Phase 2: Discovery mechanism
        1. Log unknown event (for tracking vocabulary evolution)
        2. Attempt research via LLM agent (if available)
        3. Promote symbol to local vocabulary on successful resolution
        4. Return structured response for downstream handlers
        
        Unknown ≠ Collision:
        - Unknown: one receiver lacks the symbol (triggers learning)
        - Collision: both have it with different meanings (triggers dialogue)
        """
        # Log unknown event for evolution tracking
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] UNKNOWN: {receiver_name} encountered {symbol_name}\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # Try LLM research if available
        if receiver_name in self.agents and self.message_bus_enabled and self.message_bus:
            print(f"📡 Asking {receiver_name} to research unknown symbol {symbol_name}...")
            local_vocab = lookup.context.get("local_vocabulary", []) if lookup else sorted(list(receiver.local_vocabulary))
            context = f"Local Vocabulary: {local_vocab}"
            prompt = f"research new symbol: {symbol_name}"
            response = self.message_bus_send_and_wait("HelloWorld", receiver_name, prompt, context=context)
            if response:
                # On successful research, promote to local vocabulary
                receiver.add_symbol(symbol_name)
                self.vocab_manager.save(receiver_name, receiver.local_vocabulary)
                learn_log = f"[{timestamp}] LEARNED: {receiver_name} learned {symbol_name} through research\n"
                with open(self.log_file, "a") as f:
                    f.write(learn_log)
                return response
        
        # Fallback: structural response indicating unknown state
        return (
            f"{receiver_name} {symbol_name} is unknown — not native and not inherited. "
            "Search, define, and learn it before acting."
        )

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
