"""Tests for message_handlers module."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from message_handlers import MessageHandler, MessageHandlerRegistry
from ast_nodes import MessageNode, ReceiverNode, SymbolNode, LiteralNode


def test_message_handler_pattern_matching():
    """Test that handlers match correct patterns."""
    handler = MessageHandler(
        "greet:withFeeling:",
        lambda args, recv: f"Hello with {args['withFeeling']}"
    )

    # Should match
    message1 = MessageNode(
        receiver=ReceiverNode("@awakener"),
        arguments={"greet": SymbolNode("#stillness"), "withFeeling": LiteralNode("joy")}
    )
    assert handler.matches(message1)

    # Should not match (different pattern)
    message2 = MessageNode(
        receiver=ReceiverNode("@awakener"),
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
        receiver=ReceiverNode("@awakener"),
        arguments={"greet": SymbolNode("#stillness")}
    )

    result = handler.handle(message)
    assert result == "Hello #stillness"


def test_message_handler_registry():
    """Test registry registration and lookup."""
    registry = MessageHandlerRegistry()

    # Register custom handler
    registry.register(
        "@test",
        "customAction:",
        lambda args, recv: f"Custom: {args['customAction']}"
    )

    # Test custom handler
    message = MessageNode(
        receiver=ReceiverNode("@test"),
        arguments={"customAction": SymbolNode("#fire")}
    )

    result = registry.handle("@test", message)
    assert result == "Custom: #fire"


def test_default_handlers_greet():
    """Test built-in greet: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("@awakener"),
        arguments={"greet": SymbolNode("#stillness")}
    )

    result = registry.handle("@awakener", message)
    assert "greets with #stillness" in result


def test_default_handlers_setIntention():
    """Test built-in setIntention:forDuration: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("@awakener"),
        arguments={
            "setIntention": SymbolNode("#stillness"),
            "forDuration": LiteralNode("7 days")
        }
    )

    result = registry.handle("@awakener", message)
    assert "Awakener holds #stillness for 7 days" in result


def test_default_handlers_sendVision():
    """Test built-in sendVision:withContext: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("@guardian"),
        arguments={
            "sendVision": SymbolNode("#fire"),
            "withContext": LiteralNode("dawn")
        }
    )

    result = registry.handle("@guardian", message)
    assert "Guardian sends vision of #fire" in result
    assert "context: dawn" in result


def test_handler_returns_none_for_no_match():
    """Test that registry returns None when no handler matches."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("@unknown"),
        arguments={"unknownAction": SymbolNode("#test")}
    )

    result = registry.handle("@unknown", message)
    assert result is None


def test_multiple_handlers_per_receiver():
    """Test that multiple handlers can be registered for same receiver."""
    registry = MessageHandlerRegistry()

    # Register two handlers for same receiver
    registry.register("@test", "action1:", lambda args, recv: "Action 1")
    registry.register("@test", "action2:", lambda args, recv: "Action 2")

    message1 = MessageNode(
        receiver=ReceiverNode("@test"),
        arguments={"action1": SymbolNode("#test")}
    )
    message2 = MessageNode(
        receiver=ReceiverNode("@test"),
        arguments={"action2": SymbolNode("#test")}
    )

    assert registry.handle("@test", message1) == "Action 1"
    assert registry.handle("@test", message2) == "Action 2"


def test_handler_with_literal_arguments():
    """Test handlers work with literal (string/number) arguments."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("@awakener"),
        arguments={
            "setIntention": SymbolNode("#stillness"),
            "forDuration": LiteralNode(7.5)
        }
    )

    result = registry.handle("@awakener", message)
    assert "#stillness" in result
    assert "7.5" in result


def test_vocabulary_aware_handler():
    """Test that handlers receive the receiver object for vocabulary awareness."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    guardian = Receiver("@guardian", {"#fire", "#vision", "#challenge", "#gift", "#threshold"})

    # challenge: with native symbol
    message = MessageNode(
        receiver=ReceiverNode("@guardian"),
        arguments={"challenge": SymbolNode("#fire")}
    )
    result = registry.handle("@guardian", message, receiver=guardian)
    assert "native" in result

    # challenge: with non-native, non-global symbol
    message2 = MessageNode(
        receiver=ReceiverNode("@guardian"),
        arguments={"challenge": SymbolNode("#stillness")}
    )
    result2 = registry.handle("@guardian", message2, receiver=guardian)
    assert "collision" in result2 or "boundary" in result2
