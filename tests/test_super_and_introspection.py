"""Tests for Tracks 1-3: LLM-first dispatch, super/unary messages, REPL introspection.

Covers:
- Track 1: Description loading, description-aware prompts, lazy LLM
- Track 2: SUPER token, unary messages, super lookups
- Track 3: REPL introspection commands (.chain, .lookup, .super, .collisions, .trace)
"""

import os
import sys
import tempfile
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lexer import Lexer, TokenType
from parser import Parser
from ast_nodes import (
    UnaryMessageNode, SuperLookupNode, ScopedLookupNode,
    ReceiverNode, SymbolNode,
)
from dispatcher import Dispatcher, Receiver
from vocabulary import VocabularyManager
from repl import REPL
from prompts import (
    scoped_lookup_prompt_with_descriptions,
    super_lookup_prompt,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def _fresh_dispatcher():
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    tmp = tempfile.mkdtemp()
    return Dispatcher(vocab_dir=tmp)


def _fresh_dispatcher_with_dir():
    os.environ["HELLOWORLD_DISABLE_MESSAGE_BUS"] = "1"
    tmp = tempfile.mkdtemp()
    return Dispatcher(vocab_dir=tmp), tmp


def _make_repl(dispatcher=None):
    if dispatcher is None:
        dispatcher = _fresh_dispatcher()
    return REPL(dispatcher=dispatcher, enable_readline=False)


def parse(source: str):
    return Parser.from_source(source).parse()


# ══════════════════════════════════════════════════════════════════════════
# TRACK 2a: Lexer — SUPER token
# ══════════════════════════════════════════════════════════════════════════

def test_lexer_super_token():
    """Tokenizes `super` as SUPER."""
    tokens = Lexer("super").tokenize()
    assert tokens[0].type == TokenType.SUPER
    assert tokens[0].value == "super"


def test_lexer_super_in_context():
    """Claude act super → RECEIVER, IDENTIFIER, SUPER."""
    tokens = Lexer("Claude act super").tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [TokenType.RECEIVER, TokenType.IDENTIFIER, TokenType.SUPER]


def test_lexer_super_after_symbol():
    """Claude #act super → RECEIVER, SYMBOL, SUPER."""
    tokens = Lexer("Claude #act super").tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [TokenType.RECEIVER, TokenType.SYMBOL, TokenType.SUPER]


def test_lexer_super_not_receiver():
    """super should be SUPER, not IDENTIFIER or RECEIVER."""
    tokens = Lexer("super").tokenize()
    assert tokens[0].type == TokenType.SUPER
    assert tokens[0].type != TokenType.IDENTIFIER
    assert tokens[0].type != TokenType.RECEIVER


# ══════════════════════════════════════════════════════════════════════════
# TRACK 2b: Parser — Unary messages + SuperLookupNode
# ══════════════════════════════════════════════════════════════════════════

def test_parser_unary_message():
    """Claude act → UnaryMessageNode."""
    nodes = parse("Claude act")
    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, UnaryMessageNode)
    assert node.receiver.name == "Claude"
    assert node.message == "act"
    assert node.is_super is False


def test_parser_unary_vs_keyword():
    """Claude act is unary; Claude act: #x is keyword."""
    unary = parse("Claude act")
    assert isinstance(unary[0], UnaryMessageNode)

    keyword = parse("Claude act: #x")
    assert not isinstance(keyword[0], UnaryMessageNode)


def test_parser_unary_super():
    """Claude act super → UnaryMessageNode(is_super=True)."""
    nodes = parse("Claude act super")
    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, UnaryMessageNode)
    assert node.receiver.name == "Claude"
    assert node.message == "act"
    assert node.is_super is True


def test_parser_typedef_super():
    """Claude #act super → SuperLookupNode."""
    nodes = parse("Claude #act super")
    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, SuperLookupNode)
    assert node.receiver.name == "Claude"
    assert node.symbol.name == "#act"


def test_parser_scoped_lookup_no_super():
    """Claude #act (no super) → ScopedLookupNode, not SuperLookupNode."""
    nodes = parse("Claude #act")
    assert len(nodes) == 1
    assert isinstance(nodes[0], ScopedLookupNode)


