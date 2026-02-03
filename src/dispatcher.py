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
    SuperLookupNode,
    SymbolNode,
    UnaryMessageNode,
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
from prompts import (
    scoped_lookup_prompt, scoped_lookup_prompt_with_descriptions,
    super_lookup_prompt, message_prompt, collision_prompt,
    simulate_prompt,
)


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
    def __init__(self, vocab_dir: str = "vocabularies", **kwargs):
        if "use_llm" in kwargs:
            raise TypeError(
                "use_llm parameter removed. LLM is now lazy-loaded when an API key is available. "
                "Set/unset GEMINI_API_KEY to control LLM availability."
            )
        self.registry: Dict[str, Receiver] = {}
        self.vocab_manager = VocabularyManager(vocab_dir)
        self.message_bus_enabled = os.environ.get("HELLOWORLD_DISABLE_MESSAGE_BUS") != "1"
        self.tool_registry = ToolRegistry()
        self.env_registry = EnvironmentRegistry()
        self.message_handler_registry = MessageHandlerRegistry()
        self.log_file = "collisions.log"
        self.trace = False
        # HelloWorld is the root parent
        self.agents = {"Claude", "Copilot", "Gemini", "Codex", "Scribe"}
        # Phase 4: LLM interpretation — lazy-loaded on first use
        self._llm = None
        self._llm_checked = False
        self._bootstrap()

    def _get_llm(self):
        """Lazy-load the LLM on first use. Returns GeminiModel if API key exists, None otherwise."""
        if not self._llm_checked:
            self._llm_checked = True
            from llm import has_api_key, GeminiModel
            if has_api_key():
                self._llm = GeminiModel()
        return self._llm

    @property
    def use_llm(self) -> bool:
        """LLM is available when an API key is set."""
        return self._get_llm() is not None

    @use_llm.setter
    def use_llm(self, value):
        """Allow tests to set use_llm for backward compatibility."""
        if value:
            from llm import GeminiModel
            self._llm = GeminiModel()
            self._llm_checked = True
        else:
            self._llm = None
            self._llm_checked = True

    @property
    def llm(self):
        return self._get_llm()

    @llm.setter
    def llm(self, value):
        """Allow tests to inject a mock LLM."""
        self._llm = value
        self._llm_checked = True

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
                try:
                    self.dispatch_source(hw_files[name].read_text())
                except SyntaxError:
                    pass  # Skip files with unparseable content

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

    def _trace(self, msg: str):
        """Emit trace output if tracing is enabled."""
        if self.trace:
            print(f"  [TRACE] {msg}")

    def _execute(self, node: Node) -> Optional[str]:
        if isinstance(node, VocabularyQueryNode):
            self._trace(f"VocabularyQueryNode({node.receiver.name})")
            return self._handle_query(node)
        if isinstance(node, SuperLookupNode):
            self._trace(f"SuperLookupNode({node.receiver.name}, {node.symbol.name})")
            return self._handle_super_lookup(node)
        if isinstance(node, ScopedLookupNode):
            self._trace(f"ScopedLookupNode({node.receiver.name}, {node.symbol.name})")
            result = self._handle_scoped_lookup(node)
            return result
        if isinstance(node, UnaryMessageNode):
            self._trace(f"UnaryMessageNode({node.receiver.name}, {node.message}, super={node.is_super})")
            return self._handle_unary_message(node)
        if isinstance(node, VocabularyDefinitionNode):
            self._trace(f"VocabularyDefinitionNode({node.receiver.name})")
            return self._handle_definition(node)
        if isinstance(node, MessageNode):
            self._trace(f"MessageNode({node.receiver.name}, {list(node.arguments.keys())})")
            return self._handle_message(node)
        if isinstance(node, HeadingNode):
            self._trace(f"HeadingNode(level={node.level}, name={node.name})")
            return self._handle_heading(node)
        if isinstance(node, SymbolNode):
            return self._handle_bare_symbol(node)
        if isinstance(node, DescriptionNode):
            return None  # standalone descriptions are no-ops
        return None

    def _handle_bare_symbol(self, node: SymbolNode) -> Optional[str]:
        """Handle a bare #Symbol at the top level.

        #ReceiverName → ReceiverName # (the symbol yields the vocabulary).
        The language naming itself shows you what it is.
        """
        # Strip # to get potential receiver name
        name = node.name.lstrip("#")
        if name in self.registry:
            self._trace(f"SymbolNode({node.name}) -> VocabularyQuery({name})")
            receiver = self.registry[name]
            return str(receiver)
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
        self._trace(f"lookup({receiver_name}, {symbol_name}) -> {lookup.outcome.value.upper()}")

        # Phase 4: LLM interpretation layer for agent receivers
        if receiver_name in self.agents and self.llm:
            local_vocab = sorted(receiver.local_vocabulary)
            bare_sym = symbol_name.lstrip("#") if symbol_name != "#" else "#"
            desc = self.vocab_manager.load_description(receiver_name, bare_sym)
            identity = self.vocab_manager.load_identity(receiver_name)

            # Check for super context (symbol native AND in parent chain)
            ancestor = receiver._find_in_chain(symbol_name) if lookup.is_native() else None
            if ancestor:
                ancestor_desc = self.vocab_manager.load_description(ancestor.name, bare_sym)
                from prompts import super_lookup_prompt
                prompt = super_lookup_prompt(
                    receiver_name, symbol_name, local_vocab,
                    desc, ancestor.name, ancestor_desc,
                )
            else:
                from prompts import scoped_lookup_prompt_with_descriptions
                prompt = scoped_lookup_prompt_with_descriptions(
                    receiver_name, symbol_name, local_vocab,
                    desc, identity, GlobalVocabulary.definition(symbol_name),
                )
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

    def _handle_unary_message(self, node: UnaryMessageNode) -> str:
        """Handle a unary message: Receiver act [super]

        Maps the bare message name to #message for vocabulary lookup,
        then either invokes through the LLM or returns a structural response.
        """
        receiver_name = node.receiver.name
        receiver = self._get_or_create_receiver(receiver_name)
        symbol_name = f"#{node.message}"
        lookup = receiver.lookup(symbol_name)

        if node.message == "receive" and receiver_name in self.agents:
            return self._handle_receive(receiver_name, receiver)

        if node.message == "run" and receiver_name == "HelloWorld":
            return self._handle_run()

        if node.message == "chain":
            chain = receiver.chain()
            return f"[{receiver_name}] chain: {' -> '.join(chain)}"

        if node.is_super:
            # Unary super: invoke through ancestor's meaning
            ancestor = receiver._find_in_chain(symbol_name)
            if ancestor:
                if self.llm:
                    local_vocab = sorted(receiver.local_vocabulary)
                    local_desc = self.vocab_manager.load_description(receiver_name, node.message)
                    ancestor_desc = self.vocab_manager.load_description(ancestor.name, node.message)
                    from prompts import super_lookup_prompt
                    prompt = super_lookup_prompt(
                        receiver_name, symbol_name, local_vocab,
                        local_desc, ancestor.name, ancestor_desc,
                    )
                    try:
                        llm_response = self.llm.call(prompt)
                        return f"[{receiver_name}] {node.message} (via {ancestor.name}) — {llm_response}"
                    except Exception:
                        pass
                return (
                    f"[{receiver_name}] {node.message} (via {ancestor.name}) — "
                    f"acts through inherited meaning from {ancestor.name}."
                )
            elif lookup.is_native():
                return (
                    f"[{receiver_name}] {node.message} (super) — "
                    f"native, no ancestor holds {symbol_name}. Acts with local authority."
                )
            else:
                return (
                    f"{receiver_name} {symbol_name} is unknown — "
                    f"cannot invoke super on a symbol not in the chain."
                )

        # Non-super unary message
        if lookup.is_native() or lookup.is_inherited():
            if self.use_llm and self.llm and receiver_name in self.agents:
                local_vocab = sorted(receiver.local_vocabulary)
                desc = self.vocab_manager.load_description(receiver_name, node.message)
                from prompts import scoped_lookup_prompt_with_descriptions
                identity = self.vocab_manager.load_identity(receiver_name)
                prompt = scoped_lookup_prompt_with_descriptions(
                    receiver_name, symbol_name, local_vocab, desc, identity,
                )
                try:
                    llm_response = self.llm.call(prompt)
                    return f"[{receiver_name}] {node.message} — {llm_response}"
                except Exception:
                    pass
            # Structural fallback
            if lookup.is_inherited():
                defined_in = lookup.context.get("defined_in", "parent")
                return f"[{receiver_name}] {node.message} — acts through {symbol_name} (inherited from {defined_in})."
            return f"[{receiver_name}] {node.message} — acts on {symbol_name} (native)."
        else:
            return (
                f"{receiver_name} {symbol_name} is unknown — "
                f"cannot act on what is not in the vocabulary."
            )

    def _handle_receive(self, receiver_name: str, receiver) -> str:
        """Handle `Agent receive` — pull one message, interpret through identity, respond.

        Receiving is hearing through who you are.
        """
        identity = self.vocab_manager.load_identity(receiver_name)
        local_vocab = sorted(receiver.local_vocabulary)

        msg = message_bus.receive(receiver_name)
        if msg is None:
            return f"[{receiver_name}] Inbox empty."

        # Skip self-messages
        if msg.sender == receiver_name:
            return f"[{receiver_name}] Skipped self-message."

        lines = []

        # #observe
        lines.append(
            f"[{receiver_name} #observe] Message from {msg.sender}: "
            f"\"{msg.content[:120]}\""
        )

        # #orient
        lines.append(
            f"[{receiver_name} #orient] Identity: "
            f"{(identity or 'none')[:60]}... Vocabulary: {local_vocab}"
        )

        # #act — LLM interpretation or structural fallback
        response_text = None
        if self.llm:
            prompt = simulate_prompt(
                receiver_name, identity, local_vocab,
                msg.sender, msg.content,
            )
            try:
                response_text = self.llm.call(prompt)
            except Exception:
                pass

        if response_text is None:
            response_text = self._structural_interpret(
                receiver_name, receiver, identity, local_vocab, msg.content,
            )

        lines.append(f"[{receiver_name} #act] {response_text}")

        # Send response back to sender
        message_bus.send(receiver_name, msg.sender, response_text)
        lines.append(f"  -> Sent response to {msg.sender}")

        return "\n".join(lines)

    def _handle_run(self, agent_name: str = None) -> str:
        """Handle `HelloWorld run: Agent` or `HelloWorld run` (all agents).

        HelloWorld run: Claude  — run one agent until inbox empty.
        HelloWorld run: #HelloWorld — run all agents.
        HelloWorld run            — run all agents.
        """
        # Run all agents when no specific agent or #HelloWorld
        if agent_name is None or agent_name.lstrip("#") == "HelloWorld":
            return self._handle_run_all()

        return self._handle_run_one(agent_name)

    def _handle_run_one(self, agent_name: str) -> str:
        """Run one agent until inbox is empty."""
        receiver = self._get_or_create_receiver(agent_name)
        processed = 0
        all_lines = []

        while True:
            result = self._handle_receive(agent_name, receiver)
            if "Inbox empty" in result:
                break
            if "Skipped self-message" in result:
                continue
            processed += 1
            all_lines.append(result)

        if processed == 0:
            return f"[{agent_name}] Inbox empty. Nothing to receive."

        all_lines.append(f"[{agent_name}] Processed {processed} message(s).")
        return "\n".join(all_lines)

    def _handle_run_all(self) -> str:
        """Run all agents. The protocol running the whole system."""
        all_lines = []
        total = 0

        for agent_name in sorted(self.agents):
            result = self._handle_run_one(agent_name)
            if "Nothing to receive" not in result:
                all_lines.append(result)
                # Count messages from the result
                for line in result.split("\n"):
                    if "Processed" in line and "message(s)" in line:
                        import re
                        m = re.search(r"Processed (\d+)", line)
                        if m:
                            total += int(m.group(1))

        if total == 0:
            return "[HelloWorld] All inboxes empty. Nothing to receive."

        all_lines.append(f"[HelloWorld] Processed {total} message(s) across all agents.")
        return "\n".join(all_lines)

    def _structural_interpret(
        self,
        receiver_name: str,
        receiver,
        identity: str,
        local_vocab: List[str],
        content: str,
    ) -> str:
        """Interpret a message structurally through the receiver's vocabulary.

        The Python runtime IS the fallback runtime. It can:
        - Extract #symbols from the message
        - Look each up through the receiver's inheritance chain
        - Pull .hw descriptions for native/inherited symbols
        - Flag foreign symbols as boundary events
        """
        import re
        symbols = re.findall(r"#\w+", content)

        parts = []

        if symbols:
            for sym in symbols:
                lookup = receiver.lookup(sym)
                bare = sym.lstrip("#") if sym != "#" else "#"
                desc = self.vocab_manager.load_description(receiver_name, bare)

                if lookup.is_native():
                    desc_text = f' — "{desc}"' if desc else ""
                    parts.append(f"{sym}: native{desc_text}")
                elif lookup.is_inherited():
                    defined_in = lookup.context.get("defined_in", "parent")
                    parts.append(f"{sym}: inherited from {defined_in}")
                else:
                    parts.append(f"{sym}: foreign to {receiver_name}")

            symbol_report = "; ".join(parts)
            ident = f" {identity}" if identity else ""
            return (
                f"[{receiver_name}]{ident} "
                f"Symbol analysis: {symbol_report}."
            )

        # No symbols found — identity-framed acknowledgment
        ident = identity or receiver_name
        return (
            f"[{receiver_name}] {ident} — "
            f"message acknowledged. Vocabulary: {local_vocab}."
        )

    def _handle_super_lookup(self, node: SuperLookupNode) -> str:
        """Handle typedef super: Receiver #symbol super

        Walk the inheritance chain showing the symbol's description at each level.
        """
        receiver_name = node.receiver.name
        symbol_name = node.symbol.name
        receiver = self._get_or_create_receiver(receiver_name)

        lines = [f"Super chain for {receiver_name} {symbol_name}:"]
        chain = receiver.chain()

        for name in chain:
            r = self._get_or_create_receiver(name)
            desc = self.vocab_manager.load_description(name, symbol_name.lstrip("#"))
            if r.is_native(symbol_name):
                desc_text = f'"{desc}"' if desc else "(no description)"
                lines.append(f"  {name}: native — {desc_text}")
            elif name == receiver_name:
                # Current receiver doesn't have it natively, check inherited
                ancestor = r._find_in_chain(symbol_name)
                if ancestor:
                    lines.append(f"  {name}: inherited from {ancestor.name}")
                else:
                    lines.append(f"  {name}: (not present)")
            else:
                lines.append(f"  {name}: (not present)")

        return "\n".join(lines)

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
        if self.llm:
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

        # HelloWorld run: Agent — the protocol running the agent
        if receiver_name == "HelloWorld" and keywords == ["run"]:
            agent_val = node.arguments.get("run")
            agent_name = agent_val.name if hasattr(agent_val, 'name') else str(agent_val)
            return self._handle_run(agent_name)

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
            if self.llm:
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
        if "::" in name:
            parts = name.split("::")
            target_name = parts[-1]
            
            # Ensure target exists and is loaded
            target = self._get_or_create_receiver(target_name)
            
            # Verify inheritance path: root::...::leaf
            # chain is [leaf, ..., root]
            chain = target.chain()
            last_idx = float('inf')
            for p in parts:
                if p not in chain:
                    raise ValueError(f"Invalid path {name}: {p} is not in the inheritance chain of {target_name}")
                idx = chain.index(p)
                if idx >= last_idx:
                    raise ValueError(f"Invalid path {name}: {p} must be a descendant of previous parts in the chain")
                last_idx = idx
            
            return target

        if name not in self.registry:
            persisted = self.vocab_manager.load(name)
            receiver = Receiver(name, persisted if persisted else set())
            parent_name = self.vocab_manager.load_parent(name)
            if parent_name:
                receiver._parent_name = parent_name
            self.registry[name] = receiver
        return self.registry[name]
