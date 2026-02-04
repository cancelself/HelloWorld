"""HelloWorld MCP Tools — deterministic vocabulary operations.

Seven tools that handle the structural/deterministic side of the runtime:
vocabulary lookup, listing, saving, collision logging, messaging, and
receiver discovery. These are the tools the orchestrator agent uses
to ground its interpretive work in factual state.

Designed for use with Claude Agent SDK's @tool decorator pattern,
but usable standalone for testing without the SDK.
"""

import os
from datetime import datetime
from typing import Optional

from hw_reader import read_hw_file, read_hw_directory, save_hw_symbol
import message_bus


class HwTools:
    """Collection of HelloWorld MCP tools.

    All tools operate on .hw files and the message bus.
    No parser dependency — uses hw_reader for all file operations.
    """

    def __init__(self, vocab_dir: str = "vocabularies"):
        self.vocab_dir = vocab_dir
        self.log_file = "collisions.log"

    def _receiver_path(self, receiver_name: str) -> str:
        return os.path.join(self.vocab_dir, f"{receiver_name}.hw")

    def vocabulary_lookup(
        self, receiver_name: str, symbol_name: str
    ) -> dict:
        """Three-outcome symbol lookup: native, inherited, or unknown.

        Checks the receiver's .hw file for the symbol, then checks
        the parent chain (parent's .hw file, up to HelloWorld).

        Returns:
            dict with keys: outcome, symbol, receiver, context
        """
        receiver = read_hw_file(self._receiver_path(receiver_name))
        if receiver is None:
            return {
                "outcome": "unknown",
                "symbol": symbol_name,
                "receiver": receiver_name,
                "context": f"Receiver {receiver_name} not found",
            }

        # Check native
        if symbol_name in receiver.symbols:
            return {
                "outcome": "native",
                "symbol": symbol_name,
                "receiver": receiver_name,
                "context": f"Native to {receiver_name}. "
                           f"Description: {receiver.symbol_description(symbol_name)}",
            }

        # Check inheritance chain
        parent_name = receiver.parent
        visited = {receiver_name}
        while parent_name and parent_name not in visited:
            visited.add(parent_name)
            parent_path = self._receiver_path(parent_name)
            parent = read_hw_file(parent_path)
            if parent is None:
                break
            if symbol_name in parent.symbols:
                return {
                    "outcome": "inherited",
                    "symbol": symbol_name,
                    "receiver": receiver_name,
                    "context": f"Inherited from {parent_name}. "
                               f"Description: {parent.symbol_description(symbol_name)}",
                }
            parent_name = parent.parent

        # Check HelloWorld root (all receivers inherit from it)
        if receiver_name != "HelloWorld":
            hw = read_hw_file(self._receiver_path("HelloWorld"))
            if hw and symbol_name in hw.symbols:
                return {
                    "outcome": "inherited",
                    "symbol": symbol_name,
                    "receiver": receiver_name,
                    "context": f"Inherited from HelloWorld. "
                               f"Description: {hw.symbol_description(symbol_name)}",
                }

        return {
            "outcome": "unknown",
            "symbol": symbol_name,
            "receiver": receiver_name,
            "context": f"Not found in {receiver_name} or its parent chain",
        }

    def vocabulary_list(self, receiver_name: str) -> dict:
        """List a receiver's vocabulary (symbols from its .hw file).

        Returns:
            dict with keys: receiver, symbols, count, identity
        """
        receiver = read_hw_file(self._receiver_path(receiver_name))
        if receiver is None:
            return {
                "receiver": receiver_name,
                "symbols": [],
                "count": 0,
                "identity": None,
            }

        return {
            "receiver": receiver_name,
            "symbols": receiver.vocabulary,
            "count": len(receiver.symbols),
            "identity": receiver.identity,
        }

    def vocabulary_save(
        self,
        receiver_name: str,
        symbol_name: str,
        description: Optional[str] = None,
    ) -> dict:
        """Append a new symbol to a receiver's .hw file.

        Returns:
            dict with keys: receiver, symbol, status
        """
        path = self._receiver_path(receiver_name)
        if not os.path.exists(path):
            return {
                "receiver": receiver_name,
                "symbol": symbol_name,
                "status": f"error: {path} not found",
            }

        # Check if symbol already exists
        receiver = read_hw_file(path)
        if receiver and symbol_name in receiver.symbols:
            return {
                "receiver": receiver_name,
                "symbol": symbol_name,
                "status": "already_exists",
            }

        save_hw_symbol(path, symbol_name, description)
        return {
            "receiver": receiver_name,
            "symbol": symbol_name,
            "status": "saved",
        }

    def collision_log(
        self,
        receiver_name: str,
        symbol_name: str,
        collision_type: str = "collision",
        context: Optional[str] = None,
    ) -> dict:
        """Append a collision entry to collisions.log.

        Returns:
            dict with keys: logged, entry
        """
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] {collision_type.upper()}: {receiver_name} {symbol_name}"
        if context:
            entry += f" — {context}"
        entry += "\n"

        with open(self.log_file, "a") as f:
            f.write(entry)

        return {"logged": True, "entry": entry.strip()}

    def message_send(
        self, sender: str, receiver: str, content: str
    ) -> dict:
        """Send a message via the HelloWorld message bus.

        Returns:
            dict with keys: msg_id, sender, receiver
        """
        msg_id = message_bus.send(sender, receiver, content)
        return {"msg_id": msg_id, "sender": sender, "receiver": receiver}

    def message_receive(self, receiver: str) -> dict:
        """Receive the next message from a receiver's inbox.

        Returns:
            dict with keys: has_message, sender, content, timestamp
        """
        msg = message_bus.receive(receiver)
        if msg is None:
            return {"has_message": False}
        return {
            "has_message": True,
            "sender": msg.sender,
            "content": msg.content,
            "timestamp": msg.timestamp,
        }

    def receivers_list(self) -> dict:
        """List all receivers found in the vocabulary directory.

        Returns:
            dict with keys: receivers (list of dicts with name, symbol_count, parent)
        """
        all_receivers = read_hw_directory(self.vocab_dir)
        receivers = []
        for name, rec in sorted(all_receivers.items()):
            receivers.append({
                "name": name,
                "symbol_count": len(rec.symbols),
                "parent": rec.parent,
            })
        return {"receivers": receivers}

    def all_tools(self) -> list:
        """Return all tool functions for SDK registration."""
        return [
            self.vocabulary_lookup,
            self.vocabulary_list,
            self.vocabulary_save,
            self.collision_log,
            self.message_send,
            self.message_receive,
            self.receivers_list,
        ]
