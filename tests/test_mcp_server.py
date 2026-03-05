"""Tests for HelloWorld MCP server tools."""

import sys
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
import mcp_server
from mcp_server import mcp


@pytest.fixture(autouse=True)
def use_temp_vocab(tmp_path):
    """Point the MCP server's tools and dispatcher at a temp vocab dir."""
    # Create a minimal HelloWorld.hw
    (tmp_path / "HelloWorld.hw").write_text(
        "# HelloWorld\n## Collision\n- When namespaces meet\n## Sunyata\n- Emptiness\n"
    )
    # Create a test receiver
    (tmp_path / "TestAgent.hw").write_text(
        "# TestAgent : HelloWorld\n## observe\n- Watch and learn\n## plan\n- Make a plan\n"
    )
    vocab_dir = str(tmp_path)

    from dispatcher import Dispatcher
    from hw_tools import HwTools

    new_dispatcher = Dispatcher(vocab_dir=vocab_dir)
    new_tools = HwTools(vocab_dir=vocab_dir)

    # Swap the module-level instances
    old_dispatcher = mcp_server._dispatcher
    old_tools = mcp_server._tools
    mcp_server._dispatcher = new_dispatcher
    mcp_server._tools = new_tools
    yield
    mcp_server._dispatcher = old_dispatcher
    mcp_server._tools = old_tools


class TestDispatchTool:
    def test_dispatch_bare_receiver(self):
        result = mcp_server.dispatch("@TestAgent")
        assert "results" in result
        assert len(result["results"]) > 0

    def test_dispatch_scoped_lookup(self):
        result = mcp_server.dispatch("@TestAgent.#observe")
        assert "results" in result
        assert any("observe" in r for r in result["results"])

    def test_dispatch_unknown_receiver(self):
        result = mcp_server.dispatch("@Nobody")
        assert "results" in result


class TestVocabularyTools:
    def test_vocabulary_list(self):
        result = mcp_server.vocabulary_list("TestAgent")
        assert result["receiver"] == "TestAgent"
        assert result["count"] == 2

    def test_vocabulary_lookup_native(self):
        result = mcp_server.vocabulary_lookup("TestAgent", "#observe")
        assert result["outcome"] == "native"

    def test_vocabulary_lookup_inherited(self):
        result = mcp_server.vocabulary_lookup("TestAgent", "#Collision")
        assert result["outcome"] == "inherited"

    def test_vocabulary_lookup_unknown(self):
        result = mcp_server.vocabulary_lookup("TestAgent", "#xyzzy")
        assert result["outcome"] == "unknown"

    def test_vocabulary_save(self):
        result = mcp_server.vocabulary_save("TestAgent", "#newskill", "A newly learned skill")
        assert result["status"] == "saved"
        check = mcp_server.vocabulary_lookup("TestAgent", "#newskill")
        assert check["outcome"] == "native"

    def test_vocabulary_save_duplicate(self):
        result = mcp_server.vocabulary_save("TestAgent", "#observe", "Already exists")
        assert result["status"] == "already_exists"


class TestReceiversList:
    def test_lists_receivers(self):
        result = mcp_server.receivers_list()
        names = [r["name"] for r in result["receivers"]]
        assert "TestAgent" in names
        assert "HelloWorld" in names


class TestMessageTools:
    def test_send_and_receive(self):
        send_result = mcp_server.message_send("alice", "bob", "hello bob")
        assert "msg_id" in send_result
        recv_result = mcp_server.message_receive("bob")
        assert recv_result["has_message"] is True
        assert recv_result["content"] == "hello bob"

    def test_receive_empty(self):
        result = mcp_server.message_receive("nobody_inbox_" + str(id(self)))
        assert result["has_message"] is False


class TestCollisionLog:
    def test_collision_log(self, tmp_path):
        old_log = mcp_server._tools.log_file
        mcp_server._tools.log_file = str(tmp_path / "collisions.log")
        try:
            result = mcp_server.collision_log("TestAgent", "#observe", "collision", "test context")
            assert result["logged"] is True
            assert "COLLISION" in result["entry"]
        finally:
            mcp_server._tools.log_file = old_log


class TestMCPRegistration:
    def test_tools_registered(self):
        """Verify all tools are registered with the FastMCP server."""
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        expected = [
            "dispatch", "vocabulary_lookup", "vocabulary_list",
            "vocabulary_save", "receivers_list", "message_send",
            "message_receive", "collision_log",
        ]
        for name in expected:
            assert name in tool_names, f"Tool {name} not registered"
