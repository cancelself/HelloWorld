"""Tests for CodexAdapter — OpenAI Agents SDK adapter.

Layer 1: Unit tests (no SDK needed) — tool adaptation, structure.
Layer 2: Mock SDK tests — verify create_agent/query flow.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from codex_runtime import CodexAdapter, _check_sdk
from hw_tools import HwTools


VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestCodexAdapterBasics:
    def test_name(self):
        adapter = CodexAdapter()
        assert adapter.name() == "Codex"

    def test_sdk_name(self):
        adapter = CodexAdapter()
        assert adapter.sdk_name() == "OpenAI Agents SDK"

    def test_has_sdk_returns_bool(self):
        adapter = CodexAdapter()
        assert isinstance(adapter.has_sdk(), bool)

    def test_accepts_hw_tools(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = CodexAdapter(hw_tools=tools)
        assert adapter._hw_tools is tools


class TestCodexToolAdaptation:
    """Test that adapt_tools produces the right structure without the SDK."""

    def test_adapt_tools_returns_empty_without_sdk(self):
        adapter = CodexAdapter()
        adapter._sdk_available = False
        result = adapter.adapt_tools(HwTools(vocab_dir=VOCAB_DIR))
        assert result == []

    def test_adapt_tools_returns_seven_with_mock_sdk(self):
        """Mock the agents module to test tool wrapping."""
        mock_function_tool = lambda f: f  # noqa: E731 — identity decorator

        with patch.dict(sys.modules, {"agents": MagicMock(function_tool=mock_function_tool)}):
            adapter = CodexAdapter()
            adapter._sdk_available = True
            tools = adapter.adapt_tools(HwTools(vocab_dir=VOCAB_DIR))
            assert len(tools) == 7

    def test_adapted_tools_call_through(self):
        """Verify wrapped tools actually call HwTools methods."""
        mock_function_tool = lambda f: f  # noqa: E731

        with patch.dict(sys.modules, {"agents": MagicMock(function_tool=mock_function_tool)}):
            hw_tools = HwTools(vocab_dir=VOCAB_DIR)
            adapter = CodexAdapter(hw_tools=hw_tools)
            adapter._sdk_available = True
            tools = adapter.adapt_tools(hw_tools)

            # vocabulary_lookup is the first tool
            vocab_lookup = tools[0]
            result = json.loads(vocab_lookup("Claude", "#parse"))
            assert "outcome" in result
            assert result["receiver"] == "Claude"

    def test_adapted_receivers_list_returns_json(self):
        """The receivers_list tool should return valid JSON."""
        mock_function_tool = lambda f: f  # noqa: E731

        with patch.dict(sys.modules, {"agents": MagicMock(function_tool=mock_function_tool)}):
            hw_tools = HwTools(vocab_dir=VOCAB_DIR)
            adapter = CodexAdapter(hw_tools=hw_tools)
            adapter._sdk_available = True
            tools = adapter.adapt_tools(hw_tools)

            # receivers_list is the last tool
            receivers = json.loads(tools[6]())
            assert "receivers" in receivers
            assert len(receivers["receivers"]) > 0


class TestCodexAgentCreation:
    def test_create_agent_raises_without_sdk(self):
        adapter = CodexAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="openai-agents"):
            adapter.create_agent("Codex", "prompt", [])

    def test_create_agent_with_mock_sdk(self):
        mock_agent_cls = MagicMock()
        mock_agents = MagicMock()
        mock_agents.Agent = mock_agent_cls

        with patch.dict(sys.modules, {"agents": mock_agents}):
            adapter = CodexAdapter()
            adapter._sdk_available = True
            agent = adapter.create_agent("Codex", "You are Codex", ["tool1"])

            mock_agent_cls.assert_called_once_with(
                name="Codex",
                instructions="You are Codex",
                tools=["tool1"],
            )


class TestCodexQuery:
    @pytest.mark.asyncio
    async def test_query_raises_without_sdk(self):
        adapter = CodexAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="openai-agents"):
            await adapter.query(MagicMock(), "test prompt")

    @pytest.mark.asyncio
    async def test_query_with_mock_sdk(self):
        mock_result = MagicMock()
        mock_result.final_output = "Codex responds"

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=mock_result)

        mock_agents = MagicMock()
        mock_agents.Runner = mock_runner

        with patch.dict(sys.modules, {"agents": mock_agents}):
            adapter = CodexAdapter()
            adapter._sdk_available = True
            result = await adapter.query(MagicMock(), "Codex #execute")

            assert result == "Codex responds"
            mock_runner.run.assert_called_once()
