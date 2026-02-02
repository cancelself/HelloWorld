"""Test Phase 4: LLM Integration with Dispatcher.

Verify that the LLM interpretation layer works when use_llm=True.
Tests with @pytest.mark.skipif for real API calls.
"""

import os
import pytest
import sys
from unittest.mock import MagicMock
sys.path.insert(0, "src")
from src.dispatcher import Dispatcher
from src.llm import GeminiModel, has_api_key
from src.prompts import scoped_lookup_prompt, message_prompt, collision_prompt


def test_dispatcher_llm_flag():
    """Verify dispatcher accepts use_llm flag."""
    dispatcher_no_llm = Dispatcher(use_llm=False)
    assert dispatcher_no_llm.use_llm is False
    assert dispatcher_no_llm.llm is None

    dispatcher_with_llm = Dispatcher(use_llm=True)
    assert dispatcher_with_llm.use_llm is True
    assert dispatcher_with_llm.llm is not None


def test_llm_interpretation_scoped_lookup():
    """Verify LLM interprets scoped lookups when enabled."""
    dispatcher = Dispatcher(use_llm=True)

    # Bootstrap creates Claude with minimal core
    dispatcher.dispatch_source("Claude # → [#observe, #act]")

    # Query Claude for #observe — should get LLM interpretation
    result = dispatcher.dispatch_source("Claude #observe")
    assert len(result) > 0
    assert "Claude #observe" in result[0]
    # LLM response should be more than just "is native to this identity"
    assert "native to this identity" not in result[0] or "[Gemini" in result[0]


def test_llm_interpretation_message():
    """Verify LLM interprets messages when enabled."""
    dispatcher = Dispatcher(use_llm=True)

    # Bootstrap Gemini
    dispatcher.dispatch_source("Gemini # → [#Love, #Sunyata]")

    # Send message to Gemini
    result = dispatcher.dispatch_source("Gemini reflect: #Love")
    assert len(result) > 0
    assert "Gemini" in result[0]


def test_llm_disabled_preserves_structural_behavior():
    """Verify use_llm=False maintains template responses."""
    dispatcher = Dispatcher(use_llm=False)

    dispatcher.dispatch_source("TestReceiver # → [#test]")

    # Scoped lookup should return structural response
    result = dispatcher.dispatch_source("TestReceiver #test")
    assert len(result) > 0
    assert "is native to this identity" in result[0]


def test_llm_fallback_on_error():
    """Verify graceful fallback if LLM interpretation fails."""
    # This test would require mocking LLM failure
    # For now, verify that message bus fallback exists
    dispatcher = Dispatcher(use_llm=True)
    dispatcher.dispatch_source("Claude # → [#test]")

    # Even if LLM fails, should get some response (structural or message bus)
    result = dispatcher.dispatch_source("Claude #test")
    assert len(result) > 0


def test_mock_fallback_when_no_api_key():
    """GeminiModel.call() uses mock when no API key is set."""
    model = GeminiModel(api_key=None)
    # Force no key even if env var is set
    model.api_key = None
    response = model.call("interpret: #Sunyata")
    assert "Emptiness" in response or "emptiness" in response


def test_has_api_key_reflects_env():
    """has_api_key() reflects GEMINI_API_KEY env var."""
    old = os.environ.pop("GEMINI_API_KEY", None)
    try:
        assert not has_api_key()
        os.environ["GEMINI_API_KEY"] = "test-key"
        assert has_api_key()
    finally:
        if old is not None:
            os.environ["GEMINI_API_KEY"] = old
        else:
            os.environ.pop("GEMINI_API_KEY", None)


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — skipping real API test"
)
def test_real_gemini_api_call():
    """Integration test: call the real Gemini API.

    Only runs when GEMINI_API_KEY is set in the environment.
    """
    model = GeminiModel()
    response = model.call("What is 2 + 2? Answer with just the number.")
    assert response  # Non-empty
    assert "4" in response


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — skipping real API test"
)
def test_real_gemini_collision_synthesis():
    """Integration test: real LLM collision synthesis through dispatcher.

    Only runs when GEMINI_API_KEY is set.
    """
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    dispatcher = Dispatcher(use_llm=True)

    # Both Claude and Codex hold #parse natively
    results = dispatcher.dispatch_source("Claude send: #parse to: Codex")
    assert len(results) == 1
    result = results[0]

    # Should detect collision AND produce real LLM synthesis
    assert "COLLISION" in result
    assert "COLLISION SYNTHESIS" in result
    # Real LLM response should be substantive (not mock)
    assert "[Gemini 2.0 Flash] Simulated" not in result


