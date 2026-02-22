"""AgentProcess — isolated runtime for a single HelloWorld agent.

Each agent gets its own Dispatcher, MemoryBus, HwTools, and SDK adapter.
Multiple AgentProcess instances can run concurrently via asyncio.gather().

Human-in-the-loop: messages containing #propose, #review, or #question
are routed to a human escalation channel (Web UI + native CLI pickup).
"""

import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Ensure src is on the path
_src = str(Path(__file__).resolve().parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from dispatcher import Dispatcher
from memory_bus import MemoryBus
from hw_tools import HwTools
from hw_reader import read_hw_file
import message_bus
from message_bus import Message
from daemon_registry import pid_file_for

# SDK adapter registry — agent name -> "module.ClassName"
SDK_AGENT_MAP = {
    "Codex": "codex_runtime.CodexAdapter",
    "Copilot": "copilot_runtime.CopilotAdapter",
    "Gemini": "gemini_runtime.GeminiAdapter",
    "Claude": "claude_runtime.ClaudeAdapter",
}

# Human protocol symbols that trigger escalation
HUMAN_SYMBOLS = frozenset({"#propose", "#review", "#question"})


class AgentProcess:
    """Isolated runtime for a single HelloWorld agent.

    Each agent gets:
    - Its own Dispatcher (own registry, own vocabulary state)
    - Its own MemoryBus (runtimes/<agent>/memory/)
    - Its own SDK adapter (auto-detected from SDK_AGENT_MAP)
    - Its own vocabulary drift tracking
    - Human escalation via message bus
    """

    def __init__(self, agent_name: str, vocab_dir: str = "vocabularies"):
        self.name = agent_name
        self.vocab_dir = vocab_dir
        self.runtime_dir = Path(f"runtimes/{agent_name.lower()}")
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        # Isolated runtime components
        self.dispatcher = Dispatcher(vocab_dir=vocab_dir)
        self.memory = MemoryBus(agent_name)
        self.tools = HwTools(vocab_dir=vocab_dir, memory=self.memory)
        self.adapter = self._detect_adapter()
        self.sdk_agent: Any = None

        # Per-agent state
        self.vocabulary = self._load_vocabulary()
        self.learned_symbols: List[str] = []
        self.message_count = 0
        self.started_at: Optional[datetime] = None
        self.pending_human: List[dict] = []
        self.running = False

    def _detect_adapter(self) -> Any:
        """Auto-detect SDK adapter from the SDK_AGENT_MAP registry."""
        adapter_path = SDK_AGENT_MAP.get(self.name)
        if adapter_path is None:
            return None
        module_name, class_name = adapter_path.rsplit(".", 1)
        try:
            mod = __import__(module_name)
            adapter_cls = getattr(mod, class_name)
            adapter = adapter_cls(hw_tools=self.tools)
            return adapter if adapter.has_sdk() else None
        except (ImportError, AttributeError):
            return None

    def _load_vocabulary(self) -> List[str]:
        """Load this agent's vocabulary from dispatcher (inheritance-aware)."""
        if self.name not in self.dispatcher.registry:
            return []
        receiver = self.dispatcher.registry[self.name]
        all_symbols: Set[str] = set(receiver.local_vocabulary)
        ancestor = receiver.parent
        while ancestor:
            all_symbols.update(ancestor.local_vocabulary)
            ancestor = ancestor.parent
        return sorted(all_symbols)

    def _init_sdk_agent(self):
        """Create the SDK agent with HelloWorld tools + system prompt."""
        if self.sdk_agent is not None or self.adapter is None:
            return

        system_prompt = self._build_system_prompt()
        sdk_tools = self.adapter.adapt_tools(self.tools)
        self.sdk_agent = self.adapter.create_agent(
            name=self.name,
            system_prompt=system_prompt,
            tools=sdk_tools,
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt from vocabulary file, tools, memory, and protocols."""
        hw_path = os.path.join(self.vocab_dir, f"{self.name}.hw")
        receiver = read_hw_file(hw_path)

        lines = [f"You are {self.name}, a HelloWorld receiver agent."]
        if receiver and receiver.identity:
            lines.append(f"Identity: {receiver.identity}")
        lines.append("")

        lines.append(f"## Vocabulary ({len(self.vocabulary)} symbols)")
        for sym in self.vocabulary:
            desc = None
            if receiver:
                desc = receiver.symbol_description(sym)
            if desc:
                lines.append(f"- {sym}: {desc}")
            else:
                lines.append(f"- {sym}")
        lines.append("")

        # Tools section — dynamically built from all_tools()
        lines.append("## Tools")
        lines.append("You have the following tools available:")
        for tool_fn in self.tools.all_tools():
            name = tool_fn.__name__
            doc = (tool_fn.__doc__ or "").strip().split("\n")[0]
            lines.append(f"- **{name}**: {doc}")
        lines.append("")

        # Memory section
        lines.append("## Memory")
        lines.append("- Your memory is QMD-backed (BM25 + vector hybrid search).")
        lines.append("- Context from memory is automatically prepended to incoming messages.")
        lines.append("- You can explicitly store via the memory_store tool and recall via the memory_recall tool.")
        lines.append("- Store evidence, not conclusions. Observations, patterns, exact quotes.")
        lines.append("")

        # Protocols section
        lines.append("## Protocols")
        lines.append("- Messages containing #propose, #review, or #question escalate to Human.")
        lines.append("- Messages are received via the message bus; responses are sent back automatically.")
        lines.append(f"- Your sender name is '{self.name}'.")
        lines.append("")

        lines.append("## Constraints")
        lines.append("- Stay within your vocabulary. Constraint is character.")
        lines.append("- When encountering foreign symbols, acknowledge the boundary.")
        lines.append("- Respond in your natural voice, shaped by your identity.")

        return "\n".join(lines)

    def _recall_context(self, content: str) -> str:
        """Recall relevant memories for context."""
        if not self.memory.available():
            return ""
        try:
            recalls = self.memory.recall(content, n=3)
            if recalls:
                return "\n".join(r.snippet for r in recalls)
        except Exception:
            pass
        return ""

    def _needs_human(self, msg: Message) -> bool:
        """Check if message requires human-in-the-loop."""
        content = msg.content
        return any(sym in content for sym in HUMAN_SYMBOLS)

    def _escalate_to_human(self, msg: Message) -> str:
        """Route message to human via pending queue + Human inbox."""
        self.pending_human.append({
            "from": msg.sender,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "type": "escalation",
        })
        message_bus.send(self.name, "Human", msg.content)
        return f"[{self.name}] Escalated to human: {msg.content[:80]}"

    async def process_message(self, msg: Message) -> str:
        """Process a message through this agent's SDK.

        1. Store incoming message in memory
        2. Recall relevant context
        3. Check if human escalation is needed
        4. Process through SDK adapter (or LLM fallback)
        5. Store response in memory
        """
        # 1. Store incoming
        self.memory.store(
            f"From {msg.sender}: {msg.content}",
            title=f"inbox-{msg.sender}-{self.message_count}",
            tags=["inbox", msg.sender],
        )

        # 2. Recall context
        context = self._recall_context(msg.content)

        # 3. Check for human escalation
        if self._needs_human(msg):
            print(f"[{self.name}] Escalating to human (protocol symbol detected)",
                  flush=True)
            return self._escalate_to_human(msg)

        # 4. Process through SDK or LLM
        if self.adapter and self.sdk_agent:
            print(f"[{self.name}] Processing via {self.adapter.sdk_name()}",
                  flush=True)
            prompt = msg.content
            if context:
                prompt = f"Context from memory:\n{context}\n\nMessage: {msg.content}"
            response = await self.adapter.query(self.sdk_agent, prompt)
        else:
            print(f"[{self.name}] Processing via LLM fallback", flush=True)
            response = await self._interpret_via_llm(msg, context)

        # 5. Store response
        self.memory.store(
            f"To {msg.sender}: {response}",
            title=f"outbox-{msg.sender}-{self.message_count}",
            tags=["outbox", msg.sender],
        )

        self.message_count += 1
        return response

    async def _interpret_via_llm(self, msg: Message, context: str) -> str:
        """Fallback interpretation via Claude API when no SDK adapter."""
        try:
            from claude_llm import ClaudeModel, has_anthropic_key
            if not has_anthropic_key():
                return f"[{self.name}] Received: {msg.content[:120]}"

            system = self._build_system_prompt()
            prompt = msg.content
            if context:
                prompt = f"Context from memory:\n{context}\n\nMessage: {msg.content}"

            model = ClaudeModel()
            return model.call(prompt, system=system)
        except ImportError:
            return f"[{self.name}] Received: {msg.content[:120]}"

    async def _handle_human_response(self, msg: Message):
        """Process a response from a human."""
        # Clear the corresponding pending item
        self.pending_human = [
            p for p in self.pending_human
            if p.get("content") != msg.content
        ]
        # Store in memory
        self.memory.store(
            f"Human response: {msg.content}",
            title=f"human-response-{self.message_count}",
            tags=["human", "response"],
        )

    async def run(self):
        """Main daemon loop — OODA with memory and human escalation."""
        self.started_at = datetime.now(timezone.utc)
        self.running = True
        self._init_sdk_agent()
        message_bus.hello(self.name)

        sdk_label = self.adapter.sdk_name() if self.adapter else "LLM fallback"
        print(f"[{self.name}] Started (sdk={sdk_label}, "
              f"vocab={len(self.vocabulary)} symbols, "
              f"memory={'yes' if self.memory.available() else 'no'})",
              flush=True)

        # Write PID file
        pid_file = pid_file_for(self.name)
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))

        try:
            while self.running:
                # Check for human responses
                human_msg = message_bus.receive(f"{self.name}-human")
                if human_msg:
                    print(f"[{self.name}] Human response from {human_msg.sender}",
                          flush=True)
                    await self._handle_human_response(human_msg)

                # Check agent inbox
                msg = message_bus.receive(self.name)
                if msg and msg.sender != self.name:
                    print(f"[{self.name}] Received from {msg.sender}: {msg.content[:120]}",
                          flush=True)
                    response = await self.process_message(msg)
                    if not response.startswith("NOTHING_FURTHER"):
                        print(f"[{self.name}] Replying to {msg.sender}: {response[:120]}",
                              flush=True)
                        message_bus.send(self.name, msg.sender, response)

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            pid_file.unlink(missing_ok=True)
            self.running = False
            print(f"[{self.name}] Stopped.", flush=True)

    def stop(self):
        """Signal the run loop to stop."""
        self.running = False

    def status(self) -> dict:
        """Full agent status for Web UI monitoring."""
        return {
            "name": self.name,
            "vocabulary_size": len(self.vocabulary),
            "vocabulary": self.vocabulary,
            "learned": self.learned_symbols,
            "messages_processed": self.message_count,
            "memory_available": self.memory.available(),
            "adapter": self.adapter.sdk_name() if self.adapter else "LLM fallback",
            "sdk_ready": self.sdk_agent is not None,
            "pending_human": len(self.pending_human),
            "pending_human_items": list(self.pending_human),
            "running": self.running,
            "uptime": str(datetime.now(timezone.utc) - self.started_at)
                     if self.started_at else None,
        }