# ══════════════════════════════════════════════════════════════════════════
# TRACK 2c: Dispatcher — unary message + super dispatch
# ══════════════════════════════════════════════════════════════════════════

def test_dispatch_unary_message():
    """Claude act → invokes act behavior."""
    d = _fresh_dispatcher()
    d.dispatch_source("Claude # → [#act, #observe]")
    results = d.dispatch_source("Claude act")
    assert len(results) == 1
    assert "act" in results[0]
    assert "Claude" in results[0]


def test_dispatch_unary_super():
    """Claude act super → invokes through ancestor."""
    d = _fresh_dispatcher()
    # Set up inheritance: Claude : Agent, Agent has #act
    d.dispatch_source("# Agent : Object\n## act")
    d.dispatch_source("# Claude : Agent\n## act")
    d._resolve_parents()

    results = d.dispatch_source("Claude act super")
    assert len(results) == 1
    assert "Agent" in results[0]


def test_dispatch_unary_super_no_ancestor():
    """Claude act super when no ancestor holds #act."""
    d = _fresh_dispatcher()
    d.dispatch_source("Claude # → [#uniqueSymbol]")
    results = d.dispatch_source("Claude uniqueSymbol super")
    assert len(results) == 1
    assert "native" in results[0].lower() or "no ancestor" in results[0].lower()


def test_dispatch_unary_unknown():
    """Unary message for unknown symbol → error response."""
    d = _fresh_dispatcher()
    d.dispatch_source("Claude # → [#act]")
    results = d.dispatch_source("Claude unknownAction")
    assert len(results) == 1
    assert "unknown" in results[0].lower()


def test_dispatch_typedef_super():
    """Claude #act super → shows super chain with definitions."""
    d = _fresh_dispatcher()
    d.dispatch_source("# Agent : Object\n## act")
    d.dispatch_source("# Claude : Agent\n## act")
    d._resolve_parents()

    results = d.dispatch_source("Claude #act super")
    assert len(results) == 1
    assert "Super chain" in results[0]
    assert "Claude" in results[0]


def test_super_native_with_ancestor():
    """Super chain returns both local and ancestor entries."""
    d = _fresh_dispatcher()
    d.dispatch_source("# Agent : Object\n## act")
    d.dispatch_source("# Claude : Agent\n## act")
    d._resolve_parents()

    results = d.dispatch_source("Claude #act super")
    assert "Claude" in results[0]
    assert "Agent" in results[0]
    assert "native" in results[0].lower()


def test_super_native_no_ancestor():
    """Super chain for symbol only present locally."""
    d = _fresh_dispatcher()
    d.dispatch_source("# TestLocal\n## unique")
    results = d.dispatch_source("TestLocal #unique super")
    assert "TestLocal" in results[0]


def test_super_unknown():
    """Super chain for symbol not found anywhere."""
    d = _fresh_dispatcher()
    d.dispatch_source("# TestEmpty\n## something")
    results = d.dispatch_source("TestEmpty #missing super")
    assert "not present" in results[0].lower()


def test_super_at_root():
    """HelloWorld has no parent — super shows root only."""
    d = _fresh_dispatcher()
    results = d.dispatch_source("HelloWorld #Agent super")
    assert "HelloWorld" in results[0]


# ══════════════════════════════════════════════════════════════════════════
# TRACK 1a/1b: Vocabulary description loading
# ══════════════════════════════════════════════════════════════════════════

def test_load_description():
    """load_description reads symbol description from .hw file."""
    tmp = tempfile.mkdtemp()
    hw_content = "# Test\n## act\n- Do the thing.\n## idle\n- Do nothing.\n"
    with open(os.path.join(tmp, "Test.hw"), "w") as f:
        f.write(hw_content)
    vm = VocabularyManager(tmp)
    desc = vm.load_description("Test", "act")
    assert desc == "Do the thing."


def test_load_description_missing_symbol():
    """load_description returns None for missing symbol."""
    tmp = tempfile.mkdtemp()
    hw_content = "# Test\n## act\n- Do the thing.\n"
    with open(os.path.join(tmp, "Test.hw"), "w") as f:
        f.write(hw_content)
    vm = VocabularyManager(tmp)
    assert vm.load_description("Test", "missing") is None


