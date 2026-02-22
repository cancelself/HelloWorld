"""Tests for ClaudeAdapter — Claude Agent SDK adapter.

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
from claude_runtime import ClaudeAdapter, _check_sdk
from hw_tools import HwTools


VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestClaudeAdapterBasics:
    def test_name(self):
        adapter = ClaudeAdapter()
        assert adapter.name() == "Claude"

    def test_sdk_name(self):
        adapter = ClaudeAdapter()
        assert adapter.sdk_name() == "Claude Agent SDK"

    def test_has_sdk_returns_bool(self):
        adapter = ClaudeAdapter()
        assert isinstance(adapter.has_sdk(), bool)

    def test_accepts_hw_tools(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = ClaudeAdapter(hw_tools=tools)
        assert adapter._hw_tools is tools

    def test_default_model(self):
        adapter = ClaudeAdapter()
        assert adapter._model == "claude-opus-4-6"

    def test_custom_model(self):
        adapter = ClaudeAdapter(model="claude-sonnet-4-6")
        assert adapter._model == "claude-sonnet-4-6"


class TestClaudeToolAdaptation:
    """Test that adapt_tools produces the right structure without the SDK."""

    def test_adapt_tools_returns_empty_without_sdk(self):
        adapter = ClaudeAdapter()
        adapter._sdk_available = False
        result = adapter.adapt_tools(HwTools(vocab_dir=VOCAB_DIR))
        assert result == []

    def test_adapt_tools_returns_nine_with_mock_sdk(self):
        """Mock the claude_agent_sdk module to test tool wrapping."""
        mock_tool = lambda f: f  # noqa: E731 — identity decorator

        with patch.dict(sys.modules, {"claude_agent_sdk": MagicMock(tool=mock_tool)}):
            adapter = ClaudeAdapter()
            adapter._sdk_available = True
            tools = adapter.adapt_tools(HwTools(vocab_dir=VOCAB_DIR))
            assert len(tools) == 9

    def test_adapted_tools_call_through(self):
        """Verify wrapped tools actually call HwTools methods."""
        mock_tool = lambda f: f  # noqa: E731

        with patch.dict(sys.modules, {"claude_agent_sdk": MagicMock(tool=mock_tool)}):
            hw_tools = HwTools(vocab_dir=VOCAB_DIR)
            adapter = ClaudeAdapter(hw_tools=hw_tools)
            adapter._sdk_available = True
            tools = adapter.adapt_tools(hw_tools)

            # vocabulary_lookup is the first tool
            vocab_lookup = tools[0]
            result = json.loads(vocab_lookup("Claude", "#parse"))
            assert "outcome" in result
            assert result["receiver"] == "Claude"

    def test_adapted_receivers_list_returns_json(self):
        """The receivers_list tool should return valid JSON."""
        mock_tool = lambda f: f  # noqa: E731

        with patch.dict(sys.modules, {"claude_agent_sdk": MagicMock(tool=mock_tool)}):
            hw_tools = HwTools(vocab_dir=VOCAB_DIR)
            adapter = ClaudeAdapter(hw_tools=hw_tools)
            adapter._sdk_available = True
            tools = adapter.adapt_tools(hw_tools)

            # receivers_list is the last tool
            receivers = json.loads(tools[6]())
            assert "receivers" in receivers
            assert len(receivers["receivers"]) > 0


class TestClaudeAgentCreation:
    def test_create_agent_raises_without_sdk(self):
        adapter = ClaudeAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="claude-agent-sdk"):
            adapter.create_agent("Claude", "prompt", [])

    def test_create_agent_with_mock_sdk(self):
        mock_options_cls = MagicMock()
        mock_sdk = MagicMock()
        mock_sdk.ClaudeAgentOptions = mock_options_cls

        with patch.dict(sys.modules, {"claude_agent_sdk": mock_sdk}):
            adapter = ClaudeAdapter()
            adapter._sdk_available = True
            agent = adapter.create_agent("Claude", "You are Claude", ["tool1"])

            assert agent["name"] == "Claude"
            assert agent["tools"] == ["tool1"]
            mock_options_cls.assert_called_once_with(
                system_prompt="You are Claude",
                permission_mode="bypassPermissions",
                model="claude-opus-4-6",
            )


class TestClaudeQuery:
    @pytest.mark.asyncio
    async def test_query_raises_without_sdk(self):
        adapter = ClaudeAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="claude-agent-sdk"):
            await adapter.query(MagicMock(), "test prompt")

    @pytest.mark.asyncio
    async def test_query_with_mock_sdk(self):
        mock_msg = MagicMock()
        mock_msg.result = "Claude responds"

        async def mock_query(**kwargs):
            yield mock_msg

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query

        with patch.dict(sys.modules, {"claude_agent_sdk": mock_sdk}):
            adapter = ClaudeAdapter()
            adapter._sdk_available = True
            mock_agent = {"options": MagicMock()}
            result = await adapter.query(mock_agent, "Claude #observe")

            assert result == "Claude responds"

    @pytest.mark.asyncio
    async def test_query_empty_response(self):
        async def mock_query(**kwargs):
            return
            yield  # make it an async generator

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query

        with patch.dict(sys.modules, {"claude_agent_sdk": mock_sdk}):
            adapter = ClaudeAdapter()
            adapter._sdk_available = True
            mock_agent = {"options": MagicMock()}
            result = await adapter.query(mock_agent, "test")

            assert result == "[Claude SDK] Empty response"
