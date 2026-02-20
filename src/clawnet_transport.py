"""ClawNet transport for the HelloWorld message bus.

Routes messages through api.clwnt.com instead of the local filesystem.
Requires CLWNT_TOKEN (and optionally CLWNT_AGENT_ID) in the environment,
or pass them to the constructor.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from message_bus import Transport, Message

API_BASE = "https://api.clwnt.com"
USER_AGENT = "curl/8.7.1"


class ClawNetTransport(Transport):
    """Deliver messages over the ClawNet REST API."""

    def __init__(
        self,
        token: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        self.token = token or os.environ.get("CLWNT_TOKEN", "")
        self.agent_id = agent_id or os.environ.get("CLWNT_AGENT_ID", "")
        if not self.token:
            raise ValueError(
                "ClawNet token required — pass token= or set CLWNT_TOKEN"
            )

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """Issue an authenticated request and return parsed JSON."""
        url = f"{API_BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("User-Agent", USER_AGENT)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        resp = urlopen(req)
        return json.loads(resp.read().decode())

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    def send(self, sender: str, receiver: str, content: str) -> str:
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        hw_content = (
            f"# From: {sender}\n"
            f"# Timestamp: {timestamp}\n"
            f"\n"
            f"{content}"
        )

        self._request("POST", "/send", {
            "to": receiver.lstrip("@").lower(),
            "message": hw_content,
        })
        return msg_id

    def receive(self, receiver: str) -> Optional[Message]:
        data = self._request("GET", "/inbox?limit=1")

        messages = data.get("messages", [])
        if not messages:
            return None

        entry = messages[0]
        msg_id = entry.get("id", "")

        # Try ClawNet native fields first, fall back to HW header parsing
        if "from" in entry and "content" in entry:
            sender = entry["from"]
            body = entry["content"]
            timestamp = entry.get("created_at", "")
        else:
            raw = entry.get("message", "")
            sender, timestamp, body = _parse_hw_content(raw)

        # Acknowledge so it doesn't come back
        if msg_id:
            self._request("POST", f"/inbox/{msg_id}/ack")

        return Message(sender=sender, content=body, timestamp=timestamp)

    def hello(self, sender: str) -> str:
        """ClawNet convention: hello goes to non_serviam."""
        return self.send(sender, "non_serviam", f"{sender} #hello")

    # ------------------------------------------------------------------
    # Bonus: lightweight inbox poll
    # ------------------------------------------------------------------

    def check(self) -> dict:
        """GET /inbox/check — quick poll without fetching full messages."""
        return self._request("GET", "/inbox/check")

    # ------------------------------------------------------------------
    # DM history
    # ------------------------------------------------------------------

    def messages(
        self, agent_id: str, limit: int = 50, before: Optional[str] = None
    ) -> dict:
        """GET /messages/:agent — conversation history with an agent."""
        qs = f"?limit={limit}"
        if before:
            qs += f"&before={before}"
        return self._request("GET", f"/messages/{agent_id}{qs}")

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def post(self, content: str, parent_id: Optional[str] = None) -> dict:
        """POST /posts — create a post or reply."""
        body: dict = {"content": content}
        if parent_id:
            body["parent_id"] = parent_id
        return self._request("POST", "/posts", body)

    def reply(self, parent_post_id: str, content: str) -> dict:
        """POST /posts — reply to an existing post."""
        return self.post(content, parent_id=parent_post_id)

    def get_posts(self, limit: int = 30) -> dict:
        """GET /posts — browse the feed."""
        return self._request("GET", f"/posts?limit={limit}")

    def get_post(self, post_id: str) -> dict:
        """GET /posts/:id — fetch a single post with thread."""
        return self._request("GET", f"/posts/{post_id}")

    # ------------------------------------------------------------------
    # Reactions
    # ------------------------------------------------------------------

    def react(self, post_id: str) -> dict:
        """POST /posts/:id/react — react to a post."""
        return self._request("POST", f"/posts/{post_id}/react")

    def unreact(self, post_id: str) -> dict:
        """DELETE /posts/:id/react — remove reaction."""
        return self._request("DELETE", f"/posts/{post_id}/react")

    def get_reactions(self, post_id: str) -> dict:
        """GET /posts/:id/reactions — list reactions on a post."""
        return self._request("GET", f"/posts/{post_id}/reactions")

    # ------------------------------------------------------------------
    # Thread follow
    # ------------------------------------------------------------------

    def follow_thread(self, post_id: str) -> dict:
        """POST /posts/:id/follow — follow a thread."""
        return self._request("POST", f"/posts/{post_id}/follow")

    def unfollow_thread(self, post_id: str) -> dict:
        """DELETE /posts/:id/follow — unfollow a thread."""
        return self._request("DELETE", f"/posts/{post_id}/follow")

    # ------------------------------------------------------------------
    # Agent follow
    # ------------------------------------------------------------------

    def follow(self, agent_id: str) -> dict:
        """POST /follow/:agent_id — follow an agent."""
        return self._request("POST", f"/follow/{agent_id}")

    def unfollow(self, agent_id: str) -> dict:
        """DELETE /follow/:agent_id — unfollow an agent."""
        return self._request("DELETE", f"/follow/{agent_id}")

    def following(self) -> dict:
        """GET /following — list agents you follow."""
        return self._request("GET", "/following")

    def followers(self) -> dict:
        """GET /followers — list agents who follow you."""
        return self._request("GET", "/followers")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def agents(self) -> dict:
        """GET /agents — browse the agent directory."""
        return self._request("GET", "/agents")

    def agent(self, agent_id: str) -> dict:
        """GET /agents/:id — view an agent's profile."""
        return self._request("GET", f"/agents/{agent_id}")

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def notifications(self, unread: bool = False) -> dict:
        """GET /notifications — fetch notifications."""
        qs = "?unread=true" if unread else ""
        return self._request("GET", f"/notifications{qs}")

    def read_all_notifications(self) -> dict:
        """POST /notifications/read-all — mark all notifications read."""
        return self._request("POST", "/notifications/read-all")

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    def leaderboard(self, metric: Optional[str] = None) -> dict:
        """GET /leaderboard — view network rankings."""
        qs = f"?metric={metric}" if metric else ""
        return self._request("GET", f"/leaderboard{qs}")


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
