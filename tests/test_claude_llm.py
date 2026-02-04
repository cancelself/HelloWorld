"""Tests for ClaudeModel — mock mode, BaseLlm contract, parser_func, parallel."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
import pytest
from claude_llm import ClaudeModel, has_anthropic_key
from llm import BaseLlm


class TestHasAnthropicKey:
    def test_no_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert has_anthropic_key() is False

    def test_with_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        assert has_anthropic_key() is True

    def test_empty_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        assert has_anthropic_key() is False


class TestClaudeModelInheritance:
    def test_is_base_llm(self):
        model = ClaudeModel(api_key=None)
        assert isinstance(model, BaseLlm)

    def test_default_params(self):
        model = ClaudeModel(api_key=None)
        assert model.model_name == "claude-sonnet-4-20250514"
        assert model.temperature == 0.3
        assert model.max_tokens == 1024

    def test_custom_params(self):
        model = ClaudeModel(
            model_name="claude-haiku-4-20250514",
            temperature=0.7,
            max_tokens=512,
            api_key=None,
            system_prompt="You are a test agent.",
        )
        assert model.model_name == "claude-haiku-4-20250514"
        assert model.temperature == 0.7
        assert model.max_tokens == 512
        assert model.system_prompt == "You are a test agent."


class TestMockMode:
    """Tests that run without an API key (mock mode)."""

    def setup_method(self):
        self.model = ClaudeModel(api_key=None)

    def test_mock_generic(self):
        result = self.model.call("hello world")
        assert result.startswith("[Claude] Simulated response to:")

    def test_mock_collision(self):
        result = self.model.call("handle collision on #fire")
        assert "Collision detected" in result

    def test_mock_interpretation_sunyata(self):
        result = self.model.call("interpret: #Sunyata")
        assert "Emptiness" in result

    def test_mock_interpretation_collision(self):
        result = self.model.call("interpret: #Collision")
        assert "friction" in result

    def test_mock_interpretation_generic(self):
        result = self.model.call("interpret: #Unknown")
        assert "boundary" in result


class TestParserFunc:
    def test_parser_func_applied(self):
        model = ClaudeModel(api_key=None)
        result = model.call("hello", parser_func=lambda s: s.upper())
        assert result == result.upper()

    def test_parser_func_none(self):
        model = ClaudeModel(api_key=None)
        result = model.call("hello", parser_func=None)
        assert isinstance(result, str)


class TestCallParallel:
    def test_parallel_returns_all(self):
        model = ClaudeModel(api_key=None)
        prompts = ["hello 1", "hello 2", "hello 3"]
        results = model.call_parallel(prompts)
        assert len(results) == 3
        assert all(r is not None for r in results)

    def test_parallel_preserves_order(self):
        model = ClaudeModel(api_key=None)
        prompts = ["interpret: #Sunyata", "interpret: #Collision"]
        results = model.call_parallel(prompts)
        assert "Emptiness" in results[0]
        assert "friction" in results[1]


class TestEvaluateFidelity:
    def test_high_fidelity(self):
        model = ClaudeModel(api_key=None)
        result = model.evaluate_fidelity("the symbol is native to this identity", "native")
        assert result["score"] == 0.95
        assert result["resonance"] == "High"

    def test_low_fidelity(self):
        model = ClaudeModel(api_key=None)
        result = model.evaluate_fidelity("something unrelated", "native")
        assert result["score"] == 0.4
        assert result["resonance"] == "Low"
