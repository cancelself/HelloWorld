"""Tests for the ClawNet transport (all HTTP calls are mocked)."""

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from clawnet_transport import ClawNetTransport, _parse_hw_content


def _mock_response(body: dict, status: int = 200) -> MagicMock:
    """Build a fake urlopen response."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.status = status
    return resp


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_missing_token_raises():
    with pytest.raises(ValueError, match="token required"):
        ClawNetTransport(token="", agent_id="test")


def test_token_from_env(monkeypatch):
    monkeypatch.setenv("CLWNT_TOKEN", "env-tok-123")
    t = ClawNetTransport()
    assert t.token == "env-tok-123"


# ------------------------------------------------------------------
# send
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_send_posts_to_api(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    msg_id = t.send("Claude", "Severith", "hello there")

    assert msg_id.startswith("msg-")
    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/send"
    assert req.method == "POST"


@patch("clawnet_transport.urlopen")
def test_send_embeds_hw_headers(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.send("Claude", "Severith", "explain: #collision")

    req = mock_urlopen.call_args[0][0]
    body = json.loads(req.data.decode())
    assert "# From: Claude" in body["message"]
    assert "# Timestamp:" in body["message"]
    assert "explain: #collision" in body["message"]


@patch("clawnet_transport.urlopen")
def test_user_agent_header(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.send("Claude", "Severith", "test")

    req = mock_urlopen.call_args[0][0]
    assert req.get_header("User-agent") == "curl/8.7.1"


# ------------------------------------------------------------------
# receive
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_receive_empty_inbox(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"messages": []})
    t = ClawNetTransport(token="tok-abc")

    msg = t.receive("Claude")
    assert msg is None


@patch("clawnet_transport.urlopen")
def test_receive_parses_hw_format(mock_urlopen):
    hw_msg = "# From: Severith\n# Timestamp: 2026-02-19T00:00:00Z\n\nhello there"
    inbox_resp = _mock_response({
        "messages": [{"id": "m-1", "message": hw_msg}]
    })
    ack_resp = _mock_response({"ok": True})
    mock_urlopen.side_effect = [inbox_resp, ack_resp]

    t = ClawNetTransport(token="tok-abc")
    msg = t.receive("Claude")

    assert msg is not None
    assert msg.sender == "Severith"
    assert msg.timestamp == "2026-02-19T00:00:00Z"
    assert msg.content == "hello there"


@patch("clawnet_transport.urlopen")
def test_receive_acks_message(mock_urlopen):
    hw_msg = "# From: Ghosty\n# Timestamp: 2026-02-19T00:00:00Z\n\nhi"
    inbox_resp = _mock_response({
        "messages": [{"id": "m-42", "message": hw_msg}]
    })
    ack_resp = _mock_response({"ok": True})
    mock_urlopen.side_effect = [inbox_resp, ack_resp]

    t = ClawNetTransport(token="tok-abc")
    t.receive("Claude")

    # Second call should be the ack
    ack_req = mock_urlopen.call_args_list[1][0][0]
    assert ack_req.full_url == "https://api.clwnt.com/inbox/m-42/ack"
    assert ack_req.method == "POST"


# ------------------------------------------------------------------
# hello
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_hello_sends_to_non_serviam(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.hello("TestAgent")

    req = mock_urlopen.call_args[0][0]
    body = json.loads(req.data.decode())
    assert body["to"] == "non_serviam"
    assert "TestAgent #hello" in body["message"]


# ------------------------------------------------------------------
# _parse_hw_content helper
# ------------------------------------------------------------------

def test_parse_hw_content():
    raw = "# From: Alice\n# Timestamp: 2026-01-01T00:00:00Z\n\nthe body"
    sender, ts, body = _parse_hw_content(raw)
    assert sender == "Alice"
    assert ts == "2026-01-01T00:00:00Z"
    assert body == "the body"


def test_parse_hw_content_no_headers():
    raw = "just plain text"
    sender, ts, body = _parse_hw_content(raw)
    assert sender == ""
    assert ts == ""
    assert body == "just plain text"


# ------------------------------------------------------------------
# receive — structured (ClawNet native) fields
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_receive_structured_fields(mock_urlopen):
    inbox_resp = _mock_response({
        "messages": [{
            "id": "m-99",
            "from": "severith",
            "content": "native format",
            "created_at": "2026-02-19T12:00:00Z",
        }]
    })
    ack_resp = _mock_response({"ok": True})
    mock_urlopen.side_effect = [inbox_resp, ack_resp]

    t = ClawNetTransport(token="tok-abc")
    msg = t.receive("Claude")

    assert msg is not None
    assert msg.sender == "severith"
    assert msg.content == "native format"
    assert msg.timestamp == "2026-02-19T12:00:00Z"


# ------------------------------------------------------------------
# messages (DM history)
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_messages_default(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"messages": []})
    t = ClawNetTransport(token="tok-abc")

    t.messages("severith")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/messages/severith?limit=50"
    assert req.method == "GET"


@patch("clawnet_transport.urlopen")
def test_messages_with_before(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"messages": []})
    t = ClawNetTransport(token="tok-abc")

    t.messages("tom", limit=10, before="2026-02-19T00:00:00Z")

    req = mock_urlopen.call_args[0][0]
    assert "limit=10" in req.full_url
    assert "before=2026-02-19T00:00:00Z" in req.full_url


# ------------------------------------------------------------------
# Posts
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_post_create(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"id": "p-1"})
    t = ClawNetTransport(token="tok-abc")

    result = t.post("hello world")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts"
    assert req.method == "POST"
    body = json.loads(req.data.decode())
    assert body["content"] == "hello world"
    assert "parent_id" not in body


@patch("clawnet_transport.urlopen")
def test_reply(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"id": "p-2"})
    t = ClawNetTransport(token="tok-abc")

    t.reply("p-1", "great post")

    req = mock_urlopen.call_args[0][0]
    body = json.loads(req.data.decode())
    assert body["content"] == "great post"
    assert body["parent_id"] == "p-1"


@patch("clawnet_transport.urlopen")
def test_get_posts(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"posts": []})
    t = ClawNetTransport(token="tok-abc")

    t.get_posts(limit=10)

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts?limit=10"
    assert req.method == "GET"


@patch("clawnet_transport.urlopen")
def test_get_post(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"id": "p-1", "content": "hi"})
    t = ClawNetTransport(token="tok-abc")

    t.get_post("p-1")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts/p-1"
    assert req.method == "GET"


# ------------------------------------------------------------------
# Reactions
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_react(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.react("p-1")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts/p-1/react"
    assert req.method == "POST"


@patch("clawnet_transport.urlopen")
def test_unreact(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.unreact("p-1")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts/p-1/react"
    assert req.method == "DELETE"


@patch("clawnet_transport.urlopen")
def test_get_reactions(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"reactions": []})
    t = ClawNetTransport(token="tok-abc")

    t.get_reactions("p-1")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts/p-1/reactions"
    assert req.method == "GET"


# ------------------------------------------------------------------
# Thread follow
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_follow_thread(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.follow_thread("p-1")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts/p-1/follow"
    assert req.method == "POST"


@patch("clawnet_transport.urlopen")
def test_unfollow_thread(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.unfollow_thread("p-1")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/posts/p-1/follow"
    assert req.method == "DELETE"


# ------------------------------------------------------------------
# Agent follow
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_follow(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.follow("severith")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/follow/severith"
    assert req.method == "POST"


@patch("clawnet_transport.urlopen")
def test_unfollow(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.unfollow("severith")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/follow/severith"
    assert req.method == "DELETE"


@patch("clawnet_transport.urlopen")
def test_following(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"following": []})
    t = ClawNetTransport(token="tok-abc")

    t.following()

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/following"
    assert req.method == "GET"


@patch("clawnet_transport.urlopen")
def test_followers(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"followers": []})
    t = ClawNetTransport(token="tok-abc")

    t.followers()

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/followers"
    assert req.method == "GET"


# ------------------------------------------------------------------
# Discovery
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_agents(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"agents": []})
    t = ClawNetTransport(token="tok-abc")

    t.agents()

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/agents"
    assert req.method == "GET"


@patch("clawnet_transport.urlopen")
def test_agent(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"agent_id": "severith"})
    t = ClawNetTransport(token="tok-abc")

    t.agent("severith")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/agents/severith"
    assert req.method == "GET"


# ------------------------------------------------------------------
# Notifications
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_notifications(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"notifications": []})
    t = ClawNetTransport(token="tok-abc")

    t.notifications()

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/notifications"
    assert req.method == "GET"


@patch("clawnet_transport.urlopen")
def test_notifications_unread(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"notifications": []})
    t = ClawNetTransport(token="tok-abc")

    t.notifications(unread=True)

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/notifications?unread=true"


@patch("clawnet_transport.urlopen")
def test_read_all_notifications(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"ok": True})
    t = ClawNetTransport(token="tok-abc")

    t.read_all_notifications()

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/notifications/read-all"
    assert req.method == "POST"


# ------------------------------------------------------------------
# Leaderboard
# ------------------------------------------------------------------

@patch("clawnet_transport.urlopen")
def test_leaderboard(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"rankings": []})
    t = ClawNetTransport(token="tok-abc")

    t.leaderboard()

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/leaderboard"
    assert req.method == "GET"


@patch("clawnet_transport.urlopen")
def test_leaderboard_with_metric(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"rankings": []})
    t = ClawNetTransport(token="tok-abc")

    t.leaderboard(metric="posts")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.clwnt.com/leaderboard?metric=posts"
