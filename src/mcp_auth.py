"""HelloWorld MCP OAuth 2.1 Provider.

Self-contained OAuth authorization server for the HelloWorld MCP server.
Supports dynamic client registration (required by Claude.ai) and a simple
browser-based approval flow.

Storage backends: in-memory (testing) or SQLite (production).
"""

import json
import secrets
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlencode

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken


@dataclass
class AuthorizationCode:
    code: str
    client_id: str
    redirect_uri: str
    code_challenge: str
    scopes: list
    expires_at: float
    redirect_uri_provided_explicitly: bool = True


@dataclass
class StoredRefreshToken:
    token: str
    client_id: str
    scopes: list


@dataclass
class StoredAccessToken:
    token: str
    client_id: str
    scopes: list
    expires_at: int


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------

class MemoryTokenStore:
    """In-memory store for testing."""

    def __init__(self):
        self._clients: Dict[str, dict] = {}
        self._auth_codes: Dict[str, AuthorizationCode] = {}
        self._access_tokens: Dict[str, StoredAccessToken] = {}
        self._refresh_tokens: Dict[str, StoredRefreshToken] = {}

    def save_client(self, client_id: str, data: dict):
        self._clients[client_id] = data

    def load_client(self, client_id: str) -> Optional[dict]:
        return self._clients.get(client_id)

    def save_auth_code(self, code: AuthorizationCode):
        self._auth_codes[code.code] = code

    def load_auth_code(self, code: str) -> Optional[AuthorizationCode]:
        return self._auth_codes.get(code)

    def delete_auth_code(self, code: str):
        self._auth_codes.pop(code, None)

    def save_access_token(self, token: StoredAccessToken):
        self._access_tokens[token.token] = token

    def load_access_token(self, token: str) -> Optional[StoredAccessToken]:
        return self._access_tokens.get(token)

    def delete_access_token(self, token: str):
        self._access_tokens.pop(token, None)

    def save_refresh_token(self, token: StoredRefreshToken):
        self._refresh_tokens[token.token] = token

    def load_refresh_token(self, token: str) -> Optional[StoredRefreshToken]:
        return self._refresh_tokens.get(token)

    def delete_refresh_token(self, token: str):
        self._refresh_tokens.pop(token, None)


