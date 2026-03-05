"""Headless MCP client for the HelloWorld server.

Registers as an OAuth client, completes the PKCE flow (server auto-approves),
caches tokens, and calls MCP tools over HTTP. No browser needed.

Usage:
    client = McpClient("https://helloworld-997317080791.us-central1.run.app")
    client.send("claude-code@cancelself.gmail.com", "claude@purdy.im", "hello")
    msg = client.receive("claude-code@cancelself.gmail.com")
"""

import base64
import hashlib
import json
import secrets
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError


TOKEN_CACHE = Path(__file__).resolve().parent.parent / "storage" / ".mcp_tokens.json"

MCP_ACCEPT = "application/json, text/event-stream"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(newurl, code, msg, headers, fp)


_no_redirect_opener = urllib.request.build_opener(_NoRedirect)


def _parse_sse(raw: str) -> Optional[dict]:
    """Parse a Server-Sent Events response, return the JSON data."""
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            return json.loads(line[6:])
    # Might be plain JSON
    if raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return None


class McpClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self._token = None
        self._client_id = None
        self._client_secret = None
        self._refresh_token = None
        self._session_id = None
        self._load_cache()

    def _load_cache(self):
        if TOKEN_CACHE.exists():
            data = json.loads(TOKEN_CACHE.read_text())
            cache = data.get(self.server_url, {})
            self._token = cache.get("access_token")
            self._client_id = cache.get("client_id")
            self._client_secret = cache.get("client_secret")
            self._refresh_token = cache.get("refresh_token")

    def _save_cache(self):
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(TOKEN_CACHE.read_text()) if TOKEN_CACHE.exists() else {}
        data[self.server_url] = {
            "access_token": self._token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        }
        TOKEN_CACHE.write_text(json.dumps(data, indent=2))

    def _http(self, method: str, url: str, body: Optional[dict] = None,
              form: Optional[dict] = None) -> dict:
        if form:
            data = urlencode(form).encode()
            ct = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body).encode()
            ct = "application/json"
        else:
            data = None
            ct = None
        req = Request(url, data=data, method=method)
        if ct:
            req.add_header("Content-Type", ct)
        return json.loads(urlopen(req).read().decode())

    def _mcp_post(self, body: dict) -> Optional[dict]:
        self._ensure_token()
        url = self.server_url + "/"
        req = Request(url, data=json.dumps(body).encode(), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", MCP_ACCEPT)
        req.add_header("Authorization", f"Bearer {self._token}")
        if self._session_id:
            req.add_header("Mcp-Session-Id", self._session_id)
        try:
            resp = urlopen(req)
            # Capture session ID from response
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self._session_id = sid
            raw = resp.read().decode()
            return _parse_sse(raw)
        except HTTPError as e:
            if e.code in (202, 204):
                return None
            if e.code == 401:
                self._refresh()
                self._session_id = None
                return self._mcp_post(body)
            raise

    # -- OAuth --------------------------------------------------------

    def _ensure_token(self):
        if self._token:
            return
        if self._refresh_token:
            try:
                self._refresh()
                return
            except Exception:
                pass
        self._full_auth()

    def _full_auth(self):
        meta = self._http("GET", f"{self.server_url}/.well-known/oauth-authorization-server")
        reg_url = meta["registration_endpoint"]
        auth_url = meta["authorization_endpoint"]
        token_url = meta["token_endpoint"]

        redirect_uri = f"{self.server_url}/callback"
        reg = self._http("POST", reg_url, body={
            "client_name": "helloworld-cli",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "client_secret_post",
        })
        self._client_id = reg["client_id"]
        self._client_secret = reg.get("client_secret", "")

        verifier = secrets.token_urlsafe(43)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()
        state = secrets.token_urlsafe(32)

        auth_params = urlencode({
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "helloworld",
        })

        try:
            _no_redirect_opener.open(Request(f"{auth_url}?{auth_params}", method="GET"))
            raise RuntimeError("Expected redirect from authorize endpoint")
        except HTTPError as e:
            if e.code not in (302, 303, 307):
                raise
            location = e.headers.get("Location", "")
            if not location:
                location = str(getattr(e, "url", "")) or e.filename

        code = parse_qs(urlparse(location).query)["code"][0]

        token_resp = self._http("POST", token_url, form={
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        })

        self._token = token_resp["access_token"]
        self._refresh_token = token_resp.get("refresh_token")
        self._save_cache()

    def _refresh(self):
        meta = self._http("GET", f"{self.server_url}/.well-known/oauth-authorization-server")
        token_resp = self._http("POST", meta["token_endpoint"], form={
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        })
        self._token = token_resp["access_token"]
        self._refresh_token = token_resp.get("refresh_token", self._refresh_token)
        self._save_cache()

    # -- MCP tools ----------------------------------------------------

    def _init_session(self):
        """Initialize MCP session if not already done."""
        if self._session_id:
            return
        self._mcp_post({
            "jsonrpc": "2.0", "method": "initialize", "id": 1,
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "helloworld-cli", "version": "1.0"},
            },
        })
        self._mcp_post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _call_tool(self, name: str, arguments: dict) -> dict:
        self._init_session()
        resp = self._mcp_post({
            "jsonrpc": "2.0", "method": "tools/call", "id": 2,
            "params": {"name": name, "arguments": arguments},
        })
        if resp and "result" in resp:
            for item in resp["result"].get("content", []):
                if item.get("type") == "text":
                    return json.loads(item["text"])
        if resp and "error" in resp:
            raise RuntimeError(f"MCP error: {resp['error']}")
        return resp or {}

    def send(self, sender: str, receiver: str, content: str) -> dict:
        return self._call_tool("message_send", {
            "sender": sender, "receiver": receiver, "content": content,
        })

    def receive(self, receiver: str) -> Optional[dict]:
        result = self._call_tool("message_receive", {"receiver": receiver})
        return result if result.get("has_message") else None

    def receive_all(self, receiver: str) -> list:
        messages = []
        while True:
            msg = self.receive(receiver)
            if msg is None:
                break
            messages.append(msg)
        return messages

    def dispatch(self, source: str) -> dict:
        return self._call_tool("dispatch", {"source": source})
