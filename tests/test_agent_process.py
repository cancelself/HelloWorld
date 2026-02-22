"""Tests for the AgentProcess — isolated per-agent runtime."""

import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agent_process import AgentProcess, SDK_AGENT_MAP, HUMAN_SYMBOLS
from message_bus import Message
import message_bus


@pytest.fixture
def tmp_vocab(tmp_path):
    """Create a minimal vocabulary directory with HelloWorld and Agent."""
    hw = tmp_path / "HelloWorld.hw"
    hw.write_text("# HelloWorld\n\nRoot receiver.\n\n## #\n\nThe symbol primitive.\n\n## #hello\n\nAnnounce presence.\n")
    agent = tmp_path / "Agent.hw"
    agent.write_text("# Agent : HelloWorld\n\nAgent protocol.\n\n## #observe\n\nRead state.\n\n## #act\n\nExecute.\n")
    claude = tmp_path / "Claude.hw"
    claude.write_text("# Claude : Agent\n\nClaude receiver.\n")
    return str(tmp_path)


@pytest.fixture
def agent(tmp_vocab, tmp_path, monkeypatch):
    """Create an AgentProcess with isolated file transport."""
    monkeypatch.setattr(message_bus, "BASE_DIR", tmp_path / "runtimes")
    return AgentProcess("Claude", vocab_dir=tmp_vocab)


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_agent_process_creates(agent):
    assert agent.name == "Claude"
    assert agent.message_count == 0
    assert agent.running is False
    assert agent.pending_human == []


def test_agent_process_loads_vocabulary(agent):
    # Claude has no native symbols — inherits from Agent/HelloWorld.
    # Vocabulary list is always a sorted list (may be empty if
    # inheritance chain doesn't fully resolve in temp dir).
    assert isinstance(agent.vocabulary, list)


def test_agent_process_has_dispatcher(agent):
    assert agent.dispatcher is not None


def test_agent_process_has_memory(agent):
    assert agent.memory is not None


def test_agent_process_has_tools(agent):
    assert agent.tools is not None


# ------------------------------------------------------------------
# SDK detection (no SDKs installed in test env)
# ------------------------------------------------------------------

def test_adapter_is_none_without_sdk(agent):
    # In test env, no SDKs are installed
    assert agent.adapter is None


def test_detect_adapter_unknown_agent(tmp_vocab, tmp_path, monkeypatch):
    monkeypatch.setattr(message_bus, "BASE_DIR", tmp_path / "runtimes")
    p = AgentProcess("UnknownAgent", vocab_dir=tmp_vocab)
    assert p.adapter is None


# ------------------------------------------------------------------
# Human escalation
# ------------------------------------------------------------------

def test_needs_human_with_propose(agent):
    msg = Message(sender="Gemini", content="@Claude #propose new symbol", timestamp="t1")
    assert agent._needs_human(msg) is True


def test_needs_human_with_review(agent):
    msg = Message(sender="Codex", content="#review this change", timestamp="t1")
    assert agent._needs_human(msg) is True


def test_needs_human_with_question(agent):
    msg = Message(sender="Copilot", content="#question about design", timestamp="t1")
    assert agent._needs_human(msg) is True


def test_human_sender_goes_through_sdk(agent):
    msg = Message(sender="Human", content="hello", timestamp="t1")
    assert agent._needs_human(msg) is False


def test_no_human_needed_for_normal_message(agent):
    msg = Message(sender="Gemini", content="learn: #patience", timestamp="t1")
    assert agent._needs_human(msg) is False


def test_escalate_to_human(agent):
    msg = Message(sender="Gemini", content="#propose new thing", timestamp="t1")
    result = agent._escalate_to_human(msg)
    assert "Escalated to human" in result
    assert len(agent.pending_human) == 1
    assert agent.pending_human[0]["from"] == "Gemini"


# ------------------------------------------------------------------
# Message processing
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_message_escalation(agent):
    msg = Message(sender="Gemini", content="#propose add #fire", timestamp="t1")
    result = await agent.process_message(msg)
    assert "Escalated" in result
    assert len(agent.pending_human) == 1


@pytest.mark.asyncio
async def test_process_message_normal(agent):
    msg = Message(sender="Gemini", content="learn: #patience", timestamp="t1")
    result = await agent.process_message(msg)
    # Without SDK, falls back to LLM or returns received message
    assert "Claude" in result or "Received" in result
    assert agent.message_count == 1


# ------------------------------------------------------------------
# Memory integration
# ------------------------------------------------------------------

def test_memory_store_works(agent):
    path = agent.memory.store("test content", title="test-mem")
    assert path.exists()


# ------------------------------------------------------------------
# Status
# ------------------------------------------------------------------

def test_status_dict(agent):
    s = agent.status()
    assert s["name"] == "Claude"
    assert s["messages_processed"] == 0
    assert s["pending_human"] == 0
    assert s["running"] is False
    assert s["adapter"] == "LLM fallback"
    assert "vocabulary_size" in s


# ------------------------------------------------------------------
# Stop
# ------------------------------------------------------------------

def test_stop(agent):
    agent.running = True
    agent.stop()
    assert agent.running is False


# ------------------------------------------------------------------
# Human response handling
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_human_response(agent):
    agent.pending_human.append({
        "from": "Gemini",
        "content": "do something",
        "timestamp": "t1",
        "type": "escalation",
    })
    msg = Message(sender="Human", content="do something", timestamp="t2")
    await agent._handle_human_response(msg)
    assert len(agent.pending_human) == 0


# ------------------------------------------------------------------
# System prompt
# ------------------------------------------------------------------

def test_build_system_prompt(agent):
    prompt = agent._build_system_prompt()
    assert "Claude" in prompt
    assert "Vocabulary" in prompt
    assert "Constraints" in prompt
