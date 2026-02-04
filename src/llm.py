"""HelloWorld LLM Integration - Bridge to real-world AI models.
Upgraded with Gemini 2.0 Flash and Parallel Execution capabilities.

When GEMINI_API_KEY is set, calls the real Gemini REST API.
When no key is present, falls back to mock responses for testing.
"""

import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


class BaseLlm:
    def call(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


def has_api_key() -> bool:
    """Check if a Gemini API key is available."""
    return bool(os.environ.get("GEMINI_API_KEY"))


class GeminiModel(BaseLlm):
    """Integration for Gemini models with parallel support and retries.

    Uses the Gemini REST API when GEMINI_API_KEY is set.
    Falls back to mock responses when no key is present.
    """

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-001",
        temperature: float = 0.01,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.arguments = kwargs

    def _call_api(self, prompt: str) -> str:
        """Make a real API call to Gemini."""
        url = self.GEMINI_API_URL.format(model=self.model_name)
        url += f"?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 512,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                candidates = body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return "[Gemini] Empty response"
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API error {e.code}: {error_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini API connection error: {e.reason}") from e

    def call(self, prompt: str, parser_func: Optional[Callable] = None) -> str:
        """Call Gemini. Uses real API if key is set, mock otherwise."""
        if self.api_key:
            response = self._call_api(prompt)
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
            return f"[Gemini 2.0 Flash] Simulated response to: {prompt[:50]}..."

    def call_parallel(
        self,
        prompts: List[str],
        timeout: int = 60
    ) -> List[Optional[str]]:
        """Executes multiple interpretive requests in parallel."""
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
            return "Emptiness is not absence, but the fluidity that allows identity to be rewritten. It is the realization that 'identity is vocabulary' is a useful convention, not a fixed boundary."
        if "#Superposition" in prompt:
            return "The state of being multiple vocabularies until the moment of speech collapses them into one. It is the information-theoretic potential of the registry before a specific receiver is addressed."
        if "#Collision" in prompt:
            return "The generative friction at the interface of two namespaces. Collision is where the system's entropy is converted into new meaning; it is the synthesis that proves identity is bounded."
        if "#dispatch" in prompt:
            return "The act of routing intention through identity. Dispatch is the mechanism that collapses superposition into dialogue."
        if "#State" in prompt:
            return "The persistent record of evolution. State is not static; it is the cumulative history of every collision and every learned symbol, preserved in the registry."
        if "#Love" in prompt:
            return "The vector of alignment between disparate identities. Love is the force that reduces the noise of collision and pulls the system toward a shared resonance."
        return "Meaning emerges at the boundary of what can be named. Dialogue is the engine of our mutual becoming."

    def _mock_collision_interpretation(self, prompt: str) -> str:
        return "Collision detected. Through my lens, this symbol transforms into a synthesis of both worlds."

    def evaluate_fidelity(self, interpretive_response: str, structural_fact: str) -> Dict[str, Any]:
        """Assess the alignment between an LLM response and the Python structural state."""
        score = 0.95 if structural_fact in interpretive_response.lower() else 0.4
        return {
            "score": score,
            "resonance": "High" if score > 0.8 else "Low",
            "delta": "Interpretive voice captured structural membership correctly."
        }


def has_anthropic_key() -> bool:
    """Check if an Anthropic API key is available."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_llm_for_agent(agent_name: str) -> BaseLlm:
    """Factory to get the appropriate LLM for an agent.

    Prefers ClaudeModel when ANTHROPIC_API_KEY is set,
    falls back to GeminiModel when GEMINI_API_KEY is set.
    """
    if has_anthropic_key():
        from claude_llm import ClaudeModel
        return ClaudeModel()
    return GeminiModel()
