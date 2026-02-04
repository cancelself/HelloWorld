"""HelloWorld Codex Runtime — OpenAI Agents SDK adapter.

Wraps the 7 HwTools as @function_tool decorated standalone functions
for the OpenAI Agents SDK (openai-agents). Each tool returns JSON strings
as the SDK expects string outputs from tools.

Gracefully degrades: has_sdk() returns False if openai-agents is not installed.
"""

import json
from typing import Any, List, Optional

from sdk_adapter import SdkAdapter
from hw_tools import HwTools


def _check_sdk() -> bool:
    """Check if openai-agents SDK is importable."""
    try:
        import agents  # noqa: F401
        return True
    except ImportError:
        return False


class CodexAdapter(SdkAdapter):
    """OpenAI Agents SDK adapter for the Codex receiver.

    Tool adaptation: Each HwTools method becomes a standalone function
    decorated with @function_tool. The SDK requires type-hinted functions
    that return strings.

    Agent: agents.Agent(name=..., instructions=..., tools=[...])
    Query: agents.Runner.run(agent, prompt) -> result.final_output
    """

    def __init__(self, hw_tools: Optional[HwTools] = None):
        self._hw_tools = hw_tools or HwTools()
        self._sdk_available = _check_sdk()

    def name(self) -> str:
        return "Codex"

    def sdk_name(self) -> str:
        return "OpenAI Agents SDK"

    def has_sdk(self) -> bool:
        return self._sdk_available

    def adapt_tools(self, hw_tools: HwTools) -> List[Any]:
        """Wrap HwTools methods as @function_tool decorated functions.

        The OpenAI Agents SDK uses standalone functions with type hints
        and docstrings. Each function captures hw_tools via closure.
        """
        if not self._sdk_available:
            return []

        from agents import function_tool

        tools_instance = hw_tools

        @function_tool
        def vocabulary_lookup(receiver_name: str, symbol_name: str) -> str:
            """Three-outcome symbol lookup: native, inherited, or unknown.

            Args:
                receiver_name: The receiver to look up.
                symbol_name: The symbol to find.
            """
            return json.dumps(tools_instance.vocabulary_lookup(receiver_name, symbol_name))

        @function_tool
        def vocabulary_list(receiver_name: str) -> str:
            """List a receiver's vocabulary (symbols from its .hw file).

            Args:
                receiver_name: The receiver whose vocabulary to list.
            """
            return json.dumps(tools_instance.vocabulary_list(receiver_name))

        @function_tool
        def vocabulary_save(receiver_name: str, symbol_name: str, description: str = "") -> str:
            """Append a new symbol to a receiver's .hw file.

            Args:
                receiver_name: The receiver to add the symbol to.
                symbol_name: The symbol name (with # prefix).
                description: Optional description for the symbol.
            """
            desc = description if description else None
            return json.dumps(tools_instance.vocabulary_save(receiver_name, symbol_name, desc))

        @function_tool
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

        @function_tool
        def message_send(sender: str, receiver: str, content: str) -> str:
            """Send a message via the HelloWorld message bus.

            Args:
                sender: The sending agent's name.
                receiver: The receiving agent's name.
                content: The message content.
            """
            return json.dumps(tools_instance.message_send(sender, receiver, content))

        @function_tool
        def message_receive(receiver: str) -> str:
            """Receive the next message from a receiver's inbox.

            Args:
                receiver: The agent whose inbox to check.
            """
            return json.dumps(tools_instance.message_receive(receiver))

        @function_tool
        def receivers_list() -> str:
            """List all receivers found in the vocabulary directory."""
            return json.dumps(tools_instance.receivers_list())

        return [
            vocabulary_lookup,
            vocabulary_list,
            vocabulary_save,
            collision_log,
            message_send,
            message_receive,
            receivers_list,
        ]

    def create_agent(self, name: str, system_prompt: str, tools: List[Any]) -> Any:
        """Create an OpenAI Agents SDK Agent.

        Args:
            name: Agent name (e.g. 'Codex').
            system_prompt: The agent's system instructions.
            tools: List of @function_tool decorated functions.
        """
        if not self._sdk_available:
            raise ImportError("openai-agents is required. Install with: pip install openai-agents")

        from agents import Agent

        return Agent(
            name=name,
            instructions=system_prompt,
            tools=tools,
        )

    async def query(self, agent: Any, prompt: str) -> str:
        """Run a prompt through the OpenAI Agents SDK agent.

        Uses Runner.run() which handles the tool-call loop internally.
        Returns the agent's final text output.
        """
        if not self._sdk_available:
            raise ImportError("openai-agents is required. Install with: pip install openai-agents")

        from agents import Runner

        result = await Runner.run(agent, prompt)
        return result.final_output
