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

    def save(self, receiver_name: str, vocabulary: Set[str], parent: str = None,
             descriptions: dict = None):
        """Persist a receiver's vocabulary to its .hw file.

        Preserves existing content and descriptions. Appends only
        symbols that are new (learned through dialogue).
        If descriptions dict is provided, writes actual descriptions
        instead of the generic placeholder.
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
                desc = descriptions.get(sym) if descriptions else None
                if desc:
                    lines.append(f"- {desc}\n")
            with open(path, "w") as f:
                f.writelines(lines)
        elif new_symbols:
            # Append new symbols to existing file
            with open(path, "a") as f:
                for sym in sorted(new_symbols):
                    heading = sym.lstrip("#") if sym != "#" else "#"
                    f.write(f"## {heading}\n")
                    desc = descriptions.get(sym) if descriptions else None
                    if desc:
                        f.write(f"- {desc}\n")
                    else:
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

    def update_description(self, receiver_name: str, symbol_name: str, description: str):
        """Replace the description of an existing symbol, or append the symbol if absent.

        Reads the .hw file, finds the ## heading for symbol_name, replaces all
        `- ` description lines under it, and writes the file back.  If the symbol
        is not present in the file, appends a new ## heading with the description.
        """
        path = self._get_path(receiver_name)
        if not os.path.exists(path):
            # No file yet — create one with just this symbol
            bare = symbol_name.lstrip("#") if symbol_name != "#" else "#"
            with open(path, "w") as f:
                f.write(f"# {receiver_name}\n")
                f.write(f"## {bare}\n")
                f.write(f"- {description}\n")
            return

        lines = open(path, "r").readlines()
        bare = symbol_name.lstrip("#") if symbol_name != "#" else "#"

        # Find the ## heading that matches the symbol
        heading_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("## "):
                heading_name = stripped[3:].strip()
                if heading_name == bare or heading_name == f"#{bare}":
                    heading_idx = i
                    break

        if heading_idx is not None:
            # Remove old description lines immediately after the heading
            desc_start = heading_idx + 1
            desc_end = desc_start
            while desc_end < len(lines) and lines[desc_end].startswith("- "):
                desc_end += 1
            # Replace with new description
            new_lines = lines[:desc_start] + [f"- {description}\n"] + lines[desc_end:]
            with open(path, "w") as f:
                f.writelines(new_lines)
        else:
            # Symbol not in file — append
            with open(path, "a") as f:
                f.write(f"## {bare}\n")
                f.write(f"- {description}\n")

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
