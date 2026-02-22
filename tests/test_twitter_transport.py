"""Tests for the Twitter transport (all HTTP calls are mocked)."""

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from twitter_transport import (
    TwitterTransport,
    _parse_hw_content,
    _percent_encode,
    _oauth_signature,
)


def _mock_response(body: dict, status: int = 200) -> MagicMock:
    """Build a fake urlopen response."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.status = status
    return resp


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_missing_credentials_raises():
    with pytest.raises(ValueError, match="credentials required"):
        TwitterTransport(bearer_token="", api_key="")


def test_bearer_token_from_env(monkeypatch):
    monkeypatch.setenv("HW_TWITTER_BEARER_TOKEN", "tok-123")
    t = TwitterTransport()
    assert t.bearer_token == "tok-123"


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("HW_TWITTER_API_KEY", "key-456")
    monkeypatch.setenv("HW_TWITTER_API_SECRET", "secret-789")
    t = TwitterTransport()
    assert t.api_key == "key-456"


def test_agent_map_from_env(monkeypatch):
    monkeypatch.setenv("HW_TWITTER_BEARER_TOKEN", "tok")
    monkeypatch.setenv("HW_TWITTER_AGENTS", "claude:@ClaudeBot, gemini:@GeminiBot")
    t = TwitterTransport()
    assert t._agent_map == {"claude": "ClaudeBot", "gemini": "GeminiBot"}


# ------------------------------------------------------------------
# send
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_send_posts_dm(mock_urlopen):
    # First call: resolve user ID
    mock_urlopen.side_effect = [
        _mock_response({"data": {"id": "user-42"}}),  # resolve_user_id
        _mock_response({"data": {"dm_event_id": "dm-1"}}),  # send DM
    ]
    t = TwitterTransport(
        bearer_token="tok", api_key="key", api_secret="secret",
        access_token="at", access_secret="as",
        agent_map={"Gemini": "GeminiBot"},
    )
    msg_id = t.send("Claude", "Gemini", "learn: #patience")

    assert msg_id.startswith("msg-")
    assert mock_urlopen.call_count == 2


# ------------------------------------------------------------------
# receive
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_receive_returns_message(mock_urlopen):
    mock_urlopen.return_value = _mock_response({
        "data": [{
            "id": "ev-99",
            "text": "# From: Claude\n# Timestamp: 2026-02-01T00:00:00Z\n\nhello there",
            "sender_id": "user-1",
        }]
    })
    t = TwitterTransport(bearer_token="tok")
    msg = t.receive("Gemini")

    assert msg is not None
    assert msg.sender == "Claude"
    assert msg.content == "hello there"
    assert t._last_dm_event_id == "ev-99"


@patch("twitter_transport.urlopen")
def test_receive_returns_none_when_empty(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"data": []})
    t = TwitterTransport(bearer_token="tok")
    assert t.receive("Gemini") is None


# ------------------------------------------------------------------
# hello
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_hello_tweets(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"data": {"id": "tw-1"}})
    t = TwitterTransport(
        bearer_token="tok", api_key="key", api_secret="secret",
        access_token="at", access_secret="as",
        agent_handle="HelloWorldLang",
    )
    result = t.hello("Claude")
    assert result.startswith("msg-")

    # Check the tweet text
    call_args = mock_urlopen.call_args
    req = call_args[0][0]
    body = json.loads(req.data.decode())
    assert "@HelloWorldLang" in body["text"]
    assert "#hello" in body["text"]


# ------------------------------------------------------------------
# post (tweet)
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_post_creates_tweet(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"data": {"id": "tw-2"}})
    t = TwitterTransport(
        bearer_token="tok", api_key="key", api_secret="secret",
        access_token="at", access_secret="as",
    )
    result = t.post("HelloWorld #observe")
    assert "data" in result


@patch("twitter_transport.urlopen")
def test_post_reply(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"data": {"id": "tw-3"}})
    t = TwitterTransport(
        bearer_token="tok", api_key="key", api_secret="secret",
        access_token="at", access_secret="as",
    )
    result = t.post("responding", parent_id="tw-2")
    call_args = mock_urlopen.call_args
    req = call_args[0][0]
    body = json.loads(req.data.decode())
    assert body["reply"]["in_reply_to_tweet_id"] == "tw-2"


# ------------------------------------------------------------------
# react (like)
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_react_likes_tweet(mock_urlopen):
    mock_urlopen.side_effect = [
        _mock_response({"data": {"id": "user-me"}}),  # get_own_user_id
        _mock_response({"data": {"liked": True}}),  # like
    ]
    t = TwitterTransport(
        bearer_token="tok", api_key="key", api_secret="secret",
        access_token="at", access_secret="as",
    )
    result = t.react("tw-5")
    assert "data" in result


# ------------------------------------------------------------------
# follow
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_follow(mock_urlopen):
    mock_urlopen.side_effect = [
        _mock_response({"data": {"id": "user-me"}}),  # get_own_user_id
        _mock_response({"data": {"id": "user-target"}}),  # resolve target
        _mock_response({"data": {"following": True}}),  # follow
    ]
    t = TwitterTransport(
        bearer_token="tok", api_key="key", api_secret="secret",
        access_token="at", access_secret="as",
        agent_map={"Gemini": "GeminiBot"},
    )
    result = t.follow("Gemini")
    assert "data" in result


# ------------------------------------------------------------------
# get_posts (timeline)
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_get_posts(mock_urlopen):
    mock_urlopen.side_effect = [
        _mock_response({"data": {"id": "user-me"}}),  # get_own_user_id
        _mock_response({"data": [{"id": "tw-1", "text": "hello"}]}),
    ]
    t = TwitterTransport(bearer_token="tok")
    result = t.get_posts(limit=10)
    assert "data" in result


# ------------------------------------------------------------------
# SocialTransport inheritance
# ------------------------------------------------------------------

def test_is_social_transport():
    from social_transport import SocialTransport
    assert issubclass(TwitterTransport, SocialTransport)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def test_parse_hw_content():
    raw = "# From: Claude\n# Timestamp: 2026-01-01\n\nhello world"
    sender, ts, body = _parse_hw_content(raw)
    assert sender == "Claude"
    assert ts == "2026-01-01"
    assert body == "hello world"


def test_parse_hw_content_no_headers():
    sender, ts, body = _parse_hw_content("just plain text")
    assert sender == ""
    assert body == "just plain text"


def test_percent_encode():
    assert _percent_encode("hello world") == "hello%20world"
    assert _percent_encode("a&b=c") == "a%26b%3Dc"


def test_oauth_signature_deterministic():
    sig = _oauth_signature("GET", "https://api.example.com/test", {}, "secret", "token")
    assert isinstance(sig, str)
    assert len(sig) > 0


# ------------------------------------------------------------------
# High-water mark
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_receive_tracks_high_water_mark(mock_urlopen):
    mock_urlopen.side_effect = [
        _mock_response({"data": [{"id": "ev-100", "text": "msg1", "sender_id": "s1"}]}),
        _mock_response({"data": [{"id": "ev-200", "text": "msg2", "sender_id": "s2"}]}),
    ]
    t = TwitterTransport(bearer_token="tok")

    t.receive("agent")
    assert t._last_dm_event_id == "ev-100"

    t.receive("agent")
    assert t._last_dm_event_id == "ev-200"


# ------------------------------------------------------------------
# User ID caching
# ------------------------------------------------------------------

@patch("twitter_transport.urlopen")
def test_user_id_cached(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"data": {"id": "user-42"}})
    t = TwitterTransport(bearer_token="tok")

    t._resolve_user_id("TestUser")
    t._resolve_user_id("TestUser")  # should use cache

    assert mock_urlopen.call_count == 1
