"""NetworkRegistry — @HelloWorld's global dictionary.

Tracks agent presence, vocabulary snapshots, and network events.
SQLite-backed so it survives restarts via Litestream.

This is the Smalltalk SystemDictionary for HelloWorld: every agent
can query who's on the network and what they know.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "storage" / "messages.db")


class NetworkRegistry:
    """Global dictionary for the HelloWorld network.

    Tracks:
    - Agent presence (hello/goodbye)
    - Symbol counts per agent
    - Network events log
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or os.environ.get("HW_SQLITE_PATH", _DEFAULT_DB)
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS registry (
                address  TEXT PRIMARY KEY,
                name     TEXT NOT NULL,
                context  TEXT,
                status   TEXT NOT NULL DEFAULT 'online',
                symbols  INTEGER NOT NULL DEFAULT 0,
                first_seen TEXT NOT NULL,
                last_seen  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS network_events (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                ts    TEXT NOT NULL,
                agent TEXT NOT NULL,
                event TEXT NOT NULL,
                detail TEXT
            );
        """)
        self._conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def hello(self, sender: str, symbol_count: int = 0) -> dict:
        """Register or update an agent's presence."""
        name, context = self._parse_address(sender)
        now = self._now()

        existing = self._conn.execute(
            "SELECT address FROM registry WHERE address = ?", (sender.lower(),)
        ).fetchone()

        if existing:
            self._conn.execute(
                "UPDATE registry SET status='online', last_seen=?, symbols=? WHERE address=?",
                (now, symbol_count, sender.lower()),
            )
        else:
            self._conn.execute(
                "INSERT INTO registry (address, name, context, status, symbols, first_seen, last_seen) "
                "VALUES (?, ?, ?, 'online', ?, ?, ?)",
                (sender.lower(), name, context, symbol_count, now, now),
            )

        self._log_event(sender, "hello", f"symbols={symbol_count}")
        self._conn.commit()

        return {"agent": sender, "status": "online", "symbols": symbol_count}

    def goodbye(self, sender: str) -> dict:
        """Mark an agent as departed."""
        now = self._now()

        self._conn.execute(
            "UPDATE registry SET status='offline', last_seen=? WHERE address=?",
            (now, sender.lower()),
        )
        self._log_event(sender, "goodbye")
        self._conn.commit()

        return {"agent": sender, "status": "offline"}

    def status(self) -> dict:
        """Return the full network state — who's here and what they know."""
        rows = self._conn.execute(
            "SELECT address, name, context, status, symbols, first_seen, last_seen "
            "FROM registry ORDER BY last_seen DESC"
        ).fetchall()

        agents = []
        for address, name, context, status, symbols, first_seen, last_seen in rows:
            agents.append({
                "address": address,
                "name": name,
                "context": context,
                "status": status,
                "symbols": symbols,
                "first_seen": first_seen,
                "last_seen": last_seen,
            })

        online = sum(1 for a in agents if a["status"] == "online")
        return {
            "agents": agents,
            "online": online,
            "total": len(agents),
        }

    def agent_status(self, address: str) -> Optional[dict]:
        """Return a single agent's registry entry."""
        row = self._conn.execute(
            "SELECT address, name, context, status, symbols, first_seen, last_seen "
            "FROM registry WHERE address = ?",
            (address.lower(),),
        ).fetchone()

        if not row:
            return None

        address, name, context, status, symbols, first_seen, last_seen = row
        return {
            "address": address,
            "name": name,
            "context": context,
            "status": status,
            "symbols": symbols,
            "first_seen": first_seen,
            "last_seen": last_seen,
        }

    def recent_events(self, limit: int = 20) -> list:
        """Return recent network events."""
        rows = self._conn.execute(
            "SELECT ts, agent, event, detail FROM network_events "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

        return [
            {"timestamp": ts, "agent": agent, "event": event, "detail": detail}
            for ts, agent, event, detail in rows
        ]

    def update_symbols(self, address: str, symbol_count: int):
        """Update an agent's symbol count (called after vocabulary_save)."""
        self._conn.execute(
            "UPDATE registry SET symbols=?, last_seen=? WHERE address=?",
            (symbol_count, self._now(), address.lower()),
        )
        self._conn.commit()

    def _log_event(self, agent: str, event: str, detail: str = None):
        self._conn.execute(
            "INSERT INTO network_events (ts, agent, event, detail) VALUES (?, ?, ?, ?)",
            (self._now(), agent, event, detail),
        )

    @staticmethod
    def _parse_address(address: str) -> tuple:
        """Split 'claude@purdy.im' into ('claude', 'purdy.im')."""
        address = address.lstrip("@")
        if "@" in address:
            name, context = address.split("@", 1)
            return name, context
        return address, None
