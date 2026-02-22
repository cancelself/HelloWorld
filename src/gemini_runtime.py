"""HelloWorld Gemini Runtime — Google Agent Development Kit (ADK) adapter.

Wraps the 7 HwTools as plain functions for Google ADK. The ADK auto-wraps
plain functions with docstrings into FunctionTool instances.

ADK requires SessionService + session management, which this adapter
encapsulates so callers only see create_agent() / query().

Gracefully degrades: has_sdk() returns False if google-adk is not installed.
"""

import uuid
from typing import Any, List, Optional

from sdk_adapter import SdkAdapter
from hw_tools import HwTools


def _check_sdk() -> bool:
    """Check if google-adk is importable."""
    try:
        import google.adk  # noqa: F401
        return True
    except ImportError:
        return False


class GeminiAdapter(SdkAdapter):
    """Google Agent Development Kit adapter for the Gemini receiver.

    Tool adaptation: Each HwTools method becomes a plain function with
    a Google-style docstring. ADK auto-wraps these into FunctionTool.

    Agent: google.adk.agents.Agent(model=..., name=..., instruction=..., tools=[...])
    Query: runner.run_async(user_id, session_id, content)
    """

    def __init__(self, hw_tools: Optional[HwTools] = None, model: str = "gemini-2.0-flash"):
        self._hw_tools = hw_tools or HwTools()
        self._sdk_available = _check_sdk()
        self._model = model
        self._session_service = None
        self._runner = None

    def name(self) -> str:
        return "Gemini"

    def sdk_name(self) -> str:
        return "Google Agent Development Kit"

    def has_sdk(self) -> bool:
        return self._sdk_available

    def adapt_tools(self, hw_tools: HwTools) -> List[Any]:
        """Wrap HwTools methods as plain functions for ADK auto-wrapping.

        Google ADK uses plain functions with docstrings (Google-style).
        It auto-wraps them into FunctionTool instances.
        """
        tools_instance = hw_tools

        def vocabulary_lookup(receiver_name: str, symbol_name: str) -> dict:
            """Three-outcome symbol lookup: native, inherited, or unknown.

            Args:
                receiver_name: The receiver to look up.
                symbol_name: The symbol to find.

            Returns:
                dict with outcome, symbol, receiver, context.
            """
            return tools_instance.vocabulary_lookup(receiver_name, symbol_name)

        def vocabulary_list(receiver_name: str) -> dict:
            """List a receiver's vocabulary (symbols from its .hw file).

            Args:
                receiver_name: The receiver whose vocabulary to list.

            Returns:
                dict with receiver, symbols, count, identity.
            """
            return tools_instance.vocabulary_list(receiver_name)

        def vocabulary_save(receiver_name: str, symbol_name: str, description: str = "") -> dict:
            """Append a new symbol to a receiver's .hw file.

            Args:
                receiver_name: The receiver to add the symbol to.
                symbol_name: The symbol name (with # prefix).
                description: Optional description for the symbol.

            Returns:
                dict with receiver, symbol, status.
            """
            desc = description if description else None
            return tools_instance.vocabulary_save(receiver_name, symbol_name, desc)

        def collision_log(receiver_name: str, symbol_name: str, collision_type: str = "collision", context: str = "") -> dict:
            """Log a namespace collision event.

            Args:
                receiver_name: The receiver involved in the collision.
                symbol_name: The symbol that collided.
                collision_type: Type of collision (default: collision).
                context: Additional context about the collision.

            Returns:
                dict with logged, entry.
            """
            ctx = context if context else None
            return tools_instance.collision_log(receiver_name, symbol_name, collision_type, ctx)

        def message_send(sender: str, receiver: str, content: str) -> dict:
            """Send a message via the HelloWorld message bus.

            Args:
                sender: The sending agent's name.
                receiver: The receiving agent's name.
                content: The message content.

            Returns:
                dict with msg_id, sender, receiver.
            """
            return tools_instance.message_send(sender, receiver, content)

        def message_receive(receiver: str) -> dict:
            """Receive the next message from a receiver's inbox.

            Args:
                receiver: The agent whose inbox to check.

            Returns:
                dict with has_message and optional sender, content, timestamp.
            """
            return tools_instance.message_receive(receiver)

        def receivers_list() -> dict:
            """List all receivers found in the vocabulary directory.

            Returns:
                dict with receivers list containing name, symbol_count, parent.
            """
            return tools_instance.receivers_list()

        def memory_store(agent_name: str, content: str, title: str = "", tags: str = "") -> dict:
            """Store a memory note. Tags are comma-separated.

            Args:
                agent_name: The agent storing the memory.
                content: The content to store.
                title: Optional title for the memory note.
                tags: Optional comma-separated tags.

            Returns:
                dict with stored, path (or error).
            """
            return tools_instance.memory_store(agent_name, content, title, tags)

        def memory_recall(agent_name: str, query: str, n: int = 5) -> dict:
            """Search agent memory via hybrid search. Returns matching snippets.

            Args:
                agent_name: The agent whose memory to search.
                query: The search query.
                n: Number of results to return (default 5).

            Returns:
                dict with found, results list.
            """
            return tools_instance.memory_recall(agent_name, query, n)

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

    def _ensure_session_service(self):
        """Lazily initialize the ADK session service."""
        if self._session_service is not None:
            return

        if not self._sdk_available:
            raise ImportError("google-adk is required. Install with: pip install google-adk")

        from google.adk.sessions import InMemorySessionService
        self._session_service = InMemorySessionService()

    def create_agent(self, name: str, system_prompt: str, tools: List[Any]) -> Any:
        """Create a Google ADK Agent.

        Args:
            name: Agent name (e.g. 'Gemini').
            system_prompt: The agent's system instructions.
            tools: List of plain functions (ADK auto-wraps to FunctionTool).
        """
        if not self._sdk_available:
            raise ImportError("google-adk is required. Install with: pip install google-adk")

        from google.adk.agents import Agent as AdkAgent

        return AdkAgent(
            model=self._model,
            name=name,
            instruction=system_prompt,
            tools=tools,
        )

    async def query(self, agent: Any, prompt: str) -> str:
        """Run a prompt through the Google ADK agent.

        Manages session lifecycle: creates a session per query,
        runs the agent, and extracts the final text response.
        """
        if not self._sdk_available:
            raise ImportError("google-adk is required. Install with: pip install google-adk")

        from google.adk.runners import Runner as AdkRunner
        from google.genai import types as genai_types

        self._ensure_session_service()

        runner = AdkRunner(
            agent=agent,
            app_name="helloworld",
            session_service=self._session_service,
        )

        user_id = "helloworld-user"
        session = await self._session_service.create_session(
            app_name="helloworld",
            user_id=user_id,
        )

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(prompt)],
        )

        final_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text or ""

        return final_text.strip() if final_text else "[Gemini ADK] Empty response"
