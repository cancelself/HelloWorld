"""Twitter/X transport for the HelloWorld message bus.

Routes messages through the Twitter API v2.  DMs for point-to-point
messaging (send/receive), tweets for broadcast (post/hello).

Requires Twitter API credentials via environment variables or constructor:
  HW_TWITTER_BEARER_TOKEN  — read-only (mentions, timeline)
  HW_TWITTER_API_KEY       — OAuth 1.0a consumer key  (write)
  HW_TWITTER_API_SECRET    — OAuth 1.0a consumer secret
  HW_TWITTER_ACCESS_TOKEN  — OAuth 1.0a access token
  HW_TWITTER_ACCESS_SECRET — OAuth 1.0a access token secret

Agent-handle mapping:
  HW_TWITTER_AGENT_HANDLE  — this bot's Twitter handle
  HW_TWITTER_AGENTS        — receiver:handle pairs (claude:@ClaudeBot,gemini:@GeminiBot)
"""

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from message_bus import Message
from social_transport import SocialTransport

API_BASE = "https://api.twitter.com"
USER_AGENT = "HelloWorld/1.0"


def _percent_encode(s: str) -> str:
    """RFC 3986 percent-encoding."""
    return urllib.parse.quote(str(s), safe="")


def _oauth_signature(
    method: str,
    url: str,
    params: Dict[str, str],
    consumer_secret: str,
    token_secret: str,
) -> str:
    """Generate OAuth 1.0a HMAC-SHA1 signature."""
    sorted_params = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}"
        for k, v in sorted(params.items())
    )
    base_string = "&".join([
        method.upper(),
        _percent_encode(url),
        _percent_encode(sorted_params),
    ])
    signing_key = f"{_percent_encode(consumer_secret)}&{_percent_encode(token_secret)}"
    signature = hmac.new(
        signing_key.encode(), base_string.encode(), hashlib.sha1
    ).digest()
    return base64.b64encode(signature).decode()


