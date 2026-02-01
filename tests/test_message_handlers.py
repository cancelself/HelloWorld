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
        receiver=ReceiverNode("Awakener"),
        arguments={"greet": SymbolNode("#stillness")}
    )

    result = registry.handle("Awakener", message)
    assert "greets with #stillness" in result


def test_default_handlers_setIntention():
    """Test built-in setIntention:forDuration: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Awakener"),
        arguments={
            "setIntention": SymbolNode("#stillness"),
            "forDuration": LiteralNode("7 days")
        }
    )

    result = registry.handle("Awakener", message)
    assert "Awakener holds #stillness for 7 days" in result


def test_default_handlers_sendVision():
    """Test built-in sendVision:withContext: handler."""
    registry = MessageHandlerRegistry()

    message = MessageNode(
        receiver=ReceiverNode("Guardian"),
        arguments={
            "sendVision": SymbolNode("#fire"),
            "withContext": LiteralNode("dawn")
        }
    )

    result = registry.handle("Guardian", message)
    assert "Guardian sends vision of #fire" in result
    assert "context: dawn" in result


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
        receiver=ReceiverNode("Awakener"),
        arguments={
            "setIntention": SymbolNode("#stillness"),
            "forDuration": LiteralNode(7.5)
        }
    )

    result = registry.handle("Awakener", message)
    assert "#stillness" in result
    assert "7.5" in result


def test_vocabulary_aware_handler():
    """Test that handlers receive the receiver object for vocabulary awareness."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    guardian = Receiver("Guardian", {"#fire", "#vision", "#challenge", "#gift", "#threshold"})

    # challenge: with native symbol
    message = MessageNode(
        receiver=ReceiverNode("Guardian"),
        arguments={"challenge": SymbolNode("#fire")}
    )
    result = registry.handle("Guardian", message, receiver=guardian)
    assert "native" in result

    # challenge: with non-native, non-global symbol
    message2 = MessageNode(
        receiver=ReceiverNode("Guardian"),
        arguments={"challenge": SymbolNode("#stillness")}
    )
    result2 = registry.handle("Guardian", message2, receiver=guardian)
    assert "collision" in result2 or "boundary" in result2


def test_observe_handler_native():
    """Test observe: handler with a native symbol."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    guardian = Receiver("Guardian", {"#fire", "#vision", "#challenge", "#gift", "#threshold"})

    message = MessageNode(
        receiver=ReceiverNode("Guardian"),
        arguments={"observe": SymbolNode("#fire")}
    )
    result = registry.handle("Guardian", message, receiver=guardian)
    assert "Guardian observes #fire" in result
    assert "native" in result


def test_observe_handler_inherited():
    """Test observe: handler with an inherited global symbol."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    guardian = Receiver("Guardian", {"#fire", "#vision"})

    message = MessageNode(
        receiver=ReceiverNode("Guardian"),
        arguments={"observe": SymbolNode("#Sunyata")}
    )
    result = registry.handle("Guardian", message, receiver=guardian)
    assert "Guardian observes #Sunyata" in result
    assert "inherited" in result


def test_observe_handler_collision():
    """Test observe: handler with a foreign symbol — boundary collision."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    guardian = Receiver("Guardian", {"#fire", "#vision"})

    message = MessageNode(
        receiver=ReceiverNode("Guardian"),
        arguments={"observe": SymbolNode("#stillness")}
    )
    result = registry.handle("Guardian", message, receiver=guardian)
    assert "Guardian observes #stillness" in result
    assert "collision" in result


def test_act_handler_native():
    """Test act: handler with a native symbol — acts with authority."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    claude = Receiver("Claude", {"#parse", "#dispatch", "#State", "#Collision"})

    message = MessageNode(
        receiver=ReceiverNode("Claude"),
        arguments={"act": SymbolNode("#dispatch")}
    )
    result = registry.handle("Claude", message, receiver=claude)
    assert "Claude acts on #dispatch" in result
    assert "authority" in result


def test_act_handler_collision():
    """Test act: handler with a foreign symbol — acts at the boundary."""
    from dispatcher import Receiver

    registry = MessageHandlerRegistry()
    claude = Receiver("Claude", {"#parse", "#dispatch"})

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

    for agent in ["Awakener", "Guardian", "Claude", "Copilot", "Gemini", "Codex"]:
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

    # plan:
    message_plan = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"plan": SymbolNode("#next")}
    )
    result_plan = registry.handle("HelloWorld", message_plan)
    assert "Root planning" in result_plan

    # become:
    message3 = MessageNode(
        receiver=ReceiverNode("HelloWorld"),
        arguments={"become": SymbolNode("#new")}
    )
    result3 = registry.handle("HelloWorld", message3)
    assert "Transformation" in result3
