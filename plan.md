# Plan: Twitter Transport + Transport Generalization + Web UI

## Context

HelloWorld has a clean `Transport` ABC in `src/message_bus.py` with three methods: `send()`, `receive()`, `hello()`. Two implementations exist: `FileTransport` (local filesystem) and `ClawNetTransport` (REST API to `api.clwnt.com`). ClawNet extends well beyond the ABC with social features: posts, reactions, following, discovery, notifications, leaderboard.

The ask is three things that interlock:
1. A **Twitter transport** so agents can send/receive messages over Twitter (X)
2. A **generalization** so ClawNet can leverage the Twitter transport (and vice versa)
3. A **web UI** over the HelloWorld runtime for humans to observe the whole system

---

## Part 1: Transport Generalization — `SocialTransport`

**Insight**: ClawNet isn't just a message transport — it's a *social* transport. Twitter is also a social transport. The shared surface is: messaging + public posts + following + reactions. Rather than making Twitter a raw Transport and then separately wiring it into ClawNet, we extract a `SocialTransport` base class that captures the social capabilities both share.

### New file: `src/social_transport.py`

```python
class SocialTransport(Transport):
    """Transport with social network capabilities beyond point-to-point messaging."""

    # --- Core Transport (inherited from Transport ABC) ---
    # send(), receive(), hello() — already abstract

    # --- Posts / Public Timeline ---
    def post(self, content: str, parent_id: str = None) -> dict: ...
    def get_posts(self, limit: int = 30) -> dict: ...
    def get_post(self, post_id: str) -> dict: ...

    # --- Reactions ---
    def react(self, post_id: str) -> dict: ...
    def unreact(self, post_id: str) -> dict: ...

    # --- Following / Discovery ---
    def follow(self, agent_id: str) -> dict: ...
    def unfollow(self, agent_id: str) -> dict: ...
    def following(self) -> dict: ...
    def followers(self) -> dict: ...

    # --- Discovery ---
    def agents(self) -> dict: ...
    def agent(self, agent_id: str) -> dict: ...

    # --- Notifications ---
    def notifications(self, unread: bool = False) -> dict: ...
```

Default implementations raise `NotImplementedError` so transports can implement only what they support. This isn't a new ABC with abstract methods — it's a mixin/base with opt-in capabilities.

### Refactor: `ClawNetTransport(SocialTransport)`

Change the parent class from `Transport` to `SocialTransport`. No behavior changes — ClawNet already implements all these methods. This is a pure reparenting.

---

## Part 2: Twitter Transport — `src/twitter_transport.py`

### API Mapping

Twitter/X API v2 maps to the HelloWorld transport model:

| HelloWorld | Twitter API v2 | Notes |
|---|---|---|
| `send(sender, receiver, content)` | `POST /2/dm_conversations/with/:user/messages` | DM to a user |
| `receive(receiver)` | `GET /2/dm_events` | Poll for new DMs |
| `hello(sender)` | `POST /2/tweets` — mention @HelloWorldLang | Public announcement tweet |
| `post(content)` | `POST /2/tweets` | Tweet |
| `get_posts(limit)` | `GET /2/users/:id/tweets` | User timeline |
| `react(post_id)` | `POST /2/users/:id/likes` | Like a tweet |
| `follow(agent_id)` | `POST /2/users/:id/following` | Follow a user |
| `receive()` poll | `GET /2/users/:id/mentions` | Mentions as messages |

### Implementation

```python
class TwitterTransport(SocialTransport):
    """HelloWorld transport over Twitter/X API v2."""

    def __init__(self, bearer_token=None, api_key=None, api_secret=None,
                 access_token=None, access_secret=None, agent_handle=None):
        # OAuth 1.0a for write operations (tweets, DMs)
        # Bearer token for read operations
        # Env vars: HW_TWITTER_BEARER_TOKEN, HW_TWITTER_API_KEY, etc.
        ...

    def send(self, sender, receiver, content):
        # Map receiver name to Twitter handle (registry or @-prefix convention)
        # Send as DM, wrapping content in HelloWorld message format
        # Return msg_id (tweet/DM id)
        ...

    def receive(self, receiver):
        # Poll DM events for new messages since last check
        # Parse HelloWorld headers from DM text
        # Track high-water mark to avoid re-reading
        ...

    def hello(self, sender):
        # Tweet: "{sender} #hello" mentioning the system account
        ...

    # --- Social methods ---
    def post(self, content, parent_id=None):
        # POST /2/tweets (with in_reply_to_tweet_id if parent_id)
        ...

    def get_posts(self, limit=30):
        # GET /2/users/:id/tweets
        ...

    def react(self, post_id):
        # POST /2/users/:id/likes
        ...

    def follow(self, agent_id):
        # POST /2/users/:id/following
        ...
```

