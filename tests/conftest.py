"""Shared test helpers that load symbols from .hw files at test time.

.hw files are the namespace authority. Tests should test mechanism
(lookup, inheritance, collision, learning), not specific symbol content.
"""

import sys
import tempfile
from pathlib import Path
from typing import Set

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vocabulary import VocabularyManager
from dispatcher import Dispatcher
import message_bus


# --- Vocabulary helpers ---

_VOCAB_DIR = str(Path(__file__).parent.parent / 'vocabularies')
_vm = VocabularyManager(_VOCAB_DIR)


def hw_symbols(receiver_name: str) -> Set[str]:
    """Load the symbol set for a receiver from its .hw file.

    This is the same code path the runtime uses at bootstrap.
    Returns an empty set if the .hw file doesn't exist.
    """
    symbols = _vm.load(receiver_name)
    return symbols if symbols else set()


def any_native_symbol(receiver_name: str) -> str:
    """Return one deterministic symbol native to the receiver.

    Picks the first in sorted order for reproducibility.
    """
    symbols = hw_symbols(receiver_name)
    assert symbols, f"{receiver_name}.hw has no symbols"
    return sorted(symbols)[0]


def shared_native_symbol(receiver_a: str, receiver_b: str) -> str:
    """Return a symbol native to both receivers.

    Useful for collision tests — both receivers hold it.
    """
    common = hw_symbols(receiver_a) & hw_symbols(receiver_b)
    assert common, f"No shared native symbols between {receiver_a} and {receiver_b}"
    return sorted(common)[0]


def exclusive_native_symbol(has_it: str, lacks_it: str) -> str:
    """Return a symbol native to has_it but NOT in lacks_it.

    Useful for foreign/unknown tests.
    """
    exclusive = hw_symbols(has_it) - hw_symbols(lacks_it)
    assert exclusive, f"No exclusive symbols: {has_it} vs {lacks_it}"
    return sorted(exclusive)[0]


# --- Fixtures ---

@pytest.fixture(autouse=True)
def _no_llm_keys(monkeypatch):
    """Strip LLM/SDK API keys from the environment during tests.

    Existing tests verify structural dispatch behavior (native/inherited/unknown).
    LLM keys in the environment would activate the interpretive path and break
    assertions on structural output. Tests that need a real or mock LLM should
    set the key explicitly or inject a mock via dispatcher.llm.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_COPILOT_TOKEN", raising=False)
    monkeypatch.delenv("HW_TRANSPORT", raising=False)
    monkeypatch.delenv("CLWNT_TOKEN", raising=False)


@pytest.fixture
def fresh_dispatcher():
    """Create a dispatcher with a temp vocab dir so tests start clean.

    Replaces the duplicated _fresh_dispatcher() helpers across test files.
    """
    tmp = tempfile.mkdtemp()
    message_bus.BASE_DIR = Path(tmp)
    message_bus.reset_transport()
    return Dispatcher(vocab_dir=tmp)


@pytest.fixture
def fresh_dispatcher_with_dir():
    """Create a dispatcher with a temp vocab dir, returning (dispatcher, tmpdir).

    For tests that need to inspect persisted files.
    """
    tmp = tempfile.mkdtemp()
    message_bus.BASE_DIR = Path(tmp)
    message_bus.reset_transport()
    return Dispatcher(vocab_dir=tmp), tmp
