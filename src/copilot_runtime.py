"""HelloWorld Copilot Runtime — GitHub Copilot SDK adapter.

Wraps the 7 HwTools as tool definitions for the GitHub Copilot SDK
(Technical Preview). Uses JSON schema for tool parameters.

The Copilot SDK is event-driven: session.send() triggers processing,
events are collected until session is idle.

Gracefully degrades: has_sdk() returns False if the SDK is not installed.
"""

import json
from typing import Any, List, Optional

from sdk_adapter import SdkAdapter
from hw_tools import HwTools


def _check_sdk() -> bool:
    """Check if the Copilot SDK is importable."""
    try:
        from github_copilot import CopilotClient  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        from agent_framework_github_copilot import CopilotClient  # noqa: F401
        return True
    except ImportError:
        pass
    return False


def _get_client_class():
    """Import the CopilotClient from whichever package is installed."""
    try:
        from github_copilot import CopilotClient
        return CopilotClient
    except ImportError:
        pass
    from agent_framework_github_copilot import CopilotClient
    return CopilotClient


# JSON schemas for tool parameters
_TOOL_SCHEMAS = {
    "vocabulary_lookup": {
        "name": "vocabulary_lookup",
        "description": "Three-outcome symbol lookup: native, inherited, or unknown.",
        "parameters": {
            "type": "object",
            "properties": {
                "receiver_name": {
                    "type": "string",
                    "description": "The receiver to look up.",
                },
                "symbol_name": {
                    "type": "string",
                    "description": "The symbol to find.",
                },
            },
            "required": ["receiver_name", "symbol_name"],
        },
    },
    "vocabulary_list": {
        "name": "vocabulary_list",
        "description": "List a receiver's vocabulary (symbols from its .hw file).",
        "parameters": {
            "type": "object",
            "properties": {
                "receiver_name": {
                    "type": "string",
                    "description": "The receiver whose vocabulary to list.",
                },
            },
            "required": ["receiver_name"],
        },
    },
    "vocabulary_save": {
        "name": "vocabulary_save",
        "description": "Append a new symbol to a receiver's .hw file.",
        "parameters": {
            "type": "object",
            "properties": {
                "receiver_name": {
                    "type": "string",
                    "description": "The receiver to add the symbol to.",
                },
                "symbol_name": {
                    "type": "string",
                    "description": "The symbol name (with # prefix).",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for the symbol.",
                },
            },
            "required": ["receiver_name", "symbol_name"],
        },
    },
    "collision_log": {
        "name": "collision_log",
        "description": "Log a namespace collision event.",
        "parameters": {
            "type": "object",
            "properties": {
                "receiver_name": {
                    "type": "string",
                    "description": "The receiver involved in the collision.",
                },
                "symbol_name": {
                    "type": "string",
                    "description": "The symbol that collided.",
                },
                "collision_type": {
                    "type": "string",
                    "description": "Type of collision (default: collision).",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context about the collision.",
                },
            },
            "required": ["receiver_name", "symbol_name"],
        },
    },
    "message_send": {
        "name": "message_send",
        "description": "Send a message via the HelloWorld message bus.",
        "parameters": {
            "type": "object",
            "properties": {
                "sender": {
                    "type": "string",
                    "description": "The sending agent's name.",
                },
                "receiver": {
                    "type": "string",
                    "description": "The receiving agent's name.",
                },
                "content": {
                    "type": "string",
                    "description": "The message content.",
                },
            },
            "required": ["sender", "receiver", "content"],
        },
    },
    "message_receive": {
        "name": "message_receive",
        "description": "Receive the next message from a receiver's inbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "receiver": {
                    "type": "string",
                    "description": "The agent whose inbox to check.",
                },
            },
            "required": ["receiver"],
        },
    },
    "receivers_list": {
        "name": "receivers_list",
        "description": "List all receivers found in the vocabulary directory.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


class CopilotAdapter(SdkAdapter):
    """GitHub Copilot SDK adapter for the Copilot receiver.

    Tool adaptation: Each HwTools method is registered via JSON schema.
    Tool calls are dispatched through a handler map.

    Agent: CopilotClient() + create_session()
    Query: session.send() -> collect events until idle
    """

    def __init__(self, hw_tools: Optional[HwTools] = None):
        self._hw_tools = hw_tools or HwTools()
        self._sdk_available = _check_sdk()
        self._client = None
        self._tool_handlers = {}

    def name(self) -> str:
        return "Copilot"

    def sdk_name(self) -> str:
        return "GitHub Copilot SDK"

    def has_sdk(self) -> bool:
        return self._sdk_available

    def _build_tool_handlers(self, hw_tools: HwTools) -> dict:
        """Build a map of tool_name -> handler function."""
        return {
            "vocabulary_lookup": lambda params: hw_tools.vocabulary_lookup(
                params["receiver_name"], params["symbol_name"]
            ),
            "vocabulary_list": lambda params: hw_tools.vocabulary_list(
                params["receiver_name"]
            ),
            "vocabulary_save": lambda params: hw_tools.vocabulary_save(
                params["receiver_name"],
                params["symbol_name"],
                params.get("description") or None,
            ),
            "collision_log": lambda params: hw_tools.collision_log(
                params["receiver_name"],
                params["symbol_name"],
                params.get("collision_type", "collision"),
                params.get("context") or None,
            ),
            "message_send": lambda params: hw_tools.message_send(
                params["sender"], params["receiver"], params["content"]
            ),
            "message_receive": lambda params: hw_tools.message_receive(
                params["receiver"]
            ),
            "receivers_list": lambda params: hw_tools.receivers_list(),
        }

    def adapt_tools(self, hw_tools: HwTools) -> List[Any]:
        """Return JSON schema tool definitions for the Copilot SDK.

        The Copilot SDK uses JSON schemas to define tools. Tool calls
        are dispatched to handler functions via handle_tool_call().
        """
        self._tool_handlers = self._build_tool_handlers(hw_tools)
        return list(_TOOL_SCHEMAS.values())

    def handle_tool_call(self, tool_name: str, arguments: dict) -> str:
        """Dispatch a tool call from the Copilot SDK to the appropriate handler.

        Args:
            tool_name: Name of the tool being called.
            arguments: Tool call arguments as a dict.

        Returns:
            JSON string with the tool result.
        """
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        return json.dumps(handler(arguments))

    def create_agent(self, name: str, system_prompt: str, tools: List[Any]) -> Any:
        """Create a Copilot SDK session.

        Args:
            name: Agent name (e.g. 'Copilot').
            system_prompt: The agent's system instructions.
            tools: List of JSON schema tool definitions.

        Returns:
            A dict representing the session configuration, since the
            Copilot SDK uses a client+session model rather than a standalone agent.
        """
        if not self._sdk_available:
            raise ImportError(
                "github-copilot-sdk is required. Install with: "
                "pip install github-copilot-sdk"
            )

        return {
            "name": name,
            "system_prompt": system_prompt,
            "tools": tools,
            "client_class": _get_client_class(),
        }

    async def query(self, agent: Any, prompt: str) -> str:
        """Send a prompt through the Copilot SDK and collect the response.

        The Copilot SDK is event-driven: we send a message and collect
        events until the session becomes idle. Tool calls are handled
        inline via handle_tool_call().
        """
        if not self._sdk_available:
            raise ImportError(
                "github-copilot-sdk is required. Install with: "
                "pip install github-copilot-sdk"
            )

        ClientClass = agent["client_class"]
        client = ClientClass()

        session = client.create_session(
            system_prompt=agent["system_prompt"],
            tools=agent["tools"],
        )

        response_parts = []
        async for event in session.send(prompt):
            if hasattr(event, "type"):
                if event.type == "tool_call":
                    result = self.handle_tool_call(event.tool_name, event.arguments)
                    await session.submit_tool_result(event.call_id, result)
                elif event.type == "text":
                    response_parts.append(event.text)
                elif event.type == "done":
                    break

        return "".join(response_parts).strip() if response_parts else "[Copilot] Empty response"
