"""HelloWorld Vocabulary Manager - Persistence for receiver vocabularies."""

import os
import json
from typing import Dict, List, Set, Optional

class VocabularyManager:
    def __init__(self, storage_dir: str = "storage/vocab"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def save(self, receiver_name: str, symbols: Set[str]):
        """Save a receiver's vocabulary to a .vocab file (JSON)."""
        filename = self._get_path(receiver_name)
        data = {
            "receiver": receiver_name,
            "vocabulary": sorted(list(symbols))
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, receiver_name: str) -> Optional[Set[str]]:
        """Load a receiver's vocabulary from a .vocab file."""
        filename = self._get_path(receiver_name)
        if not os.path.exists(filename):
            return None
        
        with open(filename, 'r') as f:
            data = json.load(f)
            return set(data.get("vocabulary", []))

    def _get_path(self, receiver_name: str) -> str:
        # Sanitize receiver name for filename
        safe_name = receiver_name.lower()
        if safe_name == "helloworld":
            safe_name = "root"
        return os.path.join(self.storage_dir, f"{safe_name}.vocab")
