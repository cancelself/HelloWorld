"""Tests for CopilotAdapter — GitHub Copilot SDK adapter.

Layer 1: Unit tests (no SDK needed) — tool schemas, handler dispatch.
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
from copilot_runtime import CopilotAdapter, _check_sdk, _TOOL_SCHEMAS
from hw_tools import HwTools


VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestCopilotAdapterBasics:
    def test_name(self):
        adapter = CopilotAdapter()
        assert adapter.name() == "Copilot"

    def test_sdk_name(self):
        adapter = CopilotAdapter()
        assert adapter.sdk_name() == "GitHub Copilot SDK"

    def test_has_sdk_returns_bool(self):
        adapter = CopilotAdapter()
        assert isinstance(adapter.has_sdk(), bool)

    def test_accepts_hw_tools(self):
        tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = CopilotAdapter(hw_tools=tools)
        assert adapter._hw_tools is tools


class TestCopilotToolSchemas:
    """Verify JSON schema structure for all 7 tools."""

    def test_nine_schemas_defined(self):
        assert len(_TOOL_SCHEMAS) == 9

    def test_all_schemas_have_required_fields(self):
        for name, schema in _TOOL_SCHEMAS.items():
            assert "name" in schema, f"{name} missing 'name'"
            assert "description" in schema, f"{name} missing 'description'"
            assert "parameters" in schema, f"{name} missing 'parameters'"
            assert schema["parameters"]["type"] == "object"

    def test_vocabulary_lookup_schema(self):
        schema = _TOOL_SCHEMAS["vocabulary_lookup"]
        params = schema["parameters"]
        assert "receiver_name" in params["properties"]
        assert "symbol_name" in params["properties"]
        assert params["required"] == ["receiver_name", "symbol_name"]

    def test_message_send_schema(self):
        schema = _TOOL_SCHEMAS["message_send"]
        params = schema["parameters"]
        assert "sender" in params["properties"]
        assert "receiver" in params["properties"]
        assert "content" in params["properties"]
        assert set(params["required"]) == {"sender", "receiver", "content"}

    def test_receivers_list_schema_no_required(self):
        schema = _TOOL_SCHEMAS["receivers_list"]
        assert schema["parameters"]["required"] == []


class TestCopilotToolAdaptation:
    def test_adapt_tools_returns_nine_schemas(self):
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = CopilotAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)
        assert len(tools) == 9

    def test_adapt_tools_are_dicts(self):
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = CopilotAdapter(hw_tools=hw_tools)
        tools = adapter.adapt_tools(hw_tools)
        for tool in tools:
            assert isinstance(tool, dict)
            assert "name" in tool

    def test_adapt_tools_builds_handlers(self):
        hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        adapter = CopilotAdapter(hw_tools=hw_tools)
        adapter.adapt_tools(hw_tools)
        assert len(adapter._tool_handlers) == 9


class TestCopilotToolDispatch:
    """Test handle_tool_call dispatches to HwTools correctly."""

    def setup_method(self):
        self.hw_tools = HwTools(vocab_dir=VOCAB_DIR)
        self.adapter = CopilotAdapter(hw_tools=self.hw_tools)
        self.adapter.adapt_tools(self.hw_tools)

    def test_vocabulary_lookup_dispatch(self):
        result = json.loads(self.adapter.handle_tool_call(
            "vocabulary_lookup",
            {"receiver_name": "Claude", "symbol_name": "#parse"},
        ))
        assert "outcome" in result
        assert result["receiver"] == "Claude"

    def test_vocabulary_list_dispatch(self):
        result = json.loads(self.adapter.handle_tool_call(
            "vocabulary_list",
            {"receiver_name": "HelloWorld"},
        ))
        assert "symbols" in result
        assert result["receiver"] == "HelloWorld"

    def test_receivers_list_dispatch(self):
        result = json.loads(self.adapter.handle_tool_call(
            "receivers_list",
            {},
        ))
        assert "receivers" in result

    def test_unknown_tool_returns_error(self):
        result = json.loads(self.adapter.handle_tool_call(
            "nonexistent_tool",
            {},
        ))
        assert "error" in result


class TestCopilotAgentCreation:
    def test_create_agent_raises_without_sdk(self):
        adapter = CopilotAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="github-copilot-sdk"):
            adapter.create_agent("Copilot", "prompt", [])

    def test_create_agent_returns_config_dict(self):
        mock_client_cls = MagicMock()

        with patch("copilot_runtime._get_client_class", return_value=mock_client_cls):
            adapter = CopilotAdapter()
            adapter._sdk_available = True
            agent = adapter.create_agent("Copilot", "You are Copilot", ["tool1"])

            assert isinstance(agent, dict)
            assert agent["name"] == "Copilot"
            assert agent["system_prompt"] == "You are Copilot"
            assert agent["tools"] == ["tool1"]
            assert agent["client_class"] is mock_client_cls


class TestCopilotQuery:
    @pytest.mark.asyncio
    async def test_query_raises_without_sdk(self):
        adapter = CopilotAdapter()
        adapter._sdk_available = False
        with pytest.raises(ImportError, match="github-copilot-sdk"):
            await adapter.query(MagicMock(), "test prompt")
