"""HelloWorld Claude Runtime — Claude Agent SDK adapter.

Wraps the 7 HwTools as @tool decorated standalone functions
for the Claude Agent SDK (claude-agent-sdk). Each tool returns JSON strings
as the SDK expects string outputs from tools.

Gracefully degrades: has_sdk() returns False if claude-agent-sdk is not installed.
"""

import json
from typing import Any, List, Optional

from sdk_adapter import SdkAdapter
from hw_tools import HwTools


def _check_sdk() -> bool:
    """Check if claude-agent-sdk is importable."""
    try:
        import claude_agent_sdk  # noqa: F401
        return True
    except ImportError:
        return False


class ClaudeAdapter(SdkAdapter):
    """Claude Agent SDK adapter for the Claude receiver.

    Tool adaptation: Each HwTools method becomes a standalone function
    decorated with @tool. The SDK requires type-hinted functions
    that return strings.

    Agent: dict with ClaudeAgentOptions(system_prompt=..., permission_mode=...)
    Query: async for msg in claude_agent_sdk.query(...) collecting result messages
    """

    def __init__(self, hw_tools: Optional[HwTools] = None, model: str = "claude-opus-4-6"):
        self._hw_tools = hw_tools or HwTools()
        self._sdk_available = _check_sdk()
        self._model = model

    def name(self) -> str:
        return "Claude"

    def sdk_name(self) -> str:
        return "Claude Agent SDK"

    def has_sdk(self) -> bool:
        return self._sdk_available

    def adapt_tools(self, hw_tools: HwTools) -> List[Any]:
        """Wrap HwTools methods as @tool decorated functions.

        The Claude Agent SDK uses standalone functions with type hints
        and docstrings, decorated with @tool. Each function captures
        hw_tools via closure.
        """
        if not self._sdk_available:
            return []

        from claude_agent_sdk import tool

        tools_instance = hw_tools

        @tool
        def vocabulary_lookup(receiver_name: str, symbol_name: str) -> str:
            """Three-outcome symbol lookup: native, inherited, or unknown.

            Args:
                receiver_name: The receiver to look up.
                symbol_name: The symbol to find.
            """
            return json.dumps(tools_instance.vocabulary_lookup(receiver_name, symbol_name))

        @tool
        def vocabulary_list(receiver_name: str) -> str:
            """List a receiver's vocabulary (symbols from its .hw file).

            Args:
                receiver_name: The receiver whose vocabulary to list.
            """
            return json.dumps(tools_instance.vocabulary_list(receiver_name))

        @tool
        def vocabulary_save(receiver_name: str, symbol_name: str, description: str = "") -> str:
            """Append a new symbol to a receiver's .hw file.

            Args:
                receiver_name: The receiver to add the symbol to.
                symbol_name: The symbol name (with # prefix).
                description: Optional description for the symbol.
            """
            desc = description if description else None
            return json.dumps(tools_instance.vocabulary_save(receiver_name, symbol_name, desc))

        @tool
        def collision_log(receiver_name: str, symbol_name: str, collision_type: str = "collision", context: str = "") -> str:
            """Log a namespace collision event.

            Args:
                receiver_name: The receiver involved in the collision.
                symbol_name: The symbol that collided.
                collision_type: Type of collision (default: collision).
                context: Additional context about the collision.
            """
            ctx = context if context else None
            return json.dumps(tools_instance.collision_log(receiver_name, symbol_name, collision_type, ctx))

        @tool
        def message_send(sender: str, receiver: str, content: str) -> str:
            """Send a message via the HelloWorld message bus.

            Args:
                sender: The sending agent's name.
                receiver: The receiving agent's name.
                content: The message content.
            """
            return json.dumps(tools_instance.message_send(sender, receiver, content))

        @tool
        def message_receive(receiver: str) -> str:
            """Receive the next message from a receiver's inbox.

            Args:
                receiver: The agent whose inbox to check.
            """
            return json.dumps(tools_instance.message_receive(receiver))

        @tool
        def receivers_list() -> str:
            """List all receivers found in the vocabulary directory."""
            return json.dumps(tools_instance.receivers_list())

        @tool
        def memory_store(agent_name: str, content: str, title: str = "", tags: str = "") -> str:
            """Store a memory note. Tags are comma-separated.

            Args:
                agent_name: The agent storing the memory.
                content: The content to store.
                title: Optional title for the memory note.
                tags: Optional comma-separated tags.
            """
            return json.dumps(tools_instance.memory_store(agent_name, content, title, tags))

        @tool
        def memory_recall(agent_name: str, query: str, n: int = 5) -> str:
            """Search agent memory via hybrid search. Returns matching snippets.

            Args:
                agent_name: The agent whose memory to search.
                query: The search query.
                n: Number of results to return (default 5).
            """
            return json.dumps(tools_instance.memory_recall(agent_name, query, n))

        return [
            vocabulary_lookup,
            vocabulary_list,
            vocabulary_save,
            collision_log,
            message_send,
            message_receive,
            receivers_list,
            memory_store,
            memory_recall,
        ]

    def create_agent(self, name: str, system_prompt: str, tools: List[Any]) -> Any:
        """Create a Claude Agent SDK agent configuration.

        Args:
            name: Agent name (e.g. 'Claude').
            system_prompt: The agent's system instructions.
            tools: List of @tool decorated functions.

        Returns:
            A dict with name, tools, and ClaudeAgentOptions.
        """
        if not self._sdk_available:
            raise ImportError("claude-agent-sdk is required. Install with: pip install claude-agent-sdk")

        from claude_agent_sdk import ClaudeAgentOptions

        return {
            "name": name,
            "tools": tools,
            "options": ClaudeAgentOptions(
                system_prompt=system_prompt,
                permission_mode="bypassPermissions",
                model=self._model,
            ),
        }

    async def query(self, agent: Any, prompt: str) -> str:
        """Run a prompt through the Claude Agent SDK.

        Uses claude_agent_sdk.query() which returns an async generator.
        Collects all result messages and returns the combined text.
        """
        if not self._sdk_available:
            raise ImportError("claude-agent-sdk is required. Install with: pip install claude-agent-sdk")

        import claude_agent_sdk

        response_parts = []
        async for msg in claude_agent_sdk.query(
            prompt=prompt,
            options=agent["options"],
        ):
            if hasattr(msg, "result") and msg.result:
                response_parts.append(msg.result)

        return "".join(response_parts).strip() if response_parts else "[Claude SDK] Empty response"