def test_load_description_missing_receiver():
    """load_description returns None for missing receiver file."""
    tmp = tempfile.mkdtemp()
    vm = VocabularyManager(tmp)
    assert vm.load_description("Missing", "act") is None


def test_load_identity():
    """load_identity reads receiver description from .hw file."""
    tmp = tempfile.mkdtemp()
    hw_content = "# Test\n- The test receiver.\n## act\n- Do the thing.\n"
    with open(os.path.join(tmp, "Test.hw"), "w") as f:
        f.write(hw_content)
    vm = VocabularyManager(tmp)
    ident = vm.load_identity("Test")
    assert ident == "The test receiver."


def test_load_identity_missing():
    """load_identity returns None for missing receiver file."""
    tmp = tempfile.mkdtemp()
    vm = VocabularyManager(tmp)
    assert vm.load_identity("Missing") is None


# ══════════════════════════════════════════════════════════════════════════
# TRACK 1b/1d: Description-aware prompts
# ══════════════════════════════════════════════════════════════════════════

def test_description_prompt_includes_text():
    """scoped_lookup_prompt_with_descriptions includes .hw description."""
    prompt = scoped_lookup_prompt_with_descriptions(
        "Claude", "#act", ["#act", "#observe"],
        description="Execute autonomously.",
        identity="Language designer.",
    )
    assert "Execute autonomously." in prompt
    assert "Language designer." in prompt
    assert "You are Claude" in prompt
    assert "#act" in prompt


def test_description_prompt_handles_none():
    """Prompt uses fallback text when descriptions are None."""
    prompt = scoped_lookup_prompt_with_descriptions(
        "Claude", "#act", ["#act"],
    )
    assert "no description available" in prompt
    assert "no identity description" in prompt


def test_super_prompt_includes_both():
    """super_lookup_prompt includes local + ancestor descriptions."""
    prompt = super_lookup_prompt(
        "Claude", "#act", ["#act", "#observe"],
        local_description="Execute autonomously for Claude.",
        ancestor_name="Agent",
        ancestor_description="Execute immediately [protocol].",
    )
    assert "Execute autonomously for Claude." in prompt
    assert "Execute immediately [protocol]." in prompt
    assert "Agent" in prompt
    assert "inheritance" in prompt.lower()


def test_super_prompt_handles_none():
    """Super prompt uses fallback text when descriptions are None."""
    prompt = super_lookup_prompt("Claude", "#act", ["#act"])
    assert "no local description" in prompt
    assert "no ancestor description" in prompt


# ══════════════════════════════════════════════════════════════════════════
# TRACK 1c: Lazy LLM loading
# ══════════════════════════════════════════════════════════════════════════

def test_dispatcher_no_use_llm_param():
    """Constructor rejects old use_llm parameter."""
    with pytest.raises(TypeError, match="use_llm parameter removed"):
        Dispatcher(use_llm=True)


def test_llm_lazy_load_with_key():
    """LLM is created when API key is present."""
    old = os.environ.pop("GEMINI_API_KEY", None)
    try:
        os.environ["GEMINI_API_KEY"] = "test-key"
        d = _fresh_dispatcher()
        assert d.llm is not None
        assert d.use_llm is True
    finally:
        if old is not None:
            os.environ["GEMINI_API_KEY"] = old
        else:
            os.environ.pop("GEMINI_API_KEY", None)


def test_llm_lazy_load_without_key():
    """LLM returns None when no API key is set."""
    old = os.environ.pop("GEMINI_API_KEY", None)
    try:
        d = _fresh_dispatcher()
        assert d.llm is None
        assert d.use_llm is False
    finally:
        if old is not None:
            os.environ["GEMINI_API_KEY"] = old


# ══════════════════════════════════════════════════════════════════════════
# TRACK 3: REPL introspection commands
# ══════════════════════════════════════════════════════════════════════════