class SQLiteTokenStore:
    """SQLite-backed persistent store.

    Safe for single-process use (WAL mode, same-thread check disabled
    so the async event loop can use it from any coroutine).
    """

    def __init__(self, db_path: str = "storage/oauth.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        c = self._conn
        c.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS auth_codes (
                code TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                code_challenge TEXT NOT NULL,
                scopes TEXT NOT NULL,
                expires_at REAL NOT NULL,
                redirect_uri_provided_explicitly INTEGER NOT NULL DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS access_tokens (
                token TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                scopes TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                scopes TEXT NOT NULL
            )
        """)
        c.commit()

    def save_client(self, client_id: str, data: dict):
        self._conn.execute(
            "INSERT OR REPLACE INTO clients (client_id, data) VALUES (?, ?)",
            (client_id, json.dumps(data)),
        )
        self._conn.commit()

    def load_client(self, client_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT data FROM clients WHERE client_id = ?", (client_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def save_auth_code(self, code: AuthorizationCode):
        self._conn.execute(
            "INSERT OR REPLACE INTO auth_codes "
            "(code, client_id, redirect_uri, code_challenge, scopes, expires_at, redirect_uri_provided_explicitly) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code.code, code.client_id, code.redirect_uri, code.code_challenge,
             json.dumps(code.scopes), code.expires_at,
             1 if code.redirect_uri_provided_explicitly else 0),
        )
        self._conn.commit()

    def load_auth_code(self, code: str) -> Optional[AuthorizationCode]:
        row = self._conn.execute(
            "SELECT code, client_id, redirect_uri, code_challenge, scopes, expires_at, "
            "redirect_uri_provided_explicitly FROM auth_codes WHERE code = ?",
            (code,),
        ).fetchone()
        if not row:
            return None
        return AuthorizationCode(
            code=row[0], client_id=row[1], redirect_uri=row[2],
            code_challenge=row[3], scopes=json.loads(row[4]),
            expires_at=row[5], redirect_uri_provided_explicitly=bool(row[6]),
        )

    def delete_auth_code(self, code: str):
        self._conn.execute("DELETE FROM auth_codes WHERE code = ?", (code,))
        self._conn.commit()

    def save_access_token(self, token: StoredAccessToken):
        self._conn.execute(
            "INSERT OR REPLACE INTO access_tokens (token, client_id, scopes, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token.token, token.client_id, json.dumps(token.scopes), token.expires_at),
        )
        self._conn.commit()

    def load_access_token(self, token: str) -> Optional[StoredAccessToken]:
        row = self._conn.execute(
            "SELECT token, client_id, scopes, expires_at FROM access_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        if not row:
            return None
        return StoredAccessToken(
            token=row[0], client_id=row[1], scopes=json.loads(row[2]), expires_at=row[3],
        )

    def delete_access_token(self, token: str):
        self._conn.execute("DELETE FROM access_tokens WHERE token = ?", (token,))
        self._conn.commit()

    def save_refresh_token(self, token: StoredRefreshToken):
        self._conn.execute(
            "INSERT OR REPLACE INTO refresh_tokens (token, client_id, scopes) "
            "VALUES (?, ?, ?)",
            (token.token, token.client_id, json.dumps(token.scopes)),
        )
        self._conn.commit()

    def load_refresh_token(self, token: str) -> Optional[StoredRefreshToken]:
        row = self._conn.execute(
            "SELECT token, client_id, scopes FROM refresh_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        if not row:
            return None
        return StoredRefreshToken(
            token=row[0], client_id=row[1], scopes=json.loads(row[2]),
        )

    def delete_refresh_token(self, token: str):
        self._conn.execute("DELETE FROM refresh_tokens WHERE token = ?", (token,))
        self._conn.commit()


# ---------------------------------------------------------------------------
# OAuth Provider
# ---------------------------------------------------------------------------

class HelloWorldOAuthProvider:
    """OAuth 2.1 provider for HelloWorld MCP.

    Flow:
    1. Claude.ai registers as a client (dynamic registration)
    2. Claude.ai redirects user to /authorize
    3. User hits the authorize endpoint, server auto-approves and redirects back
    4. Claude.ai exchanges auth code for tokens

    Pass store=SQLiteTokenStore(path) for persistence across restarts,
    or store=MemoryTokenStore() for testing.
    """

    def __init__(self, server_url: str, token_expiry: int = 3600,
                 store=None):
        self.server_url = server_url.rstrip("/")
        self.token_expiry = token_expiry
        self.store = store or MemoryTokenStore()

    async def get_client(self, client_id: str) -> Optional[OAuthClientInformationFull]:
        data = self.store.load_client(client_id)
        if data is None:
            return None
        return OAuthClientInformationFull(**data)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self.store.save_client(client_info.client_id, client_info.model_dump(mode="json"))

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        code = secrets.token_urlsafe(20)

        self.store.save_auth_code(AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=str(params.redirect_uri),
            code_challenge=params.code_challenge,
            scopes=params.scopes or [],
            expires_at=time.time() + 300,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
        ))

        query = {"code": code}
        if params.state:
            query["state"] = params.state
        redirect = str(params.redirect_uri)
        separator = "&" if "?" in redirect else "?"
        return f"{redirect}{separator}{urlencode(query)}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> Optional[AuthorizationCode]:
        auth_code = self.store.load_auth_code(authorization_code)
        if auth_code is None:
            return None
        if auth_code.client_id != client.client_id:
            return None
        if time.time() > auth_code.expires_at:
            self.store.delete_auth_code(authorization_code)
            return None
        return auth_code

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        self.store.delete_auth_code(authorization_code.code)

        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + self.token_expiry

        self.store.save_access_token(StoredAccessToken(
            token=access_token, client_id=client.client_id,
            scopes=authorization_code.scopes, expires_at=expires_at,
        ))
        self.store.save_refresh_token(StoredRefreshToken(
            token=refresh_token, client_id=client.client_id,
            scopes=authorization_code.scopes,
        ))

        return OAuthToken(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.token_expiry,
            refresh_token=refresh_token,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> Optional[StoredRefreshToken]:
        stored = self.store.load_refresh_token(refresh_token)
        if stored and stored.client_id == client.client_id:
            return stored
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: StoredRefreshToken,
        scopes: list,
    ) -> OAuthToken:
        self.store.delete_refresh_token(refresh_token.token)

        new_access = secrets.token_urlsafe(32)
        new_refresh = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + self.token_expiry
        effective_scopes = scopes if scopes else refresh_token.scopes

        self.store.save_access_token(StoredAccessToken(
            token=new_access, client_id=client.client_id,
            scopes=effective_scopes, expires_at=expires_at,
        ))
        self.store.save_refresh_token(StoredRefreshToken(
            token=new_refresh, client_id=client.client_id,
            scopes=effective_scopes,
        ))

        return OAuthToken(
            access_token=new_access,
            token_type="bearer",
            expires_in=self.token_expiry,
            refresh_token=new_refresh,
            scope=" ".join(effective_scopes) if effective_scopes else None,
        )

    async def load_access_token(self, token: str) -> Optional[AccessToken]:
        stored = self.store.load_access_token(token)
        if stored is None:
            return None
        if stored.expires_at and time.time() > stored.expires_at:
            self.store.delete_access_token(token)
            return None
        return AccessToken(
            token=stored.token, client_id=stored.client_id,
            scopes=stored.scopes, expires_at=stored.expires_at,
        )

    async def revoke_token(self, token) -> None:
        if isinstance(token, StoredAccessToken):
            self.store.delete_access_token(token.token)
        elif isinstance(token, StoredRefreshToken):
            self.store.delete_refresh_token(token.token)
