"""Tests for the HelloWorld Config layer."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, _parse_env_file, _discover_helloworld_src


# --- _parse_env_file ---


def test_parse_env_file_basic():
    tmp = Path(tempfile.mktemp())
    tmp.write_text("FOO=bar\nBAZ=qux\n")
    try:
        result = _parse_env_file(tmp)
        assert result == {"FOO": "bar", "BAZ": "qux"}
    finally:
        tmp.unlink()


def test_parse_env_file_skips_comments_and_blanks():
    tmp = Path(tempfile.mktemp())
    tmp.write_text("# comment\n\nKEY=val\n  # another\n")
    try:
        result = _parse_env_file(tmp)
        assert result == {"KEY": "val"}
    finally:
        tmp.unlink()


def test_parse_env_file_missing():
    result = _parse_env_file(Path("/nonexistent/.env"))
    assert result == {}


def test_parse_env_file_equals_in_value():
    tmp = Path(tempfile.mktemp())
    tmp.write_text("TOKEN=abc=def=ghi\n")
    try:
        result = _parse_env_file(tmp)
        assert result == {"TOKEN": "abc=def=ghi"}
    finally:
        tmp.unlink()


# --- Config defaults ---


def test_config_defaults():
    cfg = Config()
    assert cfg.transport == "file"
    assert cfg.helloworld_src is None
    assert cfg.agent_id == ""
    assert cfg.clwnt_token is None


def test_config_typed_properties():
    cfg = Config({
        "HELLOWORLD_SRC": "/tmp/hw/src",
        "CLWNT_AGENT_ID": "test_agent",
        "CLWNT_TOKEN": "tok_123",
        "HW_TRANSPORT": "clawnet",
        "BASE_DIR": "/tmp/runtimes",
    })
    assert cfg.helloworld_src == Path("/tmp/hw/src")
    assert cfg.agent_id == "test_agent"
    assert cfg.clwnt_token == "tok_123"
    assert cfg.transport == "clawnet"
    assert cfg.base_dir == Path("/tmp/runtimes")


def test_config_get_arbitrary_key():
    cfg = Config({"CUSTOM_KEY": "custom_val"})
    assert cfg.get("CUSTOM_KEY") == "custom_val"
    assert cfg.get("MISSING", "default") == "default"


# --- validate ---


def test_validate_missing_src():
    cfg = Config()
    try:
        cfg.validate()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "HELLOWORLD_SRC" in str(e)


def test_validate_valid_src():
    # Use the real HelloWorld/src as validation target
    real_src = str(Path(__file__).parent.parent / "src")
    cfg = Config({"HELLOWORLD_SRC": real_src})
    cfg.validate()  # Should not raise


# --- bootstrap ---


def test_bootstrap_loads_env_file():
    tmp = Path(tempfile.mktemp())
    hw_src = str(Path(__file__).parent.parent / "src")
    tmp.write_text(f"HELLOWORLD_SRC={hw_src}\nCLWNT_AGENT_ID=test\n")
    try:
        # Clear env so bootstrap reads from file
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HELLOWORLD_SRC", None)
            os.environ.pop("CLWNT_AGENT_ID", None)
            cfg = Config.bootstrap(env_path=tmp)
        assert cfg.helloworld_src == Path(hw_src)
        assert cfg.agent_id == "test"
    finally:
        tmp.unlink()


def test_bootstrap_env_overrides_file():
    tmp = Path(tempfile.mktemp())
    hw_src = str(Path(__file__).parent.parent / "src")
    tmp.write_text(f"HELLOWORLD_SRC={hw_src}\nCLWNT_AGENT_ID=from_file\n")
    try:
        with patch.dict(os.environ, {"CLWNT_AGENT_ID": "from_env"}, clear=False):
            cfg = Config.bootstrap(env_path=tmp)
        assert cfg.agent_id == "from_env"
    finally:
        tmp.unlink()
        os.environ.pop("CLWNT_AGENT_ID", None)


def test_bootstrap_adds_to_sys_path():
    hw_src = str(Path(__file__).parent.parent / "src")
    tmp = Path(tempfile.mktemp())
    tmp.write_text(f"HELLOWORLD_SRC={hw_src}\n")
    try:
        # Remove from sys.path if present
        original = sys.path[:]
        if hw_src in sys.path:
            sys.path.remove(hw_src)
        cfg = Config.bootstrap(env_path=tmp)
        assert hw_src in sys.path
        # Restore
        sys.path[:] = original
    finally:
        tmp.unlink()


def test_bootstrap_no_env_path():
    """bootstrap(None) should still work — just skips .env loading."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("HELLOWORLD_SRC", None)
        cfg = Config.bootstrap(env_path=None)
    # May or may not discover src depending on cwd, but should not crash
    assert isinstance(cfg, Config)


# --- discovery ---


def test_discover_from_env_var(monkeypatch):
    hw_src = str(Path(__file__).parent.parent / "src")
    monkeypatch.setenv("HELLOWORLD_SRC", hw_src)
    result = _discover_helloworld_src()
    assert result == Path(hw_src)


def test_discover_returns_none_when_nothing_found(monkeypatch, tmp_path):
    monkeypatch.delenv("HELLOWORLD_SRC", raising=False)
    monkeypatch.chdir(tmp_path)
    # Patch home to avoid finding ~/.helloworld/src
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = _discover_helloworld_src()
    assert result is None