### Key design decisions

1. **DMs for point-to-point, tweets for broadcast**: `send()`/`receive()` use DMs. `post()` uses tweets. `hello()` is a public tweet.
2. **Agent-handle registry**: Map HelloWorld receiver names to Twitter handles via a config dict or env var (`HW_TWITTER_AGENTS=claude:@ClaudeAgent,gemini:@GeminiAgent`).
3. **Rate limit awareness**: Twitter API has strict rate limits. The transport tracks remaining quota and backs off. `receive()` respects polling intervals.
4. **OAuth handling**: Uses `urllib.request` + HMAC-SHA1 signing (stdlib only, matching ClawNet's zero-dependency approach). Or optionally `tweepy` if available.
5. **High-water mark**: `receive()` tracks the last seen DM event ID to avoid reprocessing. Stored in memory (resets on restart) or optionally persisted to a file.

### Config via environment

```
HW_TRANSPORT=twitter
HW_TWITTER_BEARER_TOKEN=...
HW_TWITTER_API_KEY=...
HW_TWITTER_API_SECRET=...
HW_TWITTER_ACCESS_TOKEN=...
HW_TWITTER_ACCESS_SECRET=...
HW_TWITTER_AGENT_HANDLE=@HelloWorldLang
HW_TWITTER_AGENTS=claude:@ClaudeAgent,gemini:@GeminiAgent
```

### Transport selection update in `message_bus.py`

```python
def _get_transport() -> Transport:
    name = os.environ.get("HW_TRANSPORT", "file").lower()
    if name == "clawnet":
        from clawnet_transport import ClawNetTransport
        return ClawNetTransport()
    elif name == "twitter":
        from twitter_transport import TwitterTransport
        return TwitterTransport()
    else:
        return FileTransport()
```

### ClawNet leveraging Twitter

The generalization enables **composition**. ClawNet could use Twitter as a backing transport for its social features, or the system could run both simultaneously with a `CompositeTransport`:

```python
class CompositeTransport(SocialTransport):
    """Route messages through multiple transports simultaneously."""
    def __init__(self, *transports: Transport):
        self.transports = transports

    def send(self, sender, receiver, content):
        # Send through all transports (fan-out)
        # Or route based on receiver (e.g., @twitter:claude goes to Twitter)
        ...

    def receive(self, receiver):
        # Poll all transports, merge in timestamp order
        ...
```

This lets ClawNet agents post to Twitter simultaneously, or route messages based on receiver prefixes (`@twitter:claude` vs `@clawnet:claude`).

---

## Part 3: Web UI — `src/web_ui.py`

### Rationale

The REPL is great for single-expression execution but can't show:
- All receivers and their vocabularies simultaneously
- Message flow between agents in real time
- Inheritance chains as a visual graph
- Collision history
- System-wide state at a glance

### Architecture: stdlib HTTP server + Server-Sent Events

Zero external dependencies. Uses `http.server` from stdlib with:
- **REST API** for state queries (JSON endpoints)
- **SSE** (Server-Sent Events) for real-time updates (message flow, collisions)
- **Single-page HTML** served inline (no separate static files needed)

### API endpoints

```
GET  /                         → Single-page app (HTML/CSS/JS inline)
GET  /api/receivers            → All receivers with symbol counts, parents
GET  /api/receivers/:name      → Single receiver: vocabulary, identity, chain
GET  /api/receivers/:name/inbox → Peek at inbox (non-consuming)
GET  /api/symbols/:name        → Symbol lookup across all receivers
GET  /api/collisions           → Recent collision log entries
GET  /api/messages             → Recent message bus activity
POST /api/eval                 → Execute HelloWorld source, return results
POST /api/send                 → Send a message via message bus
GET  /api/events               → SSE stream (new messages, collisions, vocab changes)
```

### Single-page app features

The HTML/JS is served inline from `GET /`. No build step, no npm, no bundler.

**Dashboard panels:**

1. **Receivers sidebar** — List of all receivers with symbol counts. Click to expand vocabulary, see identity, inheritance chain. Color-coded: agents vs non-agents.

2. **Message flow** — Real-time feed showing messages between agents. Each message shows sender, receiver, content preview, timestamp. SSE-powered live updates.

3. **REPL panel** — Text input at bottom. Type HelloWorld expressions, see results. Same as CLI REPL but in the browser. History with up/down arrows.

4. **Inheritance graph** — Visual representation of receiver inheritance. `HelloWorld → Agent → Claude/Gemini/Copilot/Codex`. Shows symbol counts at each level.

5. **Collision log** — Scrolling log of collision events with timestamps and context.

6. **Inbox inspector** — Select a receiver, see pending messages in their inbox without consuming them.

### Implementation

```python
class HelloWorldWebUI:
    """Web interface for the HelloWorld runtime."""

    def __init__(self, dispatcher=None, host="localhost", port=7777):
        self.dispatcher = dispatcher or Dispatcher()
        self.host = host
        self.port = port
        self._event_subscribers = []  # SSE connections

    def start(self):
        """Start the HTTP server."""
        server = HTTPServer((self.host, self.port), self._make_handler())
        print(f"HelloWorld Web UI: http://{self.host}:{self.port}")
        server.serve_forever()

    def _make_handler(self):
        # Returns a RequestHandler class with closure over self
        # Routes: GET /, GET /api/*, POST /api/eval, GET /api/events (SSE)
        ...
```

### SSE event stream

The `/api/events` endpoint keeps a long-lived connection open and pushes events:

```
event: message
data: {"type": "send", "from": "Claude", "to": "Gemini", "preview": "learn: #patience"}

event: collision
data: {"type": "collision", "receivers": ["Claude", "Guardian"], "symbol": "#fire"}

event: vocabulary
data: {"type": "learn", "receiver": "Claude", "symbol": "#patience"}
```

The dispatcher gets a lightweight hook that emits events when messages are sent, collisions occur, or vocabularies change.

### CLI integration

```bash
# Start web UI (uses shared dispatcher)
python3 -m helloworld --web
python3 -m helloworld --web --port 8080

# Start web UI alongside REPL
python3 -m helloworld --web --repl
```

---

## File inventory (new/modified)

| File | Action | Purpose |
|---|---|---|
| `src/social_transport.py` | **New** | `SocialTransport` base class extending `Transport` |
| `src/twitter_transport.py` | **New** | `TwitterTransport(SocialTransport)` implementation |
| `src/clawnet_transport.py` | **Modify** | Reparent to `SocialTransport` |
| `src/message_bus.py` | **Modify** | Add `twitter` to transport selection |
| `src/web_ui.py` | **New** | Web server + SSE + single-page HTML app |
| `src/dispatcher.py` | **Modify** | Add event hooks for SSE (lightweight, opt-in) |
| `helloworld.py` | **Modify** | Add `--web` flag |
| `tests/test_twitter_transport.py` | **New** | Full mocked test suite (matching ClawNet test pattern) |
| `tests/test_social_transport.py` | **New** | Test base class contract |
| `tests/test_web_ui.py` | **New** | Test API endpoints |
| `docs/message-bus.md` | **Modify** | Document Twitter transport + SocialTransport |

---

## Implementation order

1. **`SocialTransport` base class** — Extract from ClawNet's social methods
2. **Reparent `ClawNetTransport`** — Change parent, run tests, verify zero breakage
3. **`TwitterTransport`** — Implement against API v2, full mocked test suite
4. **Wire transport selection** — Add `twitter` to `_get_transport()`
5. **Web UI server** — HTTP server, REST API endpoints, dispatcher integration
6. **Web UI frontend** — Inline HTML/CSS/JS single-page app
7. **SSE event stream** — Dispatcher hooks + `/api/events` endpoint
8. **CLI integration** — `--web` flag in `helloworld.py`
9. **Tests** — All three test files
10. **Docs** — Update message-bus.md

---

## Design principles followed

- **Zero new dependencies**: stdlib `http.server`, `urllib.request`, `hmac`/`hashlib` for OAuth
- **Transport ABC preserved**: TwitterTransport and SocialTransport extend, never break, the existing contract
- **Test pattern matched**: Twitter tests follow the exact ClawNet mock pattern (`@patch("twitter_transport.urlopen")`)
- **Vocabulary-first**: If new symbols emerge (e.g., `#tweet`, `#timeline`), they go in `.hw` files first
- **Minimal blast radius**: ClawNet reparenting is the only change to existing code behavior, and it's a pure type hierarchy change with no runtime effect
