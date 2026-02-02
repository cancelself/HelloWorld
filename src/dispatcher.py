"""HelloWorld Dispatcher - Executes AST nodes and manages receiver state.
Enables Hybrid Dispatch: Structural facts via Python, Interpretive voice via LLM.
Enables Prototypal Inheritance: HelloWorld is the parent of all receivers.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import os
from datetime import datetime

from ast_nodes import (
    DescriptionNode,
    HeadingNode,
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
from global_symbols import GlobalVocabulary
import message_bus
from tools import ToolRegistry
from envs import EnvironmentRegistry
from message_handlers import MessageHandlerRegistry
from prompts import scoped_lookup_prompt, message_prompt, collision_prompt


class LookupOutcome(Enum):
    """Three-outcome model for symbol lookup."""
    NATIVE = "native"
    INHERITED = "inherited"      # Found in parent chain
    UNKNOWN = "unknown"


@dataclass
class LookupResult:
    """Structured result of symbol lookup.

    Prototypal inheritance model:
    - native: receiver owns the symbol locally
    - inherited: symbol found in parent chain (not in local)
    - unknown: not in local OR parent chain — truly new

    Context preserves information needed for interpretation or learning.
    """
    outcome: LookupOutcome
    symbol: str
    receiver_name: str
    context: Optional[Dict[str, Any]] = None

    def is_native(self) -> bool:
        return self.outcome == LookupOutcome.NATIVE

    def is_inherited(self) -> bool:
        return self.outcome == LookupOutcome.INHERITED

    def is_unknown(self) -> bool:
        return self.outcome == LookupOutcome.UNKNOWN


class Receiver:
    def __init__(self, name: str, vocabulary: Set[str] = None, parent: 'Receiver' = None):
        self.name = name
        self.local_vocabulary = vocabulary if vocabulary is not None else set()
        self.parent: Optional['Receiver'] = parent
        self._parent_name: Optional[str] = None

    @property
    def vocabulary(self) -> Set[str]:
        """Returns local vocabulary ONLY (not inherited from parent chain)."""
        return self.local_vocabulary.copy()

    def is_native(self, symbol: str) -> bool:
        """Check if symbol is in receiver's local vocabulary."""
        return symbol in self.local_vocabulary

    def _find_in_chain(self, symbol: str) -> Optional['Receiver']:
        """Walk parent chain to find which ancestor holds this symbol."""
        ancestor = self.parent
        while ancestor:
            if symbol in ancestor.local_vocabulary:
                return ancestor
            ancestor = ancestor.parent
        return None

    def has_symbol(self, symbol: str) -> bool:
        """Check if receiver has symbol (local or inherited via parent chain)."""
        return self.is_native(symbol) or self._find_in_chain(symbol) is not None

    def is_inherited(self, symbol: str) -> bool:
        """Check if symbol is inherited from parent chain (not local)."""
        return not self.is_native(symbol) and self._find_in_chain(symbol) is not None

    def add_symbol(self, symbol: str):
        """Add symbol to local vocabulary."""
        self.local_vocabulary.add(symbol)

    def lookup(self, symbol: str) -> LookupResult:
        """Perform symbol lookup via prototypal inheritance chain.

        Three outcomes:
        1. NATIVE — symbol in local vocabulary
        2. INHERITED — symbol found in parent chain
        3. UNKNOWN — symbol not found anywhere
        """
        if self.is_native(symbol):
            return LookupResult(
                outcome=LookupOutcome.NATIVE,
                symbol=symbol,
                receiver_name=self.name,
                context={"local_vocabulary": sorted(self.local_vocabulary)}
            )

        ancestor = self._find_in_chain(symbol)
        if ancestor:
            return LookupResult(
                outcome=LookupOutcome.INHERITED,
                symbol=symbol,
                receiver_name=self.name,
                context={
                    "defined_in": ancestor.name,
                    "local_vocabulary": sorted(self.local_vocabulary)
                }
            )

        return LookupResult(
            outcome=LookupOutcome.UNKNOWN,
            symbol=symbol,
            receiver_name=self.name,
            context={"local_vocabulary": sorted(self.local_vocabulary)}
        )

    def chain(self) -> List[str]:
        """Return full inheritance chain as list of names."""
        result = [self.name]
        ancestor = self.parent
        while ancestor:
            result.append(ancestor.name)
            ancestor = ancestor.parent
        return result

    def __repr__(self):
        local = sorted(self.local_vocabulary)
        chain = self.chain()
        parent_name = chain[1] if len(chain) > 1 else "root"
        return f"{self.name} : {parent_name} # → {local}"


