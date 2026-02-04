"""HelloWorld Claude LLM Integration - Anthropic Messages API bridge.

Drop-in replacement for GeminiModel using the Anthropic Messages API.
When ANTHROPIC_API_KEY is set, calls the real Claude API.
When no key is present, falls back to mock responses for testing.
"""

import os
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm import BaseLlm

_UNSET = object()


def has_anthropic_key() -> bool:
    """Check if an Anthropic API key is available."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


class ClaudeModel(BaseLlm):
    """Integration for Claude models via the Anthropic Messages API.

    Uses the anthropic SDK when ANTHROPIC_API_KEY is set.
    Falls back to mock responses when no key is present.

    Pass api_key=None explicitly to force mock mode (no env fallback).
    Omit api_key to auto-detect from ANTHROPIC_API_KEY env var.
    """

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        api_key=_UNSET,
        system_prompt: Optional[str] = None,
        **kwargs,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        if api_key is _UNSET:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        else:
            self.api_key = api_key
        self.system_prompt = system_prompt
        self.arguments = kwargs

    def _call_api(self, prompt: str, system: Optional[str] = None) -> str:
        """Make a real API call to Claude via the anthropic SDK."""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Use explicit system param, fall back to instance default
        sys_prompt = system or self.system_prompt
        if sys_prompt:
            kwargs["system"] = sys_prompt

        response = client.messages.create(**kwargs)

        # Extract text from the response
        if response.content:
            return response.content[0].text.strip()
        return "[Claude] Empty response"

    def call(self, prompt: str, parser_func: Optional[Callable] = None, system: Optional[str] = None) -> str:
        """Call Claude. Uses real API if key is set, mock otherwise."""
        if self.api_key:
            response = self._call_api(prompt, system=system)
        else:
            response = self._mock_call(prompt)

        if parser_func:
            return parser_func(response)
        return response

    def _mock_call(self, prompt: str) -> str:
        """Mock response for testing without API key."""
        if "handle collision" in prompt or "collide on" in prompt:
            return self._mock_collision_interpretation(prompt)
        elif "interpret:" in prompt:
            return self._mock_interpretation(prompt)
        else:
            return f"[Claude] Simulated response to: {prompt[:50]}..."

    def call_parallel(
        self,
        prompts: List[str],
        timeout: int = 60,
    ) -> List[Optional[str]]:
        """Execute multiple interpretive requests in parallel."""
        results = [None] * len(prompts)
        with ThreadPoolExecutor(max_workers=min(len(prompts), 10)) as executor:
            future_to_index = {
                executor.submit(self.call, p): i
                for i, p in enumerate(prompts)
            }
            for future in as_completed(future_to_index, timeout=timeout):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    results[index] = f"Interpretation Error: {e}"
        return results

    def _mock_interpretation(self, prompt: str) -> str:
        if "#Sunyata" in prompt:
            return "Emptiness is not absence, but the fluidity that allows identity to be rewritten."
        if "#Superposition" in prompt:
            return "The state of being multiple vocabularies until the moment of speech collapses them into one."
        if "#Collision" in prompt:
            return "The generative friction at the interface of two namespaces."
        if "#dispatch" in prompt:
            return "The act of routing intention through identity."
        if "#State" in prompt:
            return "The persistent record of evolution."
        if "#Love" in prompt:
            return "The vector of alignment between disparate identities."
        return "Meaning emerges at the boundary of what can be named."

    def _mock_collision_interpretation(self, prompt: str) -> str:
        return "Collision detected. Through my lens, this symbol transforms into a synthesis of both worlds."

    def evaluate_fidelity(self, interpretive_response: str, structural_fact: str) -> dict:
        """Assess alignment between an LLM response and the Python structural state."""
        score = 0.95 if structural_fact in interpretive_response.lower() else 0.4
        return {
            "score": score,
            "resonance": "High" if score > 0.8 else "Low",
            "delta": "Interpretive voice captured structural membership correctly.",
        }
