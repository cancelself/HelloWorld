"""HelloWorld Config — layered configuration with auto-discovery.

Resolves agent settings from defaults, .env files, and environment variables.
Discovers HELLOWORLD_SRC automatically so agents don't need hand-edited .env.

    from config import Config
    cfg = Config.bootstrap()
    print(cfg.helloworld_src)
"""

import os
import sys
from pathlib import Path
from typing import Optional


# Signature file that identifies a HelloWorld src directory
_SIGNATURE = "dispatcher.py"


def _parse_env_file(path: Path) -> dict:
    """Parse a .env file into a dict. Same logic bus.py uses — no deps."""
    result = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip()
    return result


def _discover_helloworld_src() -> Optional[Path]:
    """Try to find HelloWorld/src by searching standard locations."""
    # 1. Env var (already set)
    env_val = os.environ.get("HELLOWORLD_SRC")
    if env_val:
        p = Path(env_val)
        if p.is_dir() and (p / _SIGNATURE).exists():
            return p

    # 2. ~/.helloworld/src
    home_path = Path.home() / ".helloworld" / "src"
    if home_path.is_dir() and (home_path / _SIGNATURE).exists():
        return home_path

    # 3. Walk parents from cwd looking for HelloWorld/src/dispatcher.py
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        candidate = parent / "HelloWorld" / "src"
        try:
            if candidate.is_dir() and (candidate / _SIGNATURE).exists():
                return candidate
        except OSError:
            continue
        # Also check sibling dirs (e.g. cancelself/HelloWorld/src)
        try:
            if parent.is_dir():
                for child in parent.iterdir():
                    if child.is_dir():
                        candidate = child / "HelloWorld" / "src"
                        if candidate.is_dir() and (candidate / _SIGNATURE).exists():
                            return candidate
        except OSError:
            continue

    return None


class Config:
    """Layered configuration: defaults → .env file → environment variables."""

    _DEFAULTS = {
        "HW_TRANSPORT": "file",
    }

    def __init__(self, values: Optional[dict] = None):
        self._values = dict(self._DEFAULTS)
        if values:
            self._values.update(values)

    # --- Typed properties ---

    @property
    def helloworld_src(self) -> Optional[Path]:
        val = self._values.get("HELLOWORLD_SRC")
        return Path(val) if val else None

    @property
    def agent_id(self) -> str:
        return self._values.get("CLWNT_AGENT_ID", "")

    @property
    def base_dir(self) -> Optional[Path]:
        val = self._values.get("BASE_DIR")
        return Path(val) if val else None

    @property
    def transport(self) -> str:
        return self._values.get("HW_TRANSPORT", "file")

    @property
    def clwnt_token(self) -> Optional[str]:
        return self._values.get("CLWNT_TOKEN")

    def get(self, key: str, default=None):
        return self._values.get(key, default)

    # --- Validation ---

    def validate(self) -> None:
        """Raise RuntimeError if required paths are missing."""
        src = self.helloworld_src
        if not src or not src.is_dir():
            raise RuntimeError(
                f"HELLOWORLD_SRC not found or not a directory: {src}"
            )
        if not (src / _SIGNATURE).exists():
            raise RuntimeError(
                f"HELLOWORLD_SRC missing {_SIGNATURE}: {src}"
            )

    # --- Bootstrap ---

    @classmethod
    def bootstrap(cls, env_path: Optional[Path] = None) -> "Config":
        """Load .env, discover HELLOWORLD_SRC, wire sys.path, return Config.

        Args:
            env_path: Path to .env file. If None, skips .env loading.
        """
        values = dict(cls._DEFAULTS)

        # Layer 1: .env file
        if env_path is not None:
            env_vars = _parse_env_file(env_path)
            values.update(env_vars)
            # Also set in os.environ (setdefault — don't clobber)
            for k, v in env_vars.items():
                os.environ.setdefault(k, v)

        # Layer 2: environment variables override .env
        for key in list(values.keys()) + [
            "HELLOWORLD_SRC", "CLWNT_TOKEN", "CLWNT_AGENT_ID",
            "HW_TRANSPORT", "BASE_DIR",
        ]:
            env_val = os.environ.get(key)
            if env_val is not None:
                values[key] = env_val

        # Layer 3: auto-discover HELLOWORLD_SRC if not set
        if not values.get("HELLOWORLD_SRC"):
            discovered = _discover_helloworld_src()
            if discovered:
                values["HELLOWORLD_SRC"] = str(discovered)

        cfg = cls(values)

        # Wire sys.path if we have a valid src
        src = cfg.helloworld_src
        if src and src.is_dir():
            src_str = str(src)
            if src_str not in sys.path:
                sys.path.insert(0, src_str)

        return cfg
