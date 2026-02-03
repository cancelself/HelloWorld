"""Tests for message_handlers module."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from message_handlers import MessageHandler, MessageHandlerRegistry
from ast_nodes import MessageNode, ReceiverNode, SymbolNode, LiteralNode
from conftest import hw_symbols, any_native_symbol


def test_message_handler_pattern_matching():
    """Test that handlers match correct patterns."""
    handler = MessageHandler(
        "greet:withFeeling:",
        lambda args, recv: f"Hello with {args['withFeeling']}"
    )

    # Should match
    message1 = MessageNode(
        receiver=ReceiverNode("Awakener"),
        arguments={"greet": SymbolNode("#stillness"), "withFeeling": LiteralNode("joy")}
    )
    assert handler.matches(message1)

    # Should not match (different pattern)
    message2 = MessageNode(
        receiver=ReceiverNode("Awakener"),
        arguments={"greet": SymbolNode("#stillness")}
    )
    assert not handler.matches(message2)


def test_message_handler_execution():
    """Test that handlers execute with correct arguments."""
    handler = MessageHandler(
        "greet:",
        lambda args, recv: f"Hello {args['greet']}"
    )

    message = MessageNode(
        receiver=ReceiverNode("Awakener"),
        arguments={"greet": SymbolNode("#stillness")}
    )

    result = handler.handle(message)
    assert result == "Hello #stillness"


def test_message_handler_registry():
    """Test registry registration and lookup."""
    registry = MessageHandlerRegistry()

    # Register custom handler
    registry.register(
        "Test",
        "customAction:",
        lambda args, recv: f"Custom: {args['customAction']}"
    )

    # Test custom handler
    message = MessageNode(
        receiver=ReceiverNode("Test"),
        arguments={"customAction": SymbolNode("#fire")}
    )

    result = registry.handle("Test", message)
    assert result == "Custom: #fire"


def test_default_handlers_greet():
    """Test built-in greet: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Copilot"),
        arguments={"greet": SymbolNode("#parse")}
    )

    result = registry.handle("Copilot", message)
    assert "greets with #parse" in result


def test_default_handlers_ask_about():
    """Test built-in ask:about: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Claude"),
        arguments={
            "ask": SymbolNode("#parse"),
            "about": SymbolNode("#dispatch")
        }
    )

    result = registry.handle("Claude", message)
    assert "Claude considers #dispatch" in result


def test_default_handlers_learn():
    """Test built-in learn: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Codex"),
        arguments={"learn": SymbolNode("#Sunyata")}
    )

    result = registry.handle("Codex", message)
    assert "Codex learns #Sunyata" in result


def test_handler_returns_none_for_no_match():
    """Test that registry returns None when no handler matches."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Unknown"),
        arguments={"unknownAction": SymbolNode("#test")}
    )

    result = registry.handle("Unknown", message)
    assert result is None


def test_multiple_handlers_per_receiver():
    """Test that multiple handlers can be registered for same receiver."""
    registry = MessageHandlerRegistry()

    # Register two handlers for same receiver
    registry.register("Test", "action1:", lambda args, recv: "Action 1")
    registry.register("Test", "action2:", lambda args, recv: "Action 2")

    message1 = MessageNode(
        receiver=ReceiverNode("Test"),
        arguments={"action1": SymbolNode("#test")}
    )
    message2 = MessageNode(
        receiver=ReceiverNode("Test"),
        arguments={"action2": SymbolNode("#test")}
    )

    assert registry.handle("Test", message1) == "Action 1"
    assert registry.handle("Test", message2) == "Action 2"


def test_handler_with_literal_arguments():
    """Test handlers work with literal (string/number) arguments."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Claude"),
        arguments={
            "ask": LiteralNode("what is meaning?"),
            "about": LiteralNode("philosophy")
        }
    )

    result = registry.handle("Claude", message)
    assert "philosophy" in result
    assert "what is meaning?" in result