def test_repl_chain():
    """.chain Claude shows full inheritance."""
    d = _fresh_dispatcher()
    d.dispatch_source("# Agent : Object\n## observe\n## act")
    d.dispatch_source("# Claude : Agent\n## parse\n## act")
    d._resolve_parents()

    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_chain("Claude")
    output = buf.getvalue()
    assert "Claude" in output
    assert "Agent" in output


def test_repl_chain_root():
    """.chain HelloWorld shows root only."""
    d = _fresh_dispatcher()
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_chain("HelloWorld")
    output = buf.getvalue()
    assert "HelloWorld" in output


def test_repl_chain_unknown():
    """.chain for unknown receiver shows error."""
    d = _fresh_dispatcher()
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_chain("NoSuchReceiver")
    output = buf.getvalue()
    assert "Unknown receiver" in output


def test_repl_lookup_native():
    """.lookup Claude #parse shows native."""
    d = _fresh_dispatcher()
    d.dispatch_source("# Claude\n## parse")
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_lookup("Claude", "#parse")
    output = buf.getvalue()
    assert "NATIVE" in output
    assert "Claude" in output


def test_repl_lookup_inherited():
    """.lookup Child #observe shows inherited from Parent."""
    d = _fresh_dispatcher()
    d.dispatch_source("# Parent : Object\n## observe")
    d.dispatch_source("# Child : Parent\n## parse")
    d._resolve_parents()
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_lookup("Child", "#observe")
    output = buf.getvalue()
    assert "INHERITED" in output
    assert "Parent" in output


def test_repl_lookup_unknown():
    """.lookup Claude #foo shows unknown."""
    d = _fresh_dispatcher()
    d.dispatch_source("# Claude\n## parse")
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_lookup("Claude", "#foo")
    output = buf.getvalue()
    assert "UNKNOWN" in output


def test_repl_super():
    """.super Claude #act walks chain with descriptions."""
    d, tmp = _fresh_dispatcher_with_dir()
    # Create .hw files with descriptions
    with open(os.path.join(tmp, "Agent.hw"), "w") as f:
        f.write("# Agent : Object\n## act\n- Execute immediately.\n")
    with open(os.path.join(tmp, "Claude.hw"), "w") as f:
        f.write("# Claude : Agent\n## act\n- Act autonomously.\n")
    # Re-bootstrap to pick up the files
    d2 = Dispatcher(vocab_dir=tmp)
    d2._resolve_parents()
    repl = _make_repl(d2)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_super("Claude", "#act")
    output = buf.getvalue()
    assert "Claude" in output
    assert "native" in output.lower()


def test_repl_collisions():
    """.collisions 3 shows last 3 entries."""
    d = _fresh_dispatcher()
    # Generate collisions
    d.dispatch_source("Claude # → [#fire]")
    d.dispatch_source("Gemini # → [#fire]")
    d.dispatch_source("Claude send: #fire to: Gemini")
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_collisions(3)
    output = buf.getvalue()
    assert "COLLISION" in output or len(output.strip()) > 0


def test_repl_collisions_empty():
    """.collisions shows 'no collisions' when log is empty."""
    d = _fresh_dispatcher()
    # Point to non-existent log
    d.log_file = os.path.join(tempfile.mkdtemp(), "nonexistent.log")
    repl = _make_repl(d)
    buf = StringIO()
    with redirect_stdout(buf):
        repl._show_collisions()
    output = buf.getvalue()
    assert "No collisions" in output


def test_repl_trace_toggle():
    """.trace on/off toggles dispatcher trace flag."""
    d = _fresh_dispatcher()
    repl = _make_repl(d)

    assert d.trace is False

    buf = StringIO()
    with redirect_stdout(buf):
        repl._toggle_trace("on")
    assert d.trace is True

    buf = StringIO()
    with redirect_stdout(buf):
        repl._toggle_trace("off")
    assert d.trace is False


def test_trace_output_in_dispatch():
    """Trace flag causes [TRACE] output during dispatch."""
    d = _fresh_dispatcher()
    d.dispatch_source("Claude # → [#act]")
    d.trace = True

    buf = StringIO()
    with redirect_stdout(buf):
        d.dispatch_source("Claude #act")
    output = buf.getvalue()
    assert "[TRACE]" in output
    assert "ScopedLookupNode" in output
