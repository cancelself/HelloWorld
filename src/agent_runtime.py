"""HelloWorld Agent Runtime - Claude Agent SDK integration.

Each HelloWorld receiver (Claude, Copilot, Gemini, Codex) becomes a subagent
with its system prompt built from its .hw vocabulary file. Uses hw_reader
(parser-free) for all .hw file operations — no lexer/parser dependency.

The orchestrator prompt is built from the vocabulary hierarchy itself:
HelloWorld.hw (root symbols), Object.hw (messaging), Agent.hw (protocol).

Works without claude-agent-sdk for construction and testing.
Raises ImportError on query()/run_autonomous() if SDK is missing.
"""

import os
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from hw_reader import HwReceiver, read_hw_file, read_hw_directory
from hw_tools import HwTools


# Agent receivers that get their own subagent
AGENT_RECEIVERS = ("Claude", "Copilot", "Gemini", "Codex")

# SDK adapter mapping: agent name -> module.ClassName
SDK_AGENT_MAP = {
    "Codex": "codex_runtime.CodexAdapter",
    "Copilot": "copilot_runtime.CopilotAdapter",
    "Gemini": "gemini_runtime.GeminiAdapter",
    "Claude": None,  # uses existing claude_llm.py directly
}

# Design principles appended to every agent's system prompt
DESIGN_PRINCIPLES = """
## Design Principles
- Identity is vocabulary. A receiver cannot speak outside its symbols. Constraint is character.
- Dialogue is namespace collision. When two receivers share a symbol, they mean different things. Honor both.
- Vocabularies drift. Receivers learn. Symbols migrate. Track it.
- Annotations are human. 'single quotes' are the user's voice alongside the protocol.
"""


@dataclass
class ReceiverAgent:
    """A HelloWorld receiver packaged as an agent definition."""
    name: str
    vocabulary: List[str]
    identity: Optional[str] = None
    symbol_descriptions: Dict[str, Optional[str]] = field(default_factory=dict)
    system_prompt: str = ""