def test_vocabulary_aware_handler():
    """Test that handlers receive the receiver object for vocabulary awareness."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    codex = Receiver("Codex", hw_symbols("Codex"))
    native_sym = any_native_symbol("Codex")

    # observe: with native symbol
    message = MessageNode(
        receiver=ReceiverNode("Codex"),
        arguments={"observe": SymbolNode(native_sym)}
    )
    result = registry.handle("Codex", message, receiver=codex)
    assert "native" in result

    # observe: with non-native, non-global symbol
    message2 = MessageNode(
        receiver=ReceiverNode("Codex"),
        arguments={"observe": SymbolNode("#stillness")}
    )
    result2 = registry.handle("Codex", message2, receiver=codex)
    assert "collision" in result2 or "boundary" in result2


def test_observe_handler_native():
    """Test observe: handler with a native symbol."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    codex = Receiver("Codex", hw_symbols("Codex"))
    native_sym = any_native_symbol("Codex")

    message = MessageNode(
        receiver=ReceiverNode("Codex"),
        arguments={"observe": SymbolNode(native_sym)}
    )
    result = registry.handle("Codex", message, receiver=codex)
    assert f"Codex observes {native_sym}" in result
    assert "native" in result


def test_observe_handler_inherited():
    """Test observe: handler with an inherited symbol via parent chain."""
    from dispatcher import Receiver

    # Build a mini parent chain: Codex → Agent (holds #observe)
    agent = Receiver("Agent", hw_symbols("Agent"))
    codex = Receiver("Codex", hw_symbols("Codex"), parent=agent)

    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Codex"),
        arguments={"observe": SymbolNode("#observe")}
    )
    result = registry.handle("Codex", message, receiver=codex)
    assert "Codex observes #observe" in result
    assert "inherited" in result


def test_observe_handler_collision():
    """Test observe: handler with a foreign symbol — boundary collision."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    codex = Receiver("Codex", hw_symbols("Codex"))

    message = MessageNode(
        receiver=ReceiverNode("Codex"),
        arguments={"observe": SymbolNode("#stillness")}
    )
    result = registry.handle("Codex", message, receiver=codex)
    assert "Codex observes #stillness" in result
    assert "collision" in result


def test_act_handler_native():
    """Test act: handler with a native symbol — acts with authority."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    claude = Receiver("Claude", hw_symbols("Claude"))
    native_sym = any_native_symbol("Claude")

    message = MessageNode(
        receiver=ReceiverNode("Claude"),
        arguments={"act": SymbolNode(native_sym)}
    )
    result = registry.handle("Claude", message, receiver=claude)
    assert f"Claude acts on {native_sym}" in result
    assert "authority" in result


def test_act_handler_collision():
    """Test act: handler with a foreign symbol — acts at the boundary."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    claude = Receiver("Claude", hw_symbols("Claude"))

    message = MessageNode(
        receiver=ReceiverNode("Claude"),
        arguments={"act": SymbolNode("#fire")}
    )
    result = registry.handle("Claude", message, receiver=claude)
    assert "Claude acts on #fire" in result
    assert "boundary" in result


def test_observe_act_all_agents():
    """Test that observe: and act: are registered for all agents."""
    registry = MessageHandlerRegistry()

    for agent in ["Claude", "Copilot", "Gemini", "Codex"]:
        observe_msg = MessageNode(
            receiver=ReceiverNode(agent),
            arguments={"observe": SymbolNode("#State")}
        )
        act_msg = MessageNode(
            receiver=ReceiverNode(agent),
            arguments={"act": SymbolNode("#State")}
        )
        assert registry.handle(agent, observe_msg) is not None, f"{agent} missing observe: handler"
        assert registry.handle(agent, act_msg) is not None, f"{agent} missing act: handler"


def test_root_handlers():
    """Test built-in handlers for the root receiver (HelloWorld)."""
    registry = MessageHandlerRegistry()

    # act:
    message1 = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"act": SymbolNode("#all")}
    )
    result1 = registry.handle("HelloWorld", message1)
    assert "Root executing" in result1

    # observe:
    message2 = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"observe": SymbolNode("#all")}
    )
    result2 = registry.handle("HelloWorld", message2)
    assert "Root observing system state" in result2

    # orient:
    message_orient = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"orient": SymbolNode("#situation")}
    )
    result_orient = registry.handle("HelloWorld", message_orient)
    assert "Root orienting" in result_orient

    # decide:
    message_decide = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"decide": SymbolNode("#action")}
    )
    result_decide = registry.handle("HelloWorld", message_decide)
    assert "Root committing to decision" in result_decide

    # reflect:
    message_reflect = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"reflect": SymbolNode("#session")}
    )
    result_reflect = registry.handle("HelloWorld", message_reflect)
    assert "Root reflecting" in result_reflect

    # become:
    message3 = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"become": SymbolNode("#new")}
    )
    result3 = registry.handle("HelloWorld", message3)
    assert "Transformation" in result3