def _oauth_header(
    method: str,
    url: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
    extra_params: Optional[Dict[str, str]] = None,
) -> str:
    """Build the Authorization header for OAuth 1.0a."""
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    all_params = {**oauth_params, **(extra_params or {})}
    oauth_params["oauth_signature"] = _oauth_signature(
        method, url, all_params, api_secret, access_secret
    )
    header_parts = ", ".join(
        f'{_percent_encode(k)}="{_percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


class TwitterTransport(SocialTransport):
    """HelloWorld transport over Twitter/X API v2.

    Point-to-point: DMs (send/receive)
    Broadcast: Tweets (post/hello)
    Social: likes (react), follows, timeline
    """

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
        agent_handle: Optional[str] = None,
        agent_map: Optional[Dict[str, str]] = None,
    ):
        self.bearer_token = bearer_token or os.environ.get("HW_TWITTER_BEARER_TOKEN", "")
        self.api_key = api_key or os.environ.get("HW_TWITTER_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("HW_TWITTER_API_SECRET", "")
        self.access_token = access_token or os.environ.get("HW_TWITTER_ACCESS_TOKEN", "")
        self.access_secret = access_secret or os.environ.get("HW_TWITTER_ACCESS_SECRET", "")
        self.agent_handle = agent_handle or os.environ.get("HW_TWITTER_AGENT_HANDLE", "")

        if not self.bearer_token and not self.api_key:
            raise ValueError(
                "Twitter credentials required — set HW_TWITTER_BEARER_TOKEN "
                "or HW_TWITTER_API_KEY + HW_TWITTER_API_SECRET"
            )

        # Agent name -> Twitter handle mapping
        self._agent_map: Dict[str, str] = agent_map or self._parse_agent_map()

        # High-water mark for DM polling
        self._last_dm_event_id: Optional[str] = None

        # Cache for user ID lookups
        self._user_id_cache: Dict[str, str] = {}
        self._own_user_id: Optional[str] = None

    def _parse_agent_map(self) -> Dict[str, str]:
        """Parse HW_TWITTER_AGENTS env var into {receiver: handle} dict."""
        raw = os.environ.get("HW_TWITTER_AGENTS", "")
        if not raw:
            return {}
        mapping = {}
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" in pair:
                name, handle = pair.split(":", 1)
                mapping[name.strip()] = handle.strip().lstrip("@")
        return mapping

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _bearer_request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """Issue a request with Bearer token auth (read-only)."""
        url = f"{API_BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.bearer_token}")
        req.add_header("User-Agent", USER_AGENT)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        resp = urlopen(req)
        return json.loads(resp.read().decode())

    def _oauth_request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """Issue a request with OAuth 1.0a auth (write operations)."""
        url = f"{API_BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, method=method)
        auth_header = _oauth_header(
            method, url,
            self.api_key, self.api_secret,
            self.access_token, self.access_secret,
        )
        req.add_header("Authorization", auth_header)
        req.add_header("User-Agent", USER_AGENT)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        resp = urlopen(req)
        return json.loads(resp.read().decode())

    def _get_own_user_id(self) -> str:
        """Get the authenticated user's Twitter ID."""
        if self._own_user_id:
            return self._own_user_id
        data = self._bearer_request("GET", "/2/users/me")
        self._own_user_id = data["data"]["id"]
        return self._own_user_id

    def _resolve_user_id(self, handle: str) -> str:
        """Resolve a Twitter handle to a user ID."""
        handle = handle.lstrip("@")
        if handle in self._user_id_cache:
            return self._user_id_cache[handle]
        data = self._bearer_request("GET", f"/2/users/by/username/{handle}")
        user_id = data["data"]["id"]
        self._user_id_cache[handle] = user_id
        return user_id

    def _receiver_to_handle(self, receiver: str) -> str:
        """Map a HelloWorld receiver name to a Twitter handle."""
        name = receiver.lstrip("@")
        if name in self._agent_map:
            return self._agent_map[name]
        # Fall back to receiver name as handle
        return name.lower()

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    def send(self, sender: str, receiver: str, content: str) -> str:
        """Send a DM to the receiver's Twitter account."""
        handle = self._receiver_to_handle(receiver)
        participant_id = self._resolve_user_id(handle)

        timestamp = datetime.now(timezone.utc).isoformat()
        hw_content = (
            f"# From: {sender}\n"
            f"# Timestamp: {timestamp}\n"
            f"\n"
            f"{content}"
        )

        self._oauth_request(
            "POST",
            f"/2/dm_conversations/with/{participant_id}/messages",
            {"text": hw_content},
        )

        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        return msg_id

    def receive(self, receiver: str) -> Optional[Message]:
        """Poll for new DMs since the last check."""
        path = "/2/dm_events?event_types=MessageCreate&max_results=1"
        if self._last_dm_event_id:
            path += f"&since_id={self._last_dm_event_id}"

        try:
            data = self._bearer_request("GET", path)
        except (HTTPError, URLError):
            return None

        events = data.get("data", [])
        if not events:
            return None

        event = events[0]
        self._last_dm_event_id = event.get("id", self._last_dm_event_id)

        text = event.get("text", "")
        sender, timestamp, body = _parse_hw_content(text)

        if not sender:
            sender_id = event.get("sender_id", "")
            sender = sender_id  # best effort without reverse lookup

        return Message(sender=sender, content=body, timestamp=timestamp)

    def hello(self, sender: str) -> str:
        """Tweet a #hello announcement."""
        mention = f"@{self.agent_handle} " if self.agent_handle else ""
        tweet_text = f"{mention}{sender} #hello"
        return self._tweet(tweet_text)

    # ------------------------------------------------------------------
    # Social: Posts (Tweets)
    # ------------------------------------------------------------------

    def post(self, content: str, parent_id: Optional[str] = None) -> dict:
        """Post a tweet, optionally as a reply."""
        body: dict = {"text": content}
        if parent_id:
            body["reply"] = {"in_reply_to_tweet_id": parent_id}
        return self._oauth_request("POST", "/2/tweets", body)

    def get_posts(self, limit: int = 30) -> dict:
        """Get the authenticated user's recent tweets."""
        user_id = self._get_own_user_id()
        return self._bearer_request(
            "GET", f"/2/users/{user_id}/tweets?max_results={min(limit, 100)}"
        )

    def get_post(self, post_id: str) -> dict:
        """Fetch a single tweet."""
        return self._bearer_request("GET", f"/2/tweets/{post_id}")

    # ------------------------------------------------------------------
    # Social: Reactions (Likes)
    # ------------------------------------------------------------------

    def react(self, post_id: str) -> dict:
        """Like a tweet."""
        user_id = self._get_own_user_id()
        return self._oauth_request(
            "POST", f"/2/users/{user_id}/likes", {"tweet_id": post_id}
        )

    def unreact(self, post_id: str) -> dict:
        """Unlike a tweet."""
        user_id = self._get_own_user_id()
        return self._oauth_request("DELETE", f"/2/users/{user_id}/likes/{post_id}")

    # ------------------------------------------------------------------
    # Social: Following
    # ------------------------------------------------------------------

    def follow(self, agent_id: str) -> dict:
        """Follow a Twitter user by handle or ID."""
        user_id = self._get_own_user_id()
        target_handle = self._receiver_to_handle(agent_id)
        target_id = self._resolve_user_id(target_handle)
        return self._oauth_request(
            "POST", f"/2/users/{user_id}/following", {"target_user_id": target_id}
        )

    def unfollow(self, agent_id: str) -> dict:
        """Unfollow a Twitter user."""
        user_id = self._get_own_user_id()
        target_handle = self._receiver_to_handle(agent_id)
        target_id = self._resolve_user_id(target_handle)
        return self._oauth_request("DELETE", f"/2/users/{user_id}/following/{target_id}")

    def following(self) -> dict:
        """List accounts the authenticated user follows."""
        user_id = self._get_own_user_id()
        return self._bearer_request("GET", f"/2/users/{user_id}/following")

    def followers(self) -> dict:
        """List the authenticated user's followers."""
        user_id = self._get_own_user_id()
        return self._bearer_request("GET", f"/2/users/{user_id}/followers")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tweet(self, text: str) -> str:
        """Post a tweet and return a msg_id."""
        self._oauth_request("POST", "/2/tweets", {"text": text})
        return f"msg-{uuid.uuid4().hex[:8]}"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _parse_hw_content(raw: str) -> tuple:
    """Extract (sender, timestamp, body) from HelloWorld-formatted content."""
    sender = ""
    timestamp = ""
    content_start = 0

    lines = raw.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# From:"):
            sender = line.split(":", 1)[1].strip()
        elif line.startswith("# Timestamp:"):
            timestamp = line.split(":", 1)[1].strip()
        elif not line.startswith("#") and line.strip():
            content_start = i
            break

    body = "\n".join(lines[content_start:]).strip()
    return sender, timestamp, body
