"""HelloWorld SDK Adapter — abstract interface for multi-SDK agent runtimes.

Each SDK adapter wraps the same 7 HwTools in its own format and provides
a uniform interface for agent creation and querying. Adapters degrade
gracefully when their SDK is not installed (has_sdk() returns False).
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class SdkAdapter(ABC):
    """Abstract base for SDK-specific agent adapters.

    Implementors: CodexAdapter (OpenAI), GeminiAdapter (Google ADK),
    CopilotAdapter (GitHub Copilot SDK).
    """

    @abstractmethod
    def name(self) -> str:
        """Return the adapter's agent name (e.g. 'Codex', 'Gemini')."""
        ...

    @abstractmethod
    def adapt_tools(self, hw_tools: Any) -> List[Any]:
        """Wrap HwTools methods in the SDK's tool format."""
        ...

    @abstractmethod
    def create_agent(self, name: str, system_prompt: str, tools: List[Any]) -> Any:
        """Create an SDK-specific agent instance."""
        ...

    @abstractmethod
    async def query(self, agent: Any, prompt: str) -> str:
        """Send a prompt to the agent and return the response."""
        ...

    @abstractmethod
    def has_sdk(self) -> bool:
        """Return True if the required SDK is importable."""
        ...

    def sdk_name(self) -> str:
        """Human-readable SDK name for status messages."""
        return f"{self.name()} SDK"
