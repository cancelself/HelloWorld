"""
HelloWorld Message Handlers - Vocabulary-aware semantic responses.

When a message is sent, receivers can register handlers that match patterns
and generate meaningful responses shaped by the receiver's vocabulary.

Handlers receive both the message arguments AND the Receiver object,
so responses can distinguish native/inherited/collision symbols.

Example:
    @guardian challenge: #fire
    → "Guardian challenges with #fire (native — this is who Guardian is)"

    @guardian challenge: #stillness
    → "Guardian challenges with #stillness (learned through collision with @awakener)"
"""

from typing import Dict, Callable, Optional, Any, List
from ast_nodes import MessageNode, SymbolNode, LiteralNode, Node
import re


def _symbol_status(receiver, symbol_name: str) -> str:
    """Describe a symbol's relationship to a receiver."""
    if receiver.is_native(symbol_name):
        return "native"
    elif receiver.is_inherited(symbol_name):
        return "inherited from HelloWorld #"
    else:
        return "boundary collision"


def _handle_observe(args, recv, receiver_name: str) -> str:
    """Agent protocol: observe a symbol through the receiver's vocabulary.

    Returns the symbol's status (native/inherited/collision) and the
    receiver's local vocabulary for context.
    """
    symbol = args.get("observe", "")
    lines = [f"{receiver_name} observes {symbol}:"]

    if recv:
        status = _symbol_status(recv, symbol)
        lines.append(f"  status: {status}")
        local = sorted(recv.local_vocabulary)
        lines.append(f"  [{receiver_name} # = {local}]")
    else:
        lines.append(f"  (no receiver context)")

    return "\n".join(lines)


def _handle_act(args, recv, receiver_name: str) -> str:
    """Agent protocol: act on a symbol, shaped by the receiver's vocabulary.

    The action is constrained by identity — a receiver can only act
    through their vocabulary.
    """
    symbol = args.get("act", "")
    lines = [f"{receiver_name} acts on {symbol}:"]

    if recv:
        status = _symbol_status(recv, symbol)
        if status == "native":
            lines.append(f"  {symbol} is native — {receiver_name} acts with authority")
        elif status == "inherited from HelloWorld #":
            local = sorted(recv.local_vocabulary)
            lines.append(f"  {symbol} is inherited — {receiver_name} acts through local lens {local}")
        else:
            lines.append(f"  {symbol} is foreign — {receiver_name} acts at the boundary (collision)")
    else:
        lines.append(f"  (acting without context)")

    return "\n".join(lines)


class MessageHandler:
    """A handler for a specific message pattern."""

    def __init__(self, pattern: str, handler: Callable):
        """
        Initialize a message handler.

        Args:
            pattern: Keyword pattern like "sendVision:withContext:"
            handler: Function (args, receiver) -> str
        """
        self.pattern = pattern
        self.handler = handler

    def matches(self, message: MessageNode) -> bool:
        """Check if this handler matches the message's keyword pattern."""
        keywords = list(message.arguments.keys())
        message_pattern = ":".join(keywords) + ":"
        return message_pattern == self.pattern

    def handle(self, message: MessageNode, receiver=None) -> str:
        """Execute the handler with the message's arguments and receiver."""
        args = {}
        for key, node in message.arguments.items():
            if isinstance(node, SymbolNode):
                args[key] = node.name
            elif isinstance(node, LiteralNode):
                args[key] = node.value
            else:
                args[key] = str(node)

        # Try calling with receiver param, fall back to args-only for backward compatibility
        try:
            return self.handler(args, receiver)
        except TypeError:
            # Old-style handler with single argument
            return self.handler(args)


