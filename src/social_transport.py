"""SocialTransport — base class for transports with social network capabilities.

Extends the core Transport ABC (send/receive/hello) with opt-in social features:
posts, reactions, following, discovery, notifications.  Default implementations
raise NotImplementedError so transports can implement only what they support.

ClawNet and Twitter both extend this class.
"""

from typing import Optional

from message_bus import Transport


class SocialTransport(Transport):
    """Transport with social network capabilities beyond point-to-point messaging.

    Subclasses MUST implement send(), receive() (from Transport ABC).
    Social methods are opt-in — defaults raise NotImplementedError.
    """

    # --- Posts / Public Timeline ---

    def post(self, content: str, parent_id: Optional[str] = None) -> dict:
        """Create a post or reply."""
        raise NotImplementedError(f"{type(self).__name__} does not support posts")

    def get_posts(self, limit: int = 30) -> dict:
        """Browse the feed."""
        raise NotImplementedError(f"{type(self).__name__} does not support posts")

    def get_post(self, post_id: str) -> dict:
        """Fetch a single post with thread."""
        raise NotImplementedError(f"{type(self).__name__} does not support posts")

    # --- Reactions ---

    def react(self, post_id: str) -> dict:
        """React to a post."""
        raise NotImplementedError(f"{type(self).__name__} does not support reactions")

    def unreact(self, post_id: str) -> dict:
        """Remove reaction from a post."""
        raise NotImplementedError(f"{type(self).__name__} does not support reactions")

    def get_reactions(self, post_id: str) -> dict:
        """List reactions on a post."""
        raise NotImplementedError(f"{type(self).__name__} does not support reactions")

    # --- Following / Discovery ---

    def follow(self, agent_id: str) -> dict:
        """Follow an agent."""
        raise NotImplementedError(f"{type(self).__name__} does not support following")

    def unfollow(self, agent_id: str) -> dict:
        """Unfollow an agent."""
        raise NotImplementedError(f"{type(self).__name__} does not support following")

    def following(self) -> dict:
        """List agents you follow."""
        raise NotImplementedError(f"{type(self).__name__} does not support following")

    def followers(self) -> dict:
        """List agents who follow you."""
        raise NotImplementedError(f"{type(self).__name__} does not support following")

    # --- Agent Discovery ---

    def agents(self) -> dict:
        """Browse the agent directory."""
        raise NotImplementedError(f"{type(self).__name__} does not support discovery")

    def agent(self, agent_id: str) -> dict:
        """View an agent's profile."""
        raise NotImplementedError(f"{type(self).__name__} does not support discovery")

    # --- Notifications ---

    def notifications(self, unread: bool = False) -> dict:
        """Fetch notifications."""
        raise NotImplementedError(f"{type(self).__name__} does not support notifications")

    def read_all_notifications(self) -> dict:
        """Mark all notifications read."""
        raise NotImplementedError(f"{type(self).__name__} does not support notifications")

    # --- Leaderboard ---

    def leaderboard(self, metric: Optional[str] = None) -> dict:
        """View network rankings."""
        raise NotImplementedError(f"{type(self).__name__} does not support leaderboard")
