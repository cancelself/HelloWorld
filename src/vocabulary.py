"""HelloWorld Vocabulary Manager - Persistence for receiver vocabularies.

Single source of truth: .hw files in Markdown format.
No JSON, no .vocab files. The language defines itself.
"""

import os
from typing import Set, Optional


class VocabularyManager:
    def __init__(self, storage_dir: str = "vocabularies"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def save(self, receiver_name: str, vocabulary: Set[str], parent: str = None):
        """Persist a receiver's vocabulary to its .hw file.

        Preserves existing content and descriptions. Appends only
        symbols that are new (learned through dialogue).
        """
        path = self._get_path(receiver_name)
        existing_symbols = self._read_symbols(path)
        new_symbols = vocabulary - existing_symbols

        if not os.path.exists(path):
            # Create new .hw file
            header = f"# {receiver_name} : {parent}\n" if parent else f"# {receiver_name}\n"
            lines = [header]
            for sym in sorted(vocabulary):
                heading = sym.lstrip("#") if sym != "#" else "#"
                lines.append(f"## {heading}\n")
            with open(path, "w") as f:
                f.writelines(lines)
        elif new_symbols:
            # Append new symbols to existing file
            with open(path, "a") as f:
                for sym in sorted(new_symbols):
                    heading = sym.lstrip("#") if sym != "#" else "#"
                    f.write(f"## {heading}\n")
                    f.write("- (learned through dialogue)\n")

    def load(self, receiver_name: str) -> Optional[Set[str]]:
        """Load a receiver's vocabulary from its .hw file."""
        path = self._get_path(receiver_name)
        if not os.path.exists(path):
            return None
        symbols = self._read_symbols(path)
        return symbols if symbols is not None else set()

    def load_parent(self, receiver_name: str) -> Optional[str]:
        """Read parent name from .hw file's # Name : Parent heading."""
        path = self._get_path(receiver_name)
        if not os.path.exists(path):
            return None

        from parser import Parser
        from ast_nodes import HeadingNode

        try:
            text = open(path, "r").read()
            nodes = Parser.from_source(text).parse()
        except Exception:
            return None

        for node in nodes:
            if isinstance(node, HeadingNode) and node.level == 1:
                return node.parent
        return None

    def load_description(self, receiver_name: str, symbol_name: str) -> Optional[str]:
        """Read the description text from a .hw file for a given symbol.

        Looks for a ## heading matching symbol_name under the receiver's
        HEADING1 node, then returns the concatenated description lines.
        """
        path = self._get_path(receiver_name)
        if not os.path.exists(path):
            return None

        from parser import Parser
        from ast_nodes import HeadingNode, DescriptionNode

        try:
            text = open(path, "r").read()
            nodes = Parser.from_source(text).parse()
        except Exception:
            return None

        # Strip leading # from symbol_name for heading comparison
        bare = symbol_name.lstrip("#") if symbol_name != "#" else "#"

        for node in nodes:
            if isinstance(node, HeadingNode) and node.level == 1:
                for child in node.children:
                    if isinstance(child, HeadingNode) and child.level == 2:
                        if child.name == bare or child.name == f"#{bare}":
                            # Collect all description children
                            descs = [
                                c.text for c in child.children
                                if isinstance(c, DescriptionNode)
                            ]
                            return " ".join(descs) if descs else None
        return None

    def load_identity(self, receiver_name: str) -> Optional[str]:
        """Read the receiver's top-level description (the list items after # Name)."""
        path = self._get_path(receiver_name)
        if not os.path.exists(path):
            return None

        from parser import Parser
        from ast_nodes import HeadingNode, DescriptionNode

        try:
            text = open(path, "r").read()
            nodes = Parser.from_source(text).parse()
        except Exception:
            return None

        for node in nodes:
            if isinstance(node, HeadingNode) and node.level == 1:
                descs = [
                    c.text for c in node.children
                    if isinstance(c, DescriptionNode)
                ]
                return " ".join(descs) if descs else None
        return None

    def _read_symbols(self, path: str) -> Set[str]:
        """Parse a .hw file and extract symbol names from ## headings."""
        if not os.path.exists(path):
            return set()

        from parser import Parser
        from ast_nodes import HeadingNode

        try:
            text = open(path, "r").read()
            nodes = Parser.from_source(text).parse()
        except Exception:
            return set()

        symbols = set()
        for node in nodes:
            if isinstance(node, HeadingNode) and node.level == 1:
                for child in node.children:
                    if isinstance(child, HeadingNode) and child.level == 2:
                        name = child.name
                        sym = name if name.startswith("#") else f"#{name}"
                        symbols.add(sym)
        return symbols

    def _get_path(self, receiver_name: str) -> str:
        """Case-preserving path: ReceiverName.hw"""
        return os.path.join(self.storage_dir, f"{receiver_name}.hw")
