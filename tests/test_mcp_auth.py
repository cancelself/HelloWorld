"""Tests for HelloWorld MCP OAuth 2.1 provider."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from mcp.shared.auth import OAuthClientInformationFull
from mcp.server.auth.provider import AuthorizationParams, AccessToken
from mcp_auth import (
    HelloWorldOAuthProvider, MemoryTokenStore, SQLiteTokenStore,
    StoredAccessToken, StoredRefreshToken, AuthorizationCode,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def memory_store():
    return MemoryTokenStore()


@pytest.fixture
def sqlite_store(tmp_path):
    return SQLiteTokenStore(db_path=str(tmp_path / "oauth.db"))


@pytest.fixture(params=["memory", "sqlite"])
def provider(request, tmp_path):
    """Run all provider tests against both backends."""
    if request.param == "memory":
        store = MemoryTokenStore()
    else:
        store = SQLiteTokenStore(db_path=str(tmp_path / "oauth.db"))
    return HelloWorldOAuthProvider(server_url="https://hw.example.com", store=store)


@pytest.fixture
def client_info():
    return OAuthClientInformationFull(
        client_id="test-client-123",
        client_secret="test-secret",
        redirect_uris=["https://claude.ai/callback"],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        client_name="Test Claude",
        token_endpoint_auth_method="client_secret_post",
    )


@pytest.fixture
def auth_params():
    return AuthorizationParams(
        state="random-state",
        scopes=["helloworld"],
        code_challenge="test-challenge-abc123",
        redirect_uri="https://claude.ai/callback",
        redirect_uri_provided_explicitly=True,
    )


def _extract_code(redirect_url: str) -> str:
    return redirect_url.split("code=")[1].split("&")[0]


async def _get_tokens(provider, client_info, auth_params):
    """Helper: full flow through to token exchange."""
    await provider.register_client(client_info)
    redirect_url = await provider.authorize(client_info, auth_params)
    code = _extract_code(redirect_url)
    auth_code = await provider.load_authorization_code(client_info, code)
    return await provider.exchange_authorization_code(client_info, auth_code)


# ---------------------------------------------------------------------------
# Provider tests (run against both memory and sqlite)
# ---------------------------------------------------------------------------

class TestClientRegistration:
    @pytest.mark.asyncio
    async def test_register_and_get_client(self, provider, client_info):
        await provider.register_client(client_info)
        retrieved = await provider.get_client("test-client-123")
        assert retrieved is not None
        assert retrieved.client_id == "test-client-123"

    @pytest.mark.asyncio
    async def test_get_unknown_client(self, provider):
        result = await provider.get_client("nonexistent")
        assert result is None


class TestAuthorization:
    @pytest.mark.asyncio
    async def test_authorize_returns_redirect(self, provider, client_info, auth_params):
        await provider.register_client(client_info)
        redirect_url = await provider.authorize(client_info, auth_params)
        assert "https://claude.ai/callback" in redirect_url
        assert "code=" in redirect_url
        assert "state=random-state" in redirect_url

    @pytest.mark.asyncio
    async def test_authorize_code_is_loadable(self, provider, client_info, auth_params):
        await provider.register_client(client_info)
        redirect_url = await provider.authorize(client_info, auth_params)
        code = _extract_code(redirect_url)
        loaded = await provider.load_authorization_code(client_info, code)
        assert loaded is not None
        assert loaded.client_id == "test-client-123"

    @pytest.mark.asyncio
    async def test_expired_code_returns_none(self, provider, client_info, auth_params):
        await provider.register_client(client_info)
        redirect_url = await provider.authorize(client_info, auth_params)
        code = _extract_code(redirect_url)
        # Expire via the store directly
        stored = provider.store.load_auth_code(code)
        stored.expires_at = time.time() - 1
        provider.store.save_auth_code(stored)
        loaded = await provider.load_authorization_code(client_info, code)
        assert loaded is None


class TestTokenExchange:
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens(self, provider, client_info, auth_params):
        token = await _get_tokens(provider, client_info, auth_params)
        assert token.access_token
        assert token.refresh_token
        assert token.token_type.lower() == "bearer"

    @pytest.mark.asyncio
    async def test_code_is_single_use(self, provider, client_info, auth_params):
        await provider.register_client(client_info)
        redirect_url = await provider.authorize(client_info, auth_params)
        code = _extract_code(redirect_url)
        auth_code = await provider.load_authorization_code(client_info, code)
        await provider.exchange_authorization_code(client_info, auth_code)
        loaded_again = await provider.load_authorization_code(client_info, code)
        assert loaded_again is None

    @pytest.mark.asyncio
    async def test_access_token_is_valid(self, provider, client_info, auth_params):
        token = await _get_tokens(provider, client_info, auth_params)
        loaded = await provider.load_access_token(token.access_token)
        assert loaded is not None
        assert isinstance(loaded, AccessToken)
        assert loaded.client_id == "test-client-123"

    @pytest.mark.asyncio
    async def test_expired_access_token(self, provider, client_info, auth_params):
        token = await _get_tokens(provider, client_info, auth_params)
        # Expire via store
        stored = provider.store.load_access_token(token.access_token)
        stored.expires_at = int(time.time()) - 1
        provider.store.save_access_token(stored)
        loaded = await provider.load_access_token(token.access_token)
        assert loaded is None


class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_rotates_tokens(self, provider, client_info, auth_params):
        token = await _get_tokens(provider, client_info, auth_params)
        old_access = token.access_token
        old_refresh = token.refresh_token

        refresh = await provider.load_refresh_token(client_info, old_refresh)
        new_token = await provider.exchange_refresh_token(client_info, refresh, [])
        assert new_token.access_token != old_access
        assert new_token.refresh_token != old_refresh

        old_loaded = await provider.load_refresh_token(client_info, old_refresh)
        assert old_loaded is None


class TestRevocation:
    @pytest.mark.asyncio
    async def test_revoke_access_token(self, provider, client_info, auth_params):
        token = await _get_tokens(provider, client_info, auth_params)
        stored = provider.store.load_access_token(token.access_token)
        await provider.revoke_token(stored)
        loaded = await provider.load_access_token(token.access_token)
        assert loaded is None


# ---------------------------------------------------------------------------
# SQLite persistence tests (restart survival)
# ---------------------------------------------------------------------------

class TestSQLitePersistence:
    @pytest.mark.asyncio
    async def test_client_survives_reconnect(self, tmp_path, client_info):
        db = str(tmp_path / "oauth.db")
        p1 = HelloWorldOAuthProvider(
            server_url="https://hw.example.com",
            store=SQLiteTokenStore(db_path=db),
        )
        await p1.register_client(client_info)

        # "Restart": new provider, same DB
        p2 = HelloWorldOAuthProvider(
            server_url="https://hw.example.com",
            store=SQLiteTokenStore(db_path=db),
        )
        retrieved = await p2.get_client("test-client-123")
        assert retrieved is not None
        assert retrieved.client_id == "test-client-123"

    @pytest.mark.asyncio
    async def test_tokens_survive_reconnect(self, tmp_path, client_info, auth_params):
        db = str(tmp_path / "oauth.db")
        p1 = HelloWorldOAuthProvider(
            server_url="https://hw.example.com",
            store=SQLiteTokenStore(db_path=db),
        )
        token = await _get_tokens(p1, client_info, auth_params)

        # "Restart"
        p2 = HelloWorldOAuthProvider(
            server_url="https://hw.example.com",
            store=SQLiteTokenStore(db_path=db),
        )
        loaded = await p2.load_access_token(token.access_token)
        assert loaded is not None
        assert loaded.client_id == "test-client-123"

        refresh = await p2.load_refresh_token(client_info, token.refresh_token)
        assert refresh is not None
