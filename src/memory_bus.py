"""HelloWorld Memory Bus — per-agent store/recall backed by QMD.

Each agent gets its own memory directory under runtimes/<agent>/memory/.
Files are markdown with YAML frontmatter. QMD provides hybrid search
(BM25 + vector + LLM re-ranking) when installed; store/get work without it.

    from memory_bus import MemoryBus
    mem = MemoryBus("non_serviam")
    mem.store("severith prefers short messages", title="severith-style")
    mem.recall("how does severith communicate")
"""

import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

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


def _parse_frontmatter(text: str) -> Tuple[dict, str]:
    """Split YAML frontmatter from content. Simple line-based — no YAML lib.

    Returns (metadata_dict, content_after_frontmatter).
    If no frontmatter found, returns ({}, original_text).
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end is None:
        return {}, text

    meta = {}
    current_key = None
    current_list: Optional[list] = None

    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped:
            continue

        # List item under a key (e.g. "  - social")
        if stripped.startswith("- ") and current_key is not None and current_list is not None:
            current_list.append(stripped[2:].strip())
            continue

        # Key-value pair
        if ":" in stripped:
            # Flush previous list
            if current_key and current_list is not None:
                meta[current_key] = current_list

            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()

            if val:
                meta[key] = val
                current_key = key
                current_list = None
            else:
                # Start of a list or empty value
                current_key = key
                current_list = []

    # Flush final list
    if current_key and current_list is not None:
        meta[current_key] = current_list

    content = "\n".join(lines[end + 1:]).lstrip("\n")
    return meta, content


@dataclass
class MemoryEntry:
    """A parsed memory file with frontmatter metadata."""
    path: Path
    title: str
    created: Optional[str] = None
    updated: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    content: str = ""


class MemoryIndex:
    """Pure-Python structured queries over .hw/.md memory files."""

    def __init__(self, memory_dir: Path):
        self._memory_dir = memory_dir
        self._entries: Optional[List[MemoryEntry]] = None

    def refresh(self) -> None:
        """Re-scan directory and rebuild the index."""
        entries = []
        if not self._memory_dir.is_dir():
            self._entries = entries
            return

        for p in sorted(self._memory_dir.iterdir()):
            if p.suffix not in (".hw", ".md"):
                continue
            try:
                text = p.read_text()
            except OSError:
                continue
            meta, content = _parse_frontmatter(text)
            tags_raw = meta.get("tags", [])
            if isinstance(tags_raw, str):
                tags_raw = [t.strip() for t in tags_raw.split(",")]
            entries.append(MemoryEntry(
                path=p,
                title=meta.get("title", p.stem),
                created=meta.get("created"),
                updated=meta.get("updated"),
                tags=tags_raw,
                content=content,
            ))
        self._entries = entries

    def _ensure_loaded(self) -> List[MemoryEntry]:
        if self._entries is None:
            self.refresh()
        return self._entries  # type: ignore[return-value]

    def all(self) -> List[MemoryEntry]:
        """Return all memory entries."""
        return list(self._ensure_loaded())

    def titles(self) -> List[str]:
        """Quick listing of all memory titles."""
        return [e.title for e in self._ensure_loaded()]

    def by_tag(self, *tags: str) -> List[MemoryEntry]:
        """Return entries matching ALL given tags (AND)."""
        tag_set = set(tags)
        return [e for e in self._ensure_loaded() if tag_set <= set(e.tags)]

    def by_title(self, pattern: str) -> List[MemoryEntry]:
        """Return entries whose title matches pattern (substring or glob)."""
        lowered = pattern.lower()
        # If pattern contains glob chars, use fnmatch
        if any(c in pattern for c in "*?[]"):
            return [e for e in self._ensure_loaded()
                    if fnmatch.fnmatch(e.title.lower(), lowered)]
        # Otherwise substring match
        return [e for e in self._ensure_loaded()
                if lowered in e.title.lower()]

    def recent(self, n: int = 5) -> List[MemoryEntry]:
        """Return the n most recently created entries (by created desc)."""
        entries = self._ensure_loaded()
        # Sort by created descending; entries without created go last
        with_date = [(e, e.created or "") for e in entries]
        with_date.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in with_date[:n]]


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
        self._index: Optional[MemoryIndex] = None

    @property
    def memory_dir(self) -> Path:
        """Read BASE_DIR dynamically so monkey-patching in tests works."""
        return _memory_dir(self.agent_id)

    @property
    def index(self) -> MemoryIndex:
        """Lazily create a MemoryIndex for this agent's memory dir."""
        if self._index is None:
            self._index = MemoryIndex(self.memory_dir)
        return self._index

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