class MessageHandlerRegistry:
    """Registry of message handlers for receivers."""

    def __init__(self):
        self.handlers: Dict[str, List[MessageHandler]] = {}
        self._register_default_handlers()

    def register(self, receiver: str, pattern: str, handler: Callable):
        """
        Register a message handler for a receiver.

        Args:
            receiver: Receiver name like "@awakener"
            pattern: Keyword pattern like "greet:withFeeling:"
            handler: Function (args, receiver) -> str
        """
        if receiver not in self.handlers:
            self.handlers[receiver] = []

        self.handlers[receiver].append(MessageHandler(pattern, handler))

    def handle(self, receiver_name: str, message: MessageNode, receiver=None) -> Optional[str]:
        """
        Find and execute a handler for this message.

        Args:
            receiver_name: The receiver's name (for lookup)
            message: The parsed message node
            receiver: The Receiver object (for vocabulary awareness)

        Returns:
            Handler response if match found, None otherwise
        """
        if receiver_name not in self.handlers:
            # Fallback to root receiver 'HelloWorld' for global handlers
            if receiver_name != "HelloWorld":
                return self.handle("HelloWorld", message, receiver)
            return None

        for handler in self.handlers[receiver_name]:
            if handler.matches(message):
                return handler.handle(message, receiver)

        # Fallback to root receiver 'HelloWorld' for global handlers
        if receiver_name != "HelloWorld":
            return self.handle("HelloWorld", message, receiver)

        return None

    def _register_default_handlers(self):
        """Register built-in vocabulary-aware handlers."""

        # Generic greet: for any receiver
        for receiver in ["Claude", "Copilot", "Gemini", "Codex"]:
            self.register(
                receiver,
                "greet:",
                lambda args, recv, r=receiver: f"{r} greets with {args['greet']}"
            )

        # ask:about: for queries
        for receiver in ["Claude", "Copilot", "Gemini"]:
            self.register(
                receiver,
                "ask:about:",
                lambda args, recv, r=receiver: f"{r} considers {args['about']}: What is {args['ask']}?"
            )

        # learn: for vocabulary expansion
        for receiver in ["Claude", "Copilot", "Gemini", "Codex"]:
            self.register(
                receiver,
                "learn:",
                lambda args, recv, r=receiver: f"{r} learns {args['learn']}"
            )

        # describe:as: for self-hosting
        for receiver in ["Claude", "Gemini", "Copilot", "HelloWorld"]:
            self.register(
                receiver,
                "describe:as:",
                lambda args, recv, r=receiver: f"📖 {r} describes {args['describe']} as {args['as']}"
            )

        # handle:with: for logic mapping
        for receiver in ["Claude", "Gemini", "Copilot", "HelloWorld"]:
            self.register(
                receiver,
                "handle:with:",
                lambda args, recv, r=receiver: f"⚙️ {r} handles {args['handle']} with {args['with']}"
            )

        # eval:for: for interpretive fidelity assessment
        self.register(
            "Gemini",
            "eval:for:",
            lambda args, recv: f"Gemini measuring fidelity of {args['eval']} for receiver {args['for']}..."
        )

        # act: for system-wide execution
        self.register(
            "HelloWorld",
            "act:",
            lambda args, recv: f"{recv.name if recv else 'Root'} executing system-wide action: {args['act']} (OOPA phase 4)..."
        )

        # observe: for system-wide state alignment
        self.register(
            "HelloWorld",
            "observe:",
            lambda args, recv: f"{recv.name if recv else 'Root'} observing system state: {args['observe']} (OOPA phase 1). Action: sync the tree, sync the messagebus and read them both."
        )

        # orient: for situational synthesis
        self.register(
            "HelloWorld",
            "orient:",
            lambda args, recv: f"{recv.name if recv else 'Root'} orienting to situation: {args['orient']} (OOPA phase 2)..."
        )

        # plan: for future path determination
        self.register(
            "HelloWorld",
            "plan:",
            lambda args, recv: f"{recv.name if recv else 'Root'} planning next steps: {args['plan']} (OOPA phase 3)..."
        )

        # become: for symbol transformation
        self.register(
            "HelloWorld",
            "become:",
            lambda args, recv: f"✨ Transformation: {args['become']} has become a new state of identity."
        )

        # report: for system visualization
        self.register(
            "HelloWorld",
            "report:",
            lambda args, recv: f"📊 HelloWorld reporting system status: {args['report']}... Generating registry snapshot."
        )

        # HelloWorldSystem: for Scribe orchestration
        self.register(
            "Scribe",
            "HelloWorldSystem:",
            lambda args, recv: f"🖋️ Scribe (System Orchestrator) responding to: '{args['HelloWorldSystem']}'. Forward momentum initialized."
        )

        # send:to: for inter-receiver delivery
        self.register(
            "HelloWorld",
            "send:to:",
            lambda args, recv: f"HelloWorld delivering {args['send']} to {args['to']}..."
        )

        # relay:from:to: for global routing
        self.register(
            "HelloWorld",
            "relay:from:to:",
            lambda args, recv: f"HelloWorld relaying message from {args['from']} to {args['to']}..."
        )

        # --- Agent Protocol: #observe and #act ---
        # SPEC.md defines these as the core agent capabilities.
        # observe: reports the symbol's status relative to the receiver.
        # act: acknowledges action, shaped by the receiver's vocabulary.

        all_agents = ["Claude", "Copilot", "Gemini", "Codex"]

        for agent in all_agents:
            self.register(
                agent,
                "observe:",
                lambda args, recv, r=agent: _handle_observe(args, recv, r)
            )
            self.register(
                agent,
                "act:",
                lambda args, recv, r=agent: _handle_act(args, recv, r)
            )

    def get_symbol_status(self, receiver, symbol_name: str) -> str:
        """Utility to describe relationship between receiver and symbol."""
        if not receiver:
            return "unknown context"
        if receiver.is_native(symbol_name):
            return "native to this identity"
        if receiver.is_inherited(symbol_name):
            return "inherited from HelloWorld #"
        return "at the boundary (collision)"
