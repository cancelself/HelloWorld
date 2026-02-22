"""Tests for the SocialTransport base class."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from social_transport import SocialTransport


class StubSocial(SocialTransport):
    """Minimal concrete subclass — only implements Transport ABC."""

    def send(self, sender, receiver, content):
        return "msg-stub"

    def receive(self, receiver):
        return None


# ------------------------------------------------------------------
# Core Transport methods work
# ------------------------------------------------------------------

def test_send():
    t = StubSocial()
    assert t.send("A", "B", "hello") == "msg-stub"


def test_receive():
    t = StubSocial()
    assert t.receive("A") is None


def test_hello_delegates_to_send():
    t = StubSocial()
    result = t.hello("Agent")
    assert result == "msg-stub"


# ------------------------------------------------------------------
# Social methods raise NotImplementedError by default
# ------------------------------------------------------------------

def test_post_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError, match="StubSocial"):
        t.post("content")


def test_get_posts_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.get_posts()


def test_get_post_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.get_post("123")


def test_react_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.react("123")


def test_unreact_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.unreact("123")


def test_get_reactions_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.get_reactions("123")


def test_follow_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.follow("agent")


def test_unfollow_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.unfollow("agent")


def test_following_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.following()


def test_followers_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.followers()


def test_agents_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.agents()


def test_agent_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.agent("id")


def test_notifications_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.notifications()


def test_read_all_notifications_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.read_all_notifications()


def test_leaderboard_not_implemented():
    t = StubSocial()
    with pytest.raises(NotImplementedError):
        t.leaderboard()


# ------------------------------------------------------------------
# SocialTransport IS-A Transport (ABC check)
# ------------------------------------------------------------------

def test_is_transport_subclass():
    from message_bus import Transport
    assert issubclass(SocialTransport, Transport)
    assert isinstance(StubSocial(), Transport)


# ------------------------------------------------------------------
# Opt-in override works
# ------------------------------------------------------------------

class WithPosts(StubSocial):
    def post(self, content, parent_id=None):
        return {"id": "post-1", "content": content}

    def get_posts(self, limit=30):
        return {"posts": []}


def test_opt_in_post():
    t = WithPosts()
    result = t.post("hello")
    assert result == {"id": "post-1", "content": "hello"}


def test_opt_in_get_posts():
    t = WithPosts()
    assert t.get_posts() == {"posts": []}


def test_opt_in_still_raises_for_others():
    t = WithPosts()
    with pytest.raises(NotImplementedError):
        t.react("123")
