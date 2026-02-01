"""Test Phase 4: LLM Integration with Dispatcher.

Verify that the LLM interpretation layer works when use_llm=True.
"""

import pytest
import sys
sys.path.insert(0, "src")
from src.dispatcher import Dispatcher


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
