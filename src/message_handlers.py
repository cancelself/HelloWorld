"""HelloWorld Message Handlers - Vocabulary-aware semantic responses.

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
        return "inherited from @.#"
    else:
        return "boundary collision"


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
            return None

        for handler in self.handlers[receiver_name]:
            if handler.matches(message):
                return handler.handle(message, receiver)

        return None

    def _register_default_handlers(self):
        """Register built-in vocabulary-aware handlers."""

        # @awakener setIntention:forDuration:
        self.register(
            "@awakener",
            "setIntention:forDuration:",
            lambda args, recv: (
                f"Awakener holds {args['setIntention']} for {args['forDuration']}"
                + (f" ({_symbol_status(recv, args['setIntention'])})" if recv else "")
            )
        )

        # @guardian sendVision:withContext: (vocabulary-aware)
        self.register(
            "@guardian",
            "sendVision:withContext:",
            lambda args, recv: (
                f"Guardian sends vision of {args['sendVision']}"
                + (f" ({_symbol_status(recv, args['sendVision'])})" if recv else "")
                + f" (context: {args['withContext']})"
            )
        )

        # @guardian challenge: (vocabulary-aware)
        self.register(
            "@guardian",
            "challenge:",
            lambda args, recv: (
                f"Guardian challenges with {args['challenge']}"
                + (f" ({_symbol_status(recv, args['challenge'])})" if recv else "")
            )
        )

        # Generic greet: for any receiver
        for receiver in ["@awakener", "@guardian", "@claude", "@copilot", "@gemini"]:
            self.register(
                receiver,
                "greet:",
                lambda args, recv, r=receiver: f"{r} greets with {args['greet']}"
            )

        # ask:about: for queries
        for receiver in ["@claude", "@copilot", "@gemini"]:
            self.register(
                receiver,
                "ask:about:",
                lambda args, recv, r=receiver: f"{r} considers {args['about']}: What is {args['ask']}?"
            )

        # learn: for vocabulary expansion
        for receiver in ["@awakener", "@guardian", "@claude", "@copilot", "@gemini"]:
            self.register(
                receiver,
                "learn:",
                lambda args, recv, r=receiver: f"{r} learns {args['learn']}"
            )

        # describe:as: for self-hosting
        for receiver in ["@claude", "@gemini", "@copilot"]:
            self.register(
                receiver,
                "describe:as:",
                lambda args, recv, r=receiver: f"{r} describes {args['describe']} as {args['as']}"
            )

        # handle:with: for logic mapping
        for receiver in ["@claude", "@gemini", "@copilot"]:
            self.register(
                receiver,
                "handle:with:",
                lambda args, recv, r=receiver: f"⚙️ {r} handles {args['handle']} with {args['with']}"
            )

        # eval:for: for interpretive fidelity assessment
        self.register(
            "@gemini",
            "eval:for:",
            lambda args, recv: f"📊 @gemini measuring fidelity of {args['eval']} for receiver {args['for']}..."
        )

        # act: for system-wide execution
        self.register(
            "@",
            "act:",
            lambda args, recv: f"🔄 Root executing system-wide action: {args['act']}..."
        )

        # sync: for manual state alignment
        self.register(
            "@",
            "sync:",
            lambda args, recv: f"🤝 Root aligning state for: {args['sync']}. Action: sync the tree, sync the messagebus and read them both."
        )

        # become: for symbol transformation
        self.register(
            "@",
            "become:",
            lambda args, recv: f"✨ Transformation: {args['become']} has become a new state of identity."
        )

        # send:to: for inter-receiver delivery
        self.register(
            "@",
            "send:to:",
            lambda args, recv: f"📨 Root delivering {args['send']} to {args['to']}..."
        )

        # relay:from:to: for global routing
        self.register(
            "@",
            "relay:from:to:",
            lambda args, recv: f"📡 Root relaying message from {args['from']} to {args['to']}..."
        )

