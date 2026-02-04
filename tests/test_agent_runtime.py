"""Tests for AgentRuntime — .hw loading, system prompt construction, agent definitions."""

import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from agent_runtime import AgentRuntime, ReceiverAgent, AGENT_RECEIVERS


# Use the real vocabularies/ directory for loading tests
VOCAB_DIR = str(Path(__file__).resolve().parent.parent / "vocabularies")


class TestAgentLoading:
    def test_loads_all_agent_receivers(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        for name in AGENT_RECEIVERS:
            assert name in runtime.agents, f"{name} should be loaded"

    def test_agent_has_vocabulary_or_identity(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        for name, agent in runtime.agents.items():
            has_symbols = len(agent.vocabulary) > 0
            has_identity = agent.identity is not None
            assert has_symbols or has_identity, f"{name} should have symbols or identity"

    def test_agent_has_identity(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        # All .hw files in the repo have identity descriptions
        for name, agent in runtime.agents.items():
            assert agent.identity is not None, f"{name} should have an identity"

    def test_agent_is_receiver_agent(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        for agent in runtime.agents.values():
            assert isinstance(agent, ReceiverAgent)


class TestSystemPromptConstruction:
    def setup_method(self):
        self.runtime = AgentRuntime(vocab_dir=VOCAB_DIR)

    def test_prompt_contains_name(self):
        agent = self.runtime.agents["Claude"]
        assert "You are Claude" in agent.system_prompt

    def test_prompt_contains_identity(self):
        agent = self.runtime.agents["Claude"]
        # Claude.hw has identity: "Language designer, spec author..."
        assert agent.identity in agent.system_prompt

    def test_prompt_contains_vocabulary_section(self):
        agent = self.runtime.agents["Copilot"]
        assert "## Vocabulary" in agent.system_prompt
        # Should list symbol count
        assert f"{len(agent.vocabulary)} symbols" in agent.system_prompt

    def test_prompt_contains_symbols(self):
        agent = self.runtime.agents["Codex"]
        for sym in agent.vocabulary:
            assert sym in agent.system_prompt

    def test_prompt_contains_descriptions(self):
        agent = self.runtime.agents["Gemini"]
        # Gemini.hw has descriptions for its symbols
        for sym, desc in agent.symbol_descriptions.items():
            if desc:
                assert desc in agent.system_prompt

    def test_prompt_contains_design_principles(self):
        agent = self.runtime.agents["Claude"]
        assert "Identity is vocabulary" in agent.system_prompt
        assert "Constraint is character" in agent.system_prompt

    def test_prompt_contains_constraints(self):
        agent = self.runtime.agents["Copilot"]
        assert "Stay within your vocabulary" in agent.system_prompt


class TestAgentDefinitions:
    def test_definitions_dict_has_all_agents(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        defs = runtime.create_agent_definitions()
        for name in AGENT_RECEIVERS:
            assert name in defs

    def test_definition_has_required_fields(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        defs = runtime.create_agent_definitions()
        for name, defn in defs.items():
            assert "name" in defn
            assert "system_prompt" in defn
            assert "vocabulary" in defn
            assert "identity" in defn
            assert defn["name"] == name

    def test_definition_system_prompt_matches_agent(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        defs = runtime.create_agent_definitions()
        for name, defn in defs.items():
            assert defn["system_prompt"] == runtime.agents[name].system_prompt


class TestEmptyVocabDir:
    def test_empty_dir_loads_no_agents(self):
        tmpdir = tempfile.mkdtemp()
        try:
            runtime = AgentRuntime(vocab_dir=tmpdir)
            assert len(runtime.agents) == 0
        finally:
            shutil.rmtree(tmpdir)


class TestInterpretWithoutKey:
    @pytest.mark.asyncio
    async def test_interpret_unknown_receiver(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        result = await runtime.interpret("Unknown", "hello")
        assert "Unknown receiver" in result

    @pytest.mark.asyncio
    async def test_interpret_no_key_mock_mode(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        result = await runtime.interpret("Claude", "What is #parse?")
        assert "Claude" in result
        assert "no API key" in result


class TestAutonomousModeRequiresSDK:
    @pytest.mark.asyncio
    async def test_autonomous_raises_without_sdk(self):
        runtime = AgentRuntime(vocab_dir=VOCAB_DIR)
        with pytest.raises(ImportError, match="claude-agent-sdk"):
            await runtime.run_autonomous()