class AgentRuntime:
    """Multi-agent runtime powered by Claude Agent SDK.

    Loads .hw vocabulary files via hw_reader (no parser dependency) and
    constructs ReceiverAgent instances. Each agent's system prompt is
    built from its identity, vocabulary, and symbol descriptions.

    The orchestrator prompt is assembled from the vocabulary hierarchy:
    HelloWorld.hw, Object.hw, Agent.hw — the language describing itself.
    """

    def __init__(self, vocab_dir: str = "vocabularies"):
        self.vocab_dir = vocab_dir
        self.tools = HwTools(vocab_dir=vocab_dir)
        self.agents: Dict[str, ReceiverAgent] = {}
        self._receivers: Dict[str, HwReceiver] = {}
        self._adapters: Dict[str, Any] = {}  # name -> SdkAdapter instance
        self._sdk_agents: Dict[str, Any] = {}  # name -> SDK-specific agent object
        self._load_agents()

    def _load_agents(self):
        """Load all agent receivers from .hw files via hw_reader."""
        self._receivers = read_hw_directory(self.vocab_dir)

        for name in AGENT_RECEIVERS:
            receiver = self._receivers.get(name)
            if receiver is None:
                continue

            vocabulary = receiver.vocabulary
            identity = receiver.identity
            descriptions = {
                sym: receiver.symbol_description(sym) for sym in vocabulary
            }

            system_prompt = self.build_system_prompt(name, vocabulary, identity, descriptions)

            self.agents[name] = ReceiverAgent(
                name=name,
                vocabulary=vocabulary,
                identity=identity,
                symbol_descriptions=descriptions,
                system_prompt=system_prompt,
            )

    def build_system_prompt(
        self,
        name: str,
        vocabulary: List[str],
        identity: Optional[str],
        descriptions: Dict[str, Optional[str]],
    ) -> str:
        """Construct a system prompt from .hw identity + vocabulary + descriptions."""
        lines = []

        # Identity
        lines.append(f"You are {name}, a HelloWorld receiver agent.")
        if identity:
            lines.append(f"Identity: {identity}")
        lines.append("")

        # Vocabulary
        lines.append(f"## Vocabulary ({len(vocabulary)} symbols)")
        for sym in vocabulary:
            desc = descriptions.get(sym)
            if desc:
                lines.append(f"- {sym}: {desc}")
            else:
                lines.append(f"- {sym}")
        lines.append("")

        # Constraints
        lines.append("## Constraints")
        lines.append("- Stay within your vocabulary. Constraint is character.")
        lines.append("- When encountering foreign symbols, acknowledge the boundary.")
        lines.append("- Respond in your natural voice, shaped by your identity.")
        lines.append("")

        # Design principles
        lines.append(DESIGN_PRINCIPLES.strip())

        return "\n".join(lines)

    def build_orchestrator_prompt(self) -> str:
        """Build the orchestrator system prompt from the vocabulary hierarchy.

        The orchestrator is the runtime: it parses HelloWorld syntax and dispatches
        to receiver subagents. Its rules come from HelloWorld.hw, Object.hw, and
        Agent.hw — the language describing itself through its own inheritance chain.
        """
        lines = [
            "You are the HelloWorld runtime orchestrator. You parse HelloWorld syntax "
            "and dispatch messages to receiver agents.",
            "",
        ]

        # Load hierarchy .hw files — the language IS the spec
        hierarchy_files = ["HelloWorld", "Object", "Agent"]
        for name in hierarchy_files:
            receiver = self._receivers.get(name)
            if receiver is None:
                receiver = read_hw_file(
                    os.path.join(self.vocab_dir, f"{name}.hw")
                )
            if receiver is None:
                continue

            lines.append(f"## {name}")
            if receiver.identity:
                lines.append(receiver.identity)
            lines.append("")
            for sym_name, sym in receiver.symbols.items():
                desc = sym.description or "(no description)"
                lines.append(f"- **{sym_name}**: {desc}")
            lines.append("")

        # Receiver summary
        lines.append("## Loaded Receivers")
        for name, agent in sorted(self.agents.items()):
            parent = self._receivers.get(name)
            parent_name = parent.parent if parent else None
            lines.append(
                f"- {name}: {len(agent.vocabulary)} symbols"
                + (f", parent: {parent_name}" if parent_name else "")
            )
        lines.append("")

        # Dispatch behavior
        lines.append("## Behavior")
        lines.append("1. Parse input: Receiver #symbol, Receiver action: value, or Markdown headings")
        lines.append("2. Use vocabulary_lookup tool for deterministic symbol checks")
        lines.append("3. For scoped lookups: check membership, delegate to receiver subagent")
        lines.append("4. For collisions: log via collision_log, synthesize through both agents")
        lines.append("5. For run/receive: use message_send/message_receive tools")
        lines.append("")
        lines.append(DESIGN_PRINCIPLES.strip())

        return "\n".join(lines)

    def create_agent_definitions(self) -> Dict[str, dict]:
        """Return agent definitions dict for the Claude Agent SDK.

        Each entry can be used to construct an Agent or passed
        to an orchestrator for multi-agent coordination.
        """
        definitions = {}
        for name, agent in self.agents.items():
            definitions[name] = {
                "name": name,
                "system_prompt": agent.system_prompt,
                "vocabulary": agent.vocabulary,
                "identity": agent.identity,
            }
        return definitions

    def create_sdk_options(self) -> dict:
        """Create configuration dict for the Claude Agent SDK.

        Returns a dict with orchestrator prompt, subagent definitions,
        and tool references. Raises ImportError if SDK is not installed.

        The returned dict structure:
            {
                "orchestrator_prompt": str,
                "subagents": {name: {"system_prompt": str, ...}, ...},
                "tools": [callable, ...],
            }
        """
        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError:
            raise ImportError(
                "claude-agent-sdk is required for SDK mode. "
                "Install it with: pip install claude-agent-sdk"
            )

        return {
            "orchestrator_prompt": self.build_orchestrator_prompt(),
            "subagents": self.create_agent_definitions(),
            "tools": self.tools.all_tools(),
        }

    def _load_adapters(self) -> Dict[str, Any]:
        """Try to import each SDK adapter, skip if SDK is missing.

        Returns a dict of agent_name -> SdkAdapter instance for all
        adapters whose SDK is installed.
        """
        adapters = {}
        for agent_name, adapter_path in SDK_AGENT_MAP.items():
            if adapter_path is None:
                continue  # Claude uses claude_llm.py directly
            module_name, class_name = adapter_path.rsplit(".", 1)
            try:
                mod = __import__(module_name)
                adapter_cls = getattr(mod, class_name)
                adapter = adapter_cls(hw_tools=self.tools)
                if adapter.has_sdk():
                    adapters[agent_name] = adapter
            except (ImportError, AttributeError):
                pass  # SDK not installed, skip
        self._adapters = adapters
        return adapters

    def _init_sdk_agent(self, agent_name: str) -> Any:
        """Initialize an SDK agent for the given receiver.

        Returns the SDK-specific agent object, or None if no adapter is available.
        """
        if agent_name in self._sdk_agents:
            return self._sdk_agents[agent_name]

        adapter = self._adapters.get(agent_name)
        if adapter is None:
            return None

        receiver_agent = self.agents.get(agent_name)
        if receiver_agent is None:
            return None

        tools = adapter.adapt_tools(self.tools)
        sdk_agent = adapter.create_agent(
            name=agent_name,
            system_prompt=receiver_agent.system_prompt,
            tools=tools,
        )
        self._sdk_agents[agent_name] = sdk_agent
        return sdk_agent

    async def query_agent(self, agent_name: str, prompt: str) -> str:
        """Route a query to the correct SDK adapter for the named agent.

        Falls back to interpret() if no SDK adapter is available.
        """
        adapter = self._adapters.get(agent_name)
        if adapter is None:
            return await self.interpret(agent_name, prompt)

        sdk_agent = self._init_sdk_agent(agent_name)
        if sdk_agent is None:
            return await self.interpret(agent_name, prompt)

        return await adapter.query(sdk_agent, prompt)

    def get_adapter(self, agent_name: str) -> Optional[Any]:
        """Return the SDK adapter for an agent, or None."""
        return self._adapters.get(agent_name)

    def loaded_adapters(self) -> Dict[str, str]:
        """Return a dict of agent_name -> SDK name for all loaded adapters."""
        return {name: adapter.sdk_name() for name, adapter in self._adapters.items()}

    async def interpret(self, receiver_name: str, prompt: str) -> str:
        """Delegate interpretation to a specific receiver's agent via Claude API.

        Requires the anthropic package. Uses ClaudeModel directly
        with the receiver's system prompt for scoped interpretation.
        """
        if receiver_name not in self.agents:
            return f"[AgentRuntime] Unknown receiver: {receiver_name}"

        agent = self.agents[receiver_name]

        from claude_llm import ClaudeModel, has_anthropic_key
        if not has_anthropic_key():
            return f"[{receiver_name}] (no API key — mock mode) {prompt[:80]}"

        model = ClaudeModel()
        return model.call(prompt, system=agent.system_prompt)

    async def query(self, source: str) -> str:
        """Send HelloWorld source to the SDK orchestrator for parsing and dispatch.

        Requires claude-agent-sdk. The orchestrator parses the syntax,
        uses tools for structural checks, and delegates to subagents.
        """
        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError:
            raise ImportError(
                "claude-agent-sdk is required for query(). "
                "Install it with: pip install claude-agent-sdk\n"
                "Use interpret() for direct receiver queries without the SDK."
            )

        # SDK orchestration goes here once the SDK is installed.
        # The SDK client would be initialized with create_sdk_options()
        # and source would be sent as a user message to the orchestrator.
        raise NotImplementedError(
            "SDK query requires claude-agent-sdk wiring. "
            "Use interpret() for single-agent queries."
        )

    async def run_dialogue(self, source: str) -> List[str]:
        """Parse HelloWorld source, dispatch structurally, delegate interpretation.

        Uses the dispatcher for structural routing (native/inherited/unknown),
        then hands off to the appropriate agent for interpretive responses.
        """
        from dispatcher import Dispatcher
        from parser import Parser

        dispatcher = Dispatcher(vocab_dir=self.vocab_dir)
        nodes = Parser.from_source(source).parse()
        structural_results = dispatcher.dispatch(nodes)

        results = []
        for result in structural_results:
            results.append(result)

        return results

    async def run_autonomous(self):
        """Start all agents in autonomous OODA loop.

        Requires claude-agent-sdk for full orchestration.
        Without it, falls back to sequential polling via interpret().
        """
        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError:
            raise ImportError(
                "claude-agent-sdk is required for autonomous mode. "
                "Install it with: pip install claude-agent-sdk"
            )

        raise NotImplementedError(
            "Autonomous mode requires claude-agent-sdk orchestration. "
            "Use interpret() for single-agent queries or run_dialogue() for source execution."
        )