class Dispatcher:
    def __init__(self, vocab_dir: str = "vocabularies", use_llm: bool = False):
        self.registry: Dict[str, Receiver] = {}
        self.vocab_manager = VocabularyManager(vocab_dir)
        self.message_bus_enabled = os.environ.get("HELLOWORLD_DISABLE_MESSAGE_BUS") != "1"
        self.tool_registry = ToolRegistry()
        self.env_registry = EnvironmentRegistry()
        self.message_handler_registry = MessageHandlerRegistry()
        self.log_file = "collisions.log"
        # HelloWorld is the root parent
        self.agents = {"Claude", "Copilot", "Gemini", "Codex", "Scribe"}
        # Phase 4: LLM interpretation layer
        self.use_llm = use_llm
        self.llm = None
        if use_llm:
            from llm import get_llm_for_agent
            self.llm = get_llm_for_agent("HelloWorld")
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
        """Initialize default receivers from .hw vocabulary files.

        The language defines its own receivers using HelloWorld syntax.
        Single source of truth: .hw files in vocabularies/ directory.

        1. Load from .hw files (vocab_manager reads Markdown format)
        2. If vocab_dir differs from vocabularies/, bootstrap from vocabularies/*.hw
        3. Fallback: HelloWorld receiver must always exist (even if empty)
        4. Resolve parent references to build the inheritance chain
        """
        # 1. Initialize known agents and HelloWorld from persisted state or .hw
        core_receivers = {"HelloWorld"} | self.agents

        # Scan storage dir for .hw files; fall back to canonical vocabularies/
        vocab_dir = Path(self.vocab_manager.storage_dir)
        hw_files = {}
        if vocab_dir.exists():
            for hw_file in vocab_dir.glob("*.hw"):
                hw_files[hw_file.stem] = hw_file

        # If storage dir has no .hw files, fall back to canonical vocabularies/
        if not hw_files:
            canonical = Path(__file__).parent.parent / "vocabularies"
            if canonical.exists():
                for hw_file in canonical.glob("*.hw"):
                    hw_files[hw_file.stem] = hw_file

        # 2. Load all core and discovered receivers
        all_potential = set(core_receivers) | set(hw_files.keys())

        for name in sorted(all_potential):
            # _get_or_create_receiver handles loading from .hw
            receiver = self._get_or_create_receiver(name)

            # If receiver is empty and a .hw file exists, load from .hw
            if not receiver.local_vocabulary and name in hw_files:
                self.dispatch_source(hw_files[name].read_text())

        # 3. Final Fallback: Ensure HelloWorld exists
        if "HelloWorld" not in self.registry:
            self.registry["HelloWorld"] = Receiver("HelloWorld", set())

        # 4. Resolve parent name strings to actual Receiver objects
        self._resolve_parents()

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
        if isinstance(node, HeadingNode):
            return self._handle_heading(node)
        if isinstance(node, DescriptionNode):
            return None  # standalone descriptions are no-ops
        return None

    def _handle_heading(self, node: HeadingNode) -> Optional[str]:
        """Handle Markdown heading nodes.

        HEADING1 declares a receiver and defines its symbols from child HEADING2 nodes.
        Stores parent name for later resolution via _resolve_parents().
        HEADING2 at top level is a standalone symbol reference (no receiver context).
        """
        if node.level == 1:
            receiver = self._get_or_create_receiver(node.name)
            if node.parent:
                receiver._parent_name = node.parent
            for child in node.children:
                if isinstance(child, HeadingNode) and child.level == 2:
                    # If name already starts with #, use as-is (e.g., ## # → "#")
                    symbol = child.name if child.name.startswith("#") else f"#{child.name}"
                    receiver.add_symbol(symbol)
            self.vocab_manager.save(receiver.name, receiver.local_vocabulary)
            return f"Defined {node.name} with {len(receiver.vocabulary)} symbols."
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
                
                return "\n".join(lines)

            global_def = GlobalVocabulary.definition(symbol_name)
            wikidata = GlobalVocabulary.wikidata_url(symbol_name)
            result = f"HelloWorld {symbol_name} → {global_def}"
            if wikidata:
                result += f"\n  Wikidata: {wikidata}"
            return result
        
        receiver = self._get_or_create_receiver(receiver_name)
        lookup = receiver.lookup(symbol_name)

        # Phase 4: LLM interpretation layer for native symbols on agent receivers
        if lookup.is_native() and receiver_name in self.agents:
            if self.use_llm and self.llm:
                local_vocab = sorted(receiver.local_vocabulary)
                global_def = GlobalVocabulary.definition(symbol_name)
                prompt = scoped_lookup_prompt(receiver_name, symbol_name, local_vocab, global_def)
                print(f"🤖 LLM interpreting {receiver_name} {symbol_name}...")
                try:
                    llm_response = self.llm.call(prompt)
                    return f"{receiver_name} {symbol_name} → {llm_response}"
                except Exception as e:
                    print(f"⚠️  LLM interpretation failed: {e}")

            if self.message_bus_enabled:
                print(f"📡 Querying {receiver_name} for {symbol_name}...")
                local_vocab = sorted(list(receiver.local_vocabulary))
                context = f"Local Vocabulary: {local_vocab}"
                prompt = f"{receiver_name} {symbol_name}?"
                self.message_bus_send_and_wait("HelloWorld", receiver_name, prompt, context=context)

        # Structural response based on lookup outcome
        if lookup.is_native():
            # Super lookup: check if symbol also lives in the parent chain
            ancestor = receiver._find_in_chain(symbol_name)
            if ancestor:
                return (
                    f"{receiver_name} {symbol_name} is native to this identity.\n"
                    f"  super: {ancestor.name} also holds {symbol_name} — "
                    f"inherited meaning shapes the local one."
                )
            return f"{receiver_name} {symbol_name} is native to this identity."
        elif lookup.is_inherited():
            defined_in = lookup.context.get("defined_in", "parent")
            return f"{receiver_name} {symbol_name} is inherited from {defined_in}."
        else:
            return self._handle_unknown_symbol(receiver_name, receiver, symbol_name, lookup)

    def _handle_cross_receiver_send(self, sender_name: str, sender, node: MessageNode) -> str:
        """Handle send:to: — deliver a symbol from one receiver to another.

        This is where 'dialogue is namespace collision' becomes real.
        The sent symbol is checked against both sender and target vocabularies:
        - both native: TRUE COLLISION — synthesis required
        - target native only: target already owns it (query, not collision)
        - inherited: target inherits it from HelloWorld # (shared ground)
        - foreign: symbol is foreign to the target — boundary event, target learns it
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

        sender_native = sender.is_native(symbol_name)
        target_native = target.is_native(symbol_name)

        if sender_native and target_native:
            # TRUE COLLISION: both receivers hold the symbol natively
            # This is the synthesis event — meanings diverge, new meaning must emerge
            self._log_collision(target_name, symbol_name, context=f"collision with {sender_name}")
            lines.append(f"  COLLISION: both {sender_name} and {target_name} hold {symbol_name} natively")
            lines.append(f"  {sender_name} vocabulary: {sorted(sender.local_vocabulary)}")
            lines.append(f"  {target_name} vocabulary: {sorted(target.local_vocabulary)}")

            # Attempt LLM synthesis if available
            synthesis = self._synthesize_collision(sender_name, sender, target_name, target, symbol_name)
            if synthesis:
                lines.append(f"  [COLLISION SYNTHESIS: {sender_name} × {target_name} on {symbol_name}]")
                lines.append(f"  {synthesis}")
            else:
                lines.append(f"  (synthesis requires LLM — structural collision detected)")

        elif target_native:
            lines.append(f"  {target_name} already holds {symbol_name} (native)")
        elif target.is_inherited(symbol_name):
            ancestor = target._find_in_chain(symbol_name)
            defined_in = ancestor.name if ancestor else "parent"
            lines.append(f"  {target_name} inherits {symbol_name} from {defined_in} (shared ground)")
        else:
            # Foreign — the symbol is foreign to the target
            self._log_collision(target_name, symbol_name)
            target.add_symbol(symbol_name)
            self.vocab_manager.save(target_name, target.local_vocabulary)
            lines.append(f"  {symbol_name} is foreign to {target_name} — boundary collision")
            lines.append(f"  {target_name} learns {symbol_name} (vocabulary drift)")
            lines.append(f"  [{target_name} # = {sorted(target.local_vocabulary)}]")

        if node.annotation:
            lines.append(f"  '{node.annotation}'")

        return "\n".join(lines)

    def _synthesize_collision(self, sender_name: str, sender, target_name: str, target, symbol_name: str) -> Optional[str]:
        """Attempt to synthesize meaning from a collision between two receivers.

        Returns a synthesis string if LLM is available, None otherwise.
        The synthesis should voice both interpretations and produce something
        neither receiver could produce alone.
        """
        # Try LLM synthesis first
        if self.use_llm and self.llm:
            sender_vocab = sorted(sender.local_vocabulary)
            target_vocab = sorted(target.local_vocabulary)
            prompt = collision_prompt(sender_name, sender_vocab, target_name, target_vocab, symbol_name)
            try:
                return self.llm.call(prompt)
            except Exception as e:
                print(f"  LLM synthesis failed: {e}")

        # Try message bus synthesis (fire-and-forget)
        if self.message_bus_enabled:
            prompt = (
                f"COLLISION SYNTHESIS: {sender_name} and {target_name} both hold {symbol_name}. "
                f"What emerges?"
            )
            context = (
                f"{sender_name} vocabulary: {sorted(sender.local_vocabulary)}\n"
                f"{target_name} vocabulary: {sorted(target.local_vocabulary)}"
            )
            self.message_bus_send_and_wait(
                "HelloWorld", sender_name, prompt, context=context
            )

        return None

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

        Inherited symbols stay inherited — only truly unknown symbols are learned.
        """
        learned = False
        for val in node.arguments.values():
            if isinstance(val, SymbolNode):
                symbol_name = val.name

                # Only learn truly unknown symbols (not native, not inherited)
                if not receiver.has_symbol(symbol_name):
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

        # Phase 4: LLM interpretation for agent messages
        if receiver_name in self.agents:
            message_content = f"{receiver_name} {args_str}"
            if node.annotation:
                message_content += f" '{node.annotation}'"
            
            # Try LLM first if enabled
            if self.use_llm and self.llm:
                local_vocab = sorted(receiver.local_vocabulary)
                prompt = message_prompt(receiver_name, local_vocab, message_content)
                print(f"🤖 LLM interpreting message for {receiver_name}...")
                try:
                    llm_response = self.llm.call(prompt)
                    return f"[{receiver_name}] {llm_response}"
                except Exception as e:
                    print(f"⚠️  LLM interpretation failed: {e}")
            
            # Fallback to message bus (fire-and-forget)
            if self.message_bus_enabled:
                print(f"📡 Dispatching to {receiver_name} for interpretive response...")
                local_vocab = sorted(list(receiver.local_vocabulary))
                context = f"Local Vocabulary: {local_vocab}"
                self.message_bus_send_and_wait("HelloWorld", receiver_name, message_content, context=context)

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
        """Handle UNKNOWN lookup outcome — trigger learning, not collision.

        1. Log unknown event (for tracking vocabulary evolution)
        2. Attempt research via LLM agent (if available)
        3. Return structured response; actual learning happens in _learn_symbols_from_message

        Unknown ≠ Collision:
        - Unknown: one receiver lacks the symbol (triggers learning)
        - Collision: both have it with different meanings (triggers dialogue)
        """
        # Log unknown event for evolution tracking
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] UNKNOWN: {receiver_name} encountered {symbol_name}\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # Try LLM research if available (fire-and-forget via message bus)
        if receiver_name in self.agents and self.message_bus_enabled:
            print(f"📡 Asking {receiver_name} to research unknown symbol {symbol_name}...")
            local_vocab = lookup.context.get("local_vocabulary", []) if lookup else sorted(list(receiver.local_vocabulary))
            context = f"Local Vocabulary: {local_vocab}"
            prompt = f"research new symbol: {symbol_name}"
            self.message_bus_send_and_wait("HelloWorld", receiver_name, prompt, context=context)
        
        # Fallback: structural response indicating unknown state
        return (
            f"{receiver_name} {symbol_name} is unknown — not native and not inherited. "
            "Search, define, and learn it before acting."
        )

    def message_bus_send_and_wait(self, sender: str, receiver: str, content: str, context: Optional[str] = None) -> Optional[str]:
        """Send a message via the bus.  Returns None (fire-and-forget)."""
        if not self.message_bus_enabled:
            return None
        full_content = content
        if context:
            full_content += f"\n\n# Context\n{context}"
        message_bus.send(sender, receiver, full_content)
        return None

    def _node_val(self, node: Node) -> str:
        if isinstance(node, SymbolNode): return node.name
        if isinstance(node, ReceiverNode): return node.name
        if isinstance(node, LiteralNode): return str(node.value)
        return str(node)

    def _resolve_parents(self):
        """Resolve parent name strings to Receiver objects after all receivers are loaded."""
        for receiver in self.registry.values():
            parent_name = receiver._parent_name
            if parent_name and parent_name in self.registry:
                receiver.parent = self.registry[parent_name]

    def _get_or_create_receiver(self, name: str) -> Receiver:
        if name not in self.registry:
            persisted = self.vocab_manager.load(name)
            receiver = Receiver(name, persisted if persisted else set())
            parent_name = self.vocab_manager.load_parent(name)
            if parent_name:
                receiver._parent_name = parent_name
            self.registry[name] = receiver
        return self.registry[name]