# --- Prompt builder unit tests ---

def test_scoped_lookup_prompt_contains_vocabulary():
    """scoped_lookup_prompt includes receiver vocabulary and global definition."""
    prompt = scoped_lookup_prompt("Claude", "#parse", ["#dispatch", "#parse", "#reflect"], "Decomposing syntax")
    assert "Claude" in prompt
    assert "#parse" in prompt
    assert "['#dispatch', '#parse', '#reflect']" in prompt
    assert "Decomposing syntax" in prompt
    assert "1-2 sentences" in prompt


def test_scoped_lookup_prompt_handles_missing_global_def():
    """scoped_lookup_prompt uses fallback when no global definition exists."""
    prompt = scoped_lookup_prompt("Gemini", "#mystery", ["#observe"], None)
    assert "no global definition" in prompt


def test_message_prompt_contains_vocabulary():
    """message_prompt includes receiver vocabulary and message content."""
    prompt = message_prompt("Gemini", ["#Love", "#Sunyata"], "Gemini reflect: #Love")
    assert "Gemini" in prompt
    assert "['#Love', '#Sunyata']" in prompt
    assert "reflect: #Love" in prompt
    assert "Constraint is character" in prompt


def test_collision_prompt_contains_both_vocabularies():
    """collision_prompt includes both sender and target vocabularies."""
    prompt = collision_prompt(
        "Claude", ["#parse", "#dispatch"],
        "Codex", ["#execute", "#parse"],
        "#parse",
    )
    assert "Claude" in prompt
    assert "Codex" in prompt
    assert "['#parse', '#dispatch']" in prompt
    assert "['#execute', '#parse']" in prompt
    assert "#parse" in prompt
    assert "synthesize" in prompt.lower()


# --- Dispatcher prompt integration tests (mock LLM) ---

def test_scoped_lookup_sends_vocabulary_prompt():
    """Dispatcher passes vocabulary-aware prompt to LLM on scoped lookup."""
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    dispatcher = Dispatcher(use_llm=True)
    dispatcher.dispatch_source("Claude # → [#observe, #act]")

    # Replace the LLM with a mock that captures the prompt
    mock_llm = MagicMock()
    mock_llm.call.return_value = "mocked interpretation"
    dispatcher.llm = mock_llm

    dispatcher.dispatch_source("Claude #observe")

    mock_llm.call.assert_called_once()
    prompt_arg = mock_llm.call.call_args[0][0]
    assert "You are Claude" in prompt_arg
    assert "#observe" in prompt_arg
    assert "vocabulary" in prompt_arg.lower()


def test_message_sends_vocabulary_prompt():
    """Dispatcher passes vocabulary-aware prompt to LLM on message dispatch."""
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    dispatcher = Dispatcher(use_llm=True)
    dispatcher.dispatch_source("Gemini # → [#Love, #Sunyata]")

    mock_llm = MagicMock()
    mock_llm.call.return_value = "mocked message response"
    dispatcher.llm = mock_llm

    dispatcher.dispatch_source("Gemini reflect: #Love")

    mock_llm.call.assert_called_once()
    prompt_arg = mock_llm.call.call_args[0][0]
    assert "You are Gemini" in prompt_arg
    assert "Constraint is character" in prompt_arg


def test_collision_sends_vocabulary_prompt():
    """Dispatcher passes vocabulary-aware prompt to LLM on collision synthesis."""
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    dispatcher = Dispatcher(use_llm=True)

    # Both Claude and Codex hold #parse natively (from bootstrap)
    mock_llm = MagicMock()
    mock_llm.call.return_value = "mocked collision synthesis"
    dispatcher.llm = mock_llm

    dispatcher.dispatch_source("Claude send: #parse to: Codex")

    mock_llm.call.assert_called_once()
    prompt_arg = mock_llm.call.call_args[0][0]
    assert "collision" in prompt_arg.lower()
    assert "#parse" in prompt_arg
    assert "synthesize" in prompt_arg.lower()
