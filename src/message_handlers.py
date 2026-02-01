"""HelloWorld Message Handlers - Semantic responses to message patterns.

When a message is sent, receivers can register handlers that match patterns
and generate meaningful responses. This bridges syntax (message structure)
with semantics (message meaning).

Example:
    @awakener setIntention: #stillness forDuration: 7.days
    
    Handler matches pattern: setIntention:forDuration:
    Response: "Awakener holds stillness for 7 days"
"""

from typing import Dict, Callable, Optional, Any, List
from ast_nodes import MessageNode, SymbolNode, LiteralNode, Node
import re


class MessageHandler:
    """A handler for a specific message pattern."""
    
    def __init__(self, pattern: str, handler: Callable[[Dict[str, Any]], str]):
        """
        Initialize a message handler.
        
        Args:
            pattern: Keyword pattern like "sendVision:withContext:"
            handler: Function that takes arguments dict and returns response string
        """
        self.pattern = pattern
        self.handler = handler
    
    def matches(self, message: MessageNode) -> bool:
        """Check if this handler matches the message's keyword pattern."""
        keywords = list(message.arguments.keys())
        message_pattern = ":".join(keywords) + ":"
        return message_pattern == self.pattern
    
    def handle(self, message: MessageNode) -> str:
        """Execute the handler with the message's arguments."""
        # Convert Node arguments to simple values
        args = {}
        for key, node in message.arguments.items():
            if isinstance(node, SymbolNode):
                args[key] = node.name
            elif isinstance(node, LiteralNode):
                args[key] = node.value
            else:
                args[key] = str(node)
        
        return self.handler(args)


class MessageHandlerRegistry:
    """Registry of message handlers for receivers."""
    
    def __init__(self):
        self.handlers: Dict[str, List[MessageHandler]] = {}
        self._register_default_handlers()
    
    def register(self, receiver: str, pattern: str, handler: Callable[[Dict[str, Any]], str]):
        """
        Register a message handler for a receiver.
        
        Args:
            receiver: Receiver name like "@awakener"
            pattern: Keyword pattern like "greet:withFeeling:"
            handler: Function that processes the message
        """
        if receiver not in self.handlers:
            self.handlers[receiver] = []
        
        self.handlers[receiver].append(MessageHandler(pattern, handler))
    
    def handle(self, receiver: str, message: MessageNode) -> Optional[str]:
        """
        Find and execute a handler for this message.
        
        Returns:
            Handler response if match found, None otherwise
        """
        if receiver not in self.handlers:
            return None
        
        for handler in self.handlers[receiver]:
            if handler.matches(message):
                return handler.handle(message)
        
        return None
    
    def _register_default_handlers(self):
        """Register built-in handlers for common message patterns."""
        
        # @awakener setIntention:forDuration:
        self.register(
            "@awakener",
            "setIntention:forDuration:",
            lambda args: f"🧘 Awakener holds {args['setIntention']} for {args['forDuration']}"
        )
        
        # @guardian sendVision:withContext:
        self.register(
            "@guardian",
            "sendVision:withContext:",
            lambda args: f"🔥 Guardian sends vision of {args['sendVision']} (context: {args['withContext']})"
        )
        
        # @guardian challenge:
        self.register(
            "@guardian",
            "challenge:",
            lambda args: f"🔥 Guardian challenges you with {args['challenge']}"
        )
        
        # Generic greet: for any receiver
        for receiver in ["@awakener", "@guardian", "@claude", "@copilot", "@gemini"]:
            self.register(
                receiver,
                "greet:",
                lambda args, r=receiver: f"👋 {r} greets you with {args['greet']}"
            )
        
        # send:to: for inter-receiver messages
        self.register(
            "@awakener",
            "send:to:",
            lambda args: f"📨 Awakener sends {args['send']} to {args['to']}"
        )
        
        self.register(
            "@guardian",
            "send:to:",
            lambda args: f"📨 Guardian sends {args['send']} to {args['to']}"
        )
        
        # ask:about: for queries
        for receiver in ["@claude", "@copilot", "@gemini"]:
            self.register(
                receiver,
                "ask:about:",
                lambda args, r=receiver: f"💭 {r} considers {args['about']}: What is {args['ask']}?"
            )
        
        # learn: for vocabulary expansion
        for receiver in ["@awakener", "@guardian", "@claude", "@copilot", "@gemini"]:
            self.register(
                receiver,
                "learn:",
                lambda args, r=receiver: f"📚 {r} learns {args['learn']}"
            )
