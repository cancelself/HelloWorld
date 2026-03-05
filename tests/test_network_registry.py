"""Tests for the NetworkRegistry — @HelloWorld's global dictionary."""

import tempfile
import os
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from network_registry import NetworkRegistry


@pytest.fixture
def registry(tmp_path):
    db_path = str(tmp_path / "test.db")
    return NetworkRegistry(db_path=db_path)


class TestHelloGoodbye:
    def test_hello_registers_agent(self, registry):
        result = registry.hello("claude@purdy.im", symbol_count=12)
        assert result["status"] == "online"
        assert result["agent"] == "claude@purdy.im"

    def test_hello_appears_in_status(self, registry):
        registry.hello("claude@purdy.im", symbol_count=12)
        status = registry.status()
        assert status["online"] == 1
        assert status["total"] == 1
        assert status["agents"][0]["address"] == "claude@purdy.im"
        assert status["agents"][0]["name"] == "claude"
        assert status["agents"][0]["context"] == "purdy.im"
        assert status["agents"][0]["symbols"] == 12

    def test_goodbye_marks_offline(self, registry):
        registry.hello("claude@purdy.im")
        registry.goodbye("claude@purdy.im")
        status = registry.status()
        assert status["online"] == 0
        assert status["total"] == 1
        assert status["agents"][0]["status"] == "offline"

    def test_hello_after_goodbye_comes_back(self, registry):
        registry.hello("claude@purdy.im")
        registry.goodbye("claude@purdy.im")
        registry.hello("claude@purdy.im", symbol_count=15)
        status = registry.status()
        assert status["online"] == 1
        assert status["agents"][0]["status"] == "online"
        assert status["agents"][0]["symbols"] == 15

    def test_multiple_agents(self, registry):
        registry.hello("claude@purdy.im", symbol_count=12)
        registry.hello("claude-code@cancelself.gmail.com", symbol_count=8)
        registry.hello("copilot@github.com", symbol_count=10)
        status = registry.status()
        assert status["online"] == 3
        assert status["total"] == 3

    def test_plain_receiver_no_context(self, registry):
        registry.hello("HelloWorld")
        agent = registry.agent_status("helloworld")
        assert agent["name"] == "HelloWorld"
        assert agent["context"] is None


class TestAgentStatus:
    def test_lookup_existing(self, registry):
        registry.hello("claude@purdy.im", symbol_count=12)
        agent = registry.agent_status("claude@purdy.im")
        assert agent is not None
        assert agent["symbols"] == 12

    def test_lookup_missing(self, registry):
        assert registry.agent_status("nobody@nowhere.com") is None

    def test_case_insensitive(self, registry):
        registry.hello("Claude@Purdy.im")
        agent = registry.agent_status("claude@purdy.im")
        assert agent is not None


class TestEvents:
    def test_hello_logged(self, registry):
        registry.hello("claude@purdy.im")
        events = registry.recent_events()
        assert len(events) == 1
        assert events[0]["event"] == "hello"
        assert events[0]["agent"] == "claude@purdy.im"

    def test_goodbye_logged(self, registry):
        registry.hello("claude@purdy.im")
        registry.goodbye("claude@purdy.im")
        events = registry.recent_events()
        assert len(events) == 2
        assert events[0]["event"] == "goodbye"

    def test_event_limit(self, registry):
        for i in range(30):
            registry.hello(f"agent{i}@test.com")
        events = registry.recent_events(limit=5)
        assert len(events) == 5


class TestUpdateSymbols:
    def test_update_count(self, registry):
        registry.hello("claude@purdy.im", symbol_count=10)
        registry.update_symbols("claude@purdy.im", 15)
        agent = registry.agent_status("claude@purdy.im")
        assert agent["symbols"] == 15
