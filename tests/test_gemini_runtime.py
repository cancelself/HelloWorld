"""Tests for GeminiAdapter — Google Agent Development Kit adapter.

Layer 1: Unit tests (no SDK needed) — tool adaptation, structure.
Layer 2: Mock SDK tests — verify create_agent/query flow.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from gemini_runtime import GeminiAdapter, _check_sdk
from hw_tools import HwTools


VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestGeminiAdapterBasics:
    def test_name(self):
        adapter = GeminiAdapter()
        assert adapter.name() == "Gemini"

    def test_sdk_name(self):
        adapter = GeminiAdapter()
        assert adapter.sdk_name() == "Google Agent Development Kit"

    def test_has_sdk_returns_bool(self):
        adapter = GeminiAdapter()
        assert isinstance(adapter.has_sdk(), bool)

    def test_accepts_hw_tools(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=tools)
        assert adapter._hw_tools is tools

    def test_custom_model(self):
        adapter = GeminiAdapter(model="gemini-1.5-pro")
        assert adapter._model == "gemini-1.5-pro"


class TestGeminiToolAdaptation:
    """Test that adapt_tools produces the right structure."""

    def test_adapt_tools_returns_nine_functions(self):
        """ADK tools are plain functions — no SDK import needed."""
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)
        assert len(tools) == 9

    def test_adapted_tools_are_callable(self):
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)
        for tool in tools:
            assert callable(tool)

    def test_adapted_tools_have_docstrings(self):
        """ADK requires docstrings for tool description extraction."""
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)
        for tool in tools:
            assert tool.__doc__ is not None
            assert len(tool.__doc__) > 10

    def test_adapted_tools_call_through(self):
        """Verify wrapped tools actually call HwTools methods."""
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)

        # vocabulary_lookup is the first tool
        vocab_lookup = tools[0]
        result = vocab_lookup("Claude", "#parse")
        assert isinstance(result, dict)
        assert "outcome" in result
        assert result["receiver"] == "Claude"

    def test_adapted_receivers_list(self):
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)

        # receivers_list is the last tool
        result = tools[6]()
        assert isinstance(result, dict)
        assert "receivers" in result

    def test_vocabulary_list_returns_dict(self):
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = GeminiAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)

        # vocabulary_list is the second tool
        result = tools[1]("HelloWorld")
        assert isinstance(result, dict)
        assert "symbols" in result


class TestGeminiAgentCreation:
    def test_create_agent_raises_without_sdk(self):
        adapter = GeminiAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="google-adk"):
            adapter.create_agent("Gemini", "prompt", [])

    def test_create_agent_with_mock_sdk(self):
        mock_adk_agent = MagicMock()

        # Build mock module hierarchy: google.adk.agents.Agent
        mock_google = MagicMock()
        mock_google.adk.agents.Agent = mock_adk_agent

        with patch.dict(sys.modules, {
            "google": mock_google,
            "google.adk": mock_google.adk,
            "google.adk.agents": mock_google.adk.agents,
        }):
            adapter = GeminiAdapter()
            adapter._sdk_available = True
            agent = adapter.create_agent("Gemini", "You are Gemini", ["tool1"])

            mock_adk_agent.assert_called_once_with(
                model="gemini-2.0-flash",
                name="Gemini",
                instruction="You are Gemini",
                tools=["tool1"],
            )


class TestGeminiQuery:
    @pytest.mark.asyncio
    async def test_query_raises_without_sdk(self):
        adapter = GeminiAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="google-adk"):
            await adapter.query(MagicMock(), "test prompt")


class TestGeminiSessionService:
    def test_ensure_session_raises_without_sdk(self):
        adapter = GeminiAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="google-adk"):
            adapter._ensure_session_service()
