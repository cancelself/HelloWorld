"""Tests for AgentRuntime SDK features — orchestrator prompt, SDK options, query()."""

import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from agent_runtime import AgentRuntime, AGENT_RECEIVERS


VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestOrchestratorPrompt:
    def setup_method(self):
        self.runtime = AgentRuntime(vocab_dir=VOCAB_DIR)

    def test_contains_helloworld_section(self):
        prompt = self.runtime.build_orchestrator_prompt()
        assert "## HelloWorld" in prompt
        assert "#send" in prompt
        assert "#receive" in prompt

    def test_contains_object_section(self):
        prompt = self.runtime.build_orchestrator_prompt()
        assert "## Object" in prompt

    def test_contains_agent_section(self):
        prompt = self.runtime.build_orchestrator_prompt()
        assert "## Agent" in prompt
        assert "#observe" in prompt
        assert "#unknown" in prompt

    def test_contains_receiver_summary(self):
        prompt = self.runtime.build_orchestrator_prompt()
        assert "## Loaded Receivers" in prompt
        for name in AGENT_RECEIVERS:
            assert name in prompt

    def test_contains_behavior_section(self):
        prompt = self.runtime.build_orchestrator_prompt()
        assert "## Behavior" in prompt
        assert "vocabulary_lookup" in prompt

    def test_contains_design_principles(self):
        prompt = self.runtime.build_orchestrator_prompt()
        assert "Identity is vocabulary" in prompt


class TestHwReaderIntegration:
    """Verify hw_reader produces same results as old VocabularyManager."""

    def setup_method(self):
        self.runtime = AgentRuntime(vocab_dir=VOCAB_DIR)

    def test_agent_vocabulary_matches_hw_file(self):
        """Agent vocabulary should match what hw_reader extracts from the .hw file."""
        from hw_reader import read_hw_file
        import os

        for name in AGENT_RECEIVERS:
            agent = self.runtime.agents[name]
            receiver = read_hw_file(os.path.join(VOCAB_DIR, f"{name}.hw"))
            assert receiver is not None
            assert agent.vocabulary == receiver.vocabulary

    def test_agent_identity_matches_hw_file(self):
        from hw_reader import read_hw_file
        import os

        for name in AGENT_RECEIVERS:
            agent = self.runtime.agents[name]
            receiver = read_hw_file(os.path.join(VOCAB_DIR, f"{name}.hw"))
            assert receiver is not None
            assert agent.identity == receiver.identity


class TestSdkOptions:
    def test_create_sdk_options_raises_without_sdk(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        with pytest.raises(ImportError, match="claude-agent-sdk"):
            runtime.create_sdk_options()


class TestQueryRequiresSDK:
    @pytest.mark.asyncio
    async def test_query_raises_without_sdk(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        with pytest.raises(ImportError, match="claude-agent-sdk"):
            await runtime.query("Claude #parse")


class TestToolsIntegration:
    def test_runtime_has_tools(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        assert runtime.tools is not None
        assert len(runtime.tools.all_tools()) == 7

    def test_tools_use_same_vocab_dir(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        assert runtime.tools.vocab_dir == VOCAB_DIR
