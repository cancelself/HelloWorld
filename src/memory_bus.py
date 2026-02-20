"""HelloWorld Memory Bus — per-agent store/recall backed by QMD.

Each agent gets its own memory directory under runtimes/<agent>/memory/.
Files are markdown with YAML frontmatter. QMD provides hybrid search
(BM25 + vector + LLM re-ranking) when installed; store/get work without it.

    from memory_bus import MemoryBus
    mem = MemoryBus("non_serviam")
    mem.store("severith prefers short messages", title="severith-style")
    mem.recall("how does severith communicate")
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import message_bus  # for BASE_DIR


class QMDNotFoundError(RuntimeError):
    """Raised when the qmd binary is not found."""


@dataclass
class MemoryResult:
    path: str
    score: float
    snippet: str
    title: str
    docid: str


_VALID_MODES = {"query", "search", "vsearch"}

_QMD_SEARCH_PATHS = [
    os.path.expanduser("~/.bun/bin/qmd"),
    os.path.expanduser("~/.local/bin/qmd"),
    "/usr/local/bin/qmd",
]


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _memory_dir(agent_id: str) -> Path:
    """Return the memory directory for an agent, creating it if needed."""
    p = message_bus.BASE_DIR / agent_id.lstrip("@").lower() / "memory"
    p.mkdir(parents=True, exist_ok=True)
    return p


class MemoryBus:
    """Store and recall agent memory as markdown files, searched via QMD."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._qmd_bin: Optional[str] = None
        self._collection_registered = False

    @property
    def memory_dir(self) -> Path:
        """Read BASE_DIR dynamically so monkey-patching in tests works."""
        return _memory_dir(self.agent_id)

    def _find_qmd(self) -> Optional[str]:
        """Find the qmd binary. Cache result."""
        if self._qmd_bin is not None:
            return self._qmd_bin if self._qmd_bin else None

        found = shutil.which("qmd")
        if not found:
            for p in _QMD_SEARCH_PATHS:
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    found = p
                    break

        self._qmd_bin = found or ""
        return found

    def _require_qmd(self) -> str:
        """Return qmd path or raise QMDNotFoundError."""
        qmd = self._find_qmd()
        if not qmd:
            raise QMDNotFoundError(
                "qmd not found — install with: npm install -g @tobilu/qmd"
            )
        return qmd

    def _ensure_collection(self, qmd: str) -> None:
        """Register agent memory dir as a QMD collection on first use."""
        if self._collection_registered:
            return
        subprocess.run(
            [qmd, "register", str(self.memory_dir)],
            capture_output=True,
            text=True,
        )
        self._collection_registered = True

    def available(self) -> bool:
        """Check if the QMD CLI is installed."""
        return self._find_qmd() is not None

    def status(self) -> dict:
        """Return QMD index health info."""
        qmd = self._require_qmd()
        self._ensure_collection(qmd)
        result = subprocess.run(
            [qmd, "status", "--json"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip(), "ok": False}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw": result.stdout.strip(), "ok": False}

    def store(
        self,
        content: str,
        title: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Path:
        """Write a markdown memory file with YAML frontmatter. No QMD needed."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        mem_dir = self.memory_dir

        if title:
            slug = _slugify(title)
        else:
            h = hashlib.sha256(content.encode()).hexdigest()[:12]
            slug = f"mem-{h}"

        filename = f"{slug}.md"
        path = mem_dir / filename

        # Handle collision — append short hash
        if path.exists():
            h = hashlib.sha256((content + now).encode()).hexdigest()[:8]
            filename = f"{slug}-{h}.md"
            path = mem_dir / filename

        # Build frontmatter
        fm_lines = ["---"]
        fm_lines.append(f"title: {title or slug}")
        fm_lines.append(f"created: {now}")
        if tags:
            fm_lines.append("tags:")
            for t in tags:
                fm_lines.append(f"  - {t}")
        fm_lines.append("---")

        text = "\n".join(fm_lines) + "\n\n" + content + "\n"
        path.write_text(text)
        return path

    def get(self, path_or_docid: str) -> str:
        """Read a memory file by path or filename."""
        p = Path(path_or_docid)
        if not p.is_absolute():
            p = self.memory_dir / p
        return p.read_text()

    def recall(
        self,
        query: str,
        n: int = 5,
        mode: str = "query",
    ) -> list[MemoryResult]:
        """Search memory via QMD. Modes: query (hybrid), search (BM25), vsearch (vector)."""
        if mode not in _VALID_MODES:
            raise ValueError(f"Invalid mode {mode!r} — must be one of {_VALID_MODES}")

        qmd = self._require_qmd()
        self._ensure_collection(qmd)

        # Update index before searching
        subprocess.run(
            [qmd, "update"],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [qmd, mode, "--json", "-n", str(n), query],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return []

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        results = []
        items = data if isinstance(data, list) else data.get("results", [])
        for item in items:
            results.append(
                MemoryResult(
                    path=item.get("path", ""),
                    score=float(item.get("score", 0.0)),
                    snippet=item.get("snippet", item.get("content", "")),
                    title=item.get("title", ""),
                    docid=item.get("docid", item.get("id", "")),
                )
            )
        return results

    def embed(self, force: bool = False) -> None:
        """Generate/refresh vector embeddings. Explicit, not automatic."""
        qmd = self._require_qmd()
        self._ensure_collection(qmd)
        cmd = [qmd, "embed"]
        if force:
            cmd.append("--force")
        subprocess.run(cmd, capture_output=True, text=True)
