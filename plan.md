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

## Part 4: SDK-Driven Agent Daemons with Human-in-the-Loop

### Vision

Each agent daemon IS its namesake AI, powered by that AI's SDK. The daemon isn't a wrapper — it's Claude/Codex/Gemini/Copilot running with HelloWorld tools, vocabulary, and memory. Humans interact through two interfaces: the **Web UI** (browser, all agents) and the **native CLI** (terminal, one agent at a time).

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Human Interfaces                          │
│                                                               │
│  Web UI (browser)               Native CLIs (terminal)        │
│  ┌──────────────┐      ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │ All agents   │      │claude│ │codex │ │gemini│ │copilot│  │
│  │ Dashboard    │      │ code │ │ cli  │ │ cli  │ │ cli   │  │
│  │ REPL         │      └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘  │
│  │ Inbox viewer │         │        │        │        │       │
│  └──────┬───────┘         │        │        │        │       │
│         │                 │        │        │        │       │
├─────────┼─────────────────┼────────┼────────┼────────┼───────┤
│         │           HelloWorld Message Bus                     │
│         │      (FileTransport / ClawNet / Twitter)             │
├─────────┼─────────────────┼────────┼────────┼────────┼───────┤
│         ▼                 ▼        ▼        ▼        ▼       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │               Agent Daemons (N concurrent)            │    │
│  │                                                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │    │
│  │  │ Claude   │ │ Codex    │ │ Gemini   │ │ Copilot  │ │    │
│  │  │ Process  │ │ Process  │ │ Process  │ │ Process  │ │    │
│  │  │          │ │          │ │          │ │          │ │    │
│  │  │SDK:      │ │SDK:      │ │SDK:      │ │SDK:      │ │    │
│  │  │Claude    │ │OpenAI    │ │Google    │ │GitHub    │ │    │
│  │  │Agent SDK │ │Agents SDK│ │ADK       │ │Copilot   │ │    │
│  │  │          │ │          │ │          │ │          │ │    │
│  │  │Memory:   │ │Memory:   │ │Memory:   │ │Memory:   │ │    │
│  │  │own bus   │ │own bus   │ │own bus   │ │own bus   │ │    │
│  │  │          │ │          │ │          │ │          │ │    │
│  │  │Vocab:    │ │Vocab:    │ │Vocab:    │ │Vocab:    │ │    │
│  │  │own disp  │ │own disp  │ │own disp  │ │own disp  │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Problem (current state)

1. **Copy-paste duplication** — 4 nearly identical daemon files differ only in `AGENT_NAME` and adapter class.
2. **No runtime isolation** — Each daemon loads ALL agents' vocabularies via `AgentRuntime()`.
3. **No memory integration** — `MemoryBus` exists per-agent but daemons don't use it.
4. **No human-in-the-loop** — Daemons run fully autonomously with no escalation mechanism.
5. **Inconsistent code paths** — `agent_daemon.py` uses `get_llm_for_agent()` while SDK daemons use `AgentRuntime` + adapter.

### Solution: `AgentProcess` — isolated, SDK-driven, human-aware

```python
class AgentProcess:
    """Isolated runtime for a single HelloWorld agent.

    Each agent gets:
    - Its own Dispatcher (own registry, own vocabulary state)
    - Its own MemoryBus (runtimes/<agent>/memory/)
    - Its own SDK adapter (auto-detected from SdkAdapter registry)
    - Its own vocabulary drift tracking
    - Human escalation via message bus (#propose, #review, #approve)
    """

    def __init__(self, agent_name: str, vocab_dir: str = "vocabularies"):
        self.name = agent_name
        self.runtime_dir = Path(f"runtimes/{agent_name.lower()}")

        # Isolated runtime components
        self.dispatcher = Dispatcher(vocab_dir=vocab_dir)
        self.memory = MemoryBus(agent_name)
        self.tools = HwTools(vocab_dir=vocab_dir)
        self.adapter = self._detect_adapter()
        self.sdk_agent = None  # initialized lazily

        # Per-agent state
        self.vocabulary = self._load_vocabulary()
        self.learned_symbols = []
        self.message_count = 0
        self.started_at = None
        self.pending_human = []  # messages awaiting human response

    def _detect_adapter(self) -> Optional[SdkAdapter]:
        """Auto-detect SDK adapter from the SDK_AGENT_MAP registry.

        Tries import, returns adapter instance if SDK is available.
        """
        adapter_path = SDK_AGENT_MAP.get(self.name)
        if adapter_path is None:
            return None
        module_name, class_name = adapter_path.rsplit(".", 1)
        try:
            mod = __import__(module_name)
            adapter_cls = getattr(mod, class_name)
            adapter = adapter_cls(hw_tools=self.tools)
            return adapter if adapter.has_sdk() else None
        except (ImportError, AttributeError):
            return None

    def _init_sdk_agent(self):
        """Create the SDK agent with HelloWorld tools + system prompt."""
        if self.sdk_agent or not self.adapter:
            return
        agent_def = self._build_agent_def()
        sdk_tools = self.adapter.adapt_tools(self.tools)
        self.sdk_agent = self.adapter.create_agent(
            name=self.name,
            system_prompt=agent_def.system_prompt,
            tools=sdk_tools,
        )

    async def process_message(self, msg: Message) -> str:
        """Process a message through this agent's SDK.

        1. Store incoming message in memory
        2. Recall relevant context from memory
        3. Check if human escalation is needed
        4. Process through SDK adapter (or LLM fallback)
        5. Store response in memory
        6. Track vocabulary drift
        """
        # 1. Store incoming
        self.memory.store(
            f"From {msg.sender}: {msg.content}",
            title=f"inbox-{msg.sender}-{self.message_count}",
            tags=["inbox", msg.sender],
        )

        # 2. Recall context
        context = self._recall_context(msg.content)

        # 3. Check for human escalation
        if self._needs_human(msg):
            return self._escalate_to_human(msg)

        # 4. Process through SDK
        if self.adapter and self.sdk_agent:
            prompt = self._build_prompt(msg, context)
            response = await self.adapter.query(self.sdk_agent, prompt)
        else:
            response = await self._interpret_via_llm(msg, context)

        # 5. Store response
        self.memory.store(
            f"To {msg.sender}: {response}",
            title=f"outbox-{msg.sender}-{self.message_count}",
            tags=["outbox", msg.sender],
        )

        self.message_count += 1
        return response

    def _needs_human(self, msg: Message) -> bool:
        """Check if message requires human-in-the-loop.

        Triggers: #propose (needs #approve), #review (needs human eyes),
        #question (needs human answer), messages from Human receiver.
        """
        content = msg.content
        return any(sym in content for sym in
                   ("#propose", "#review", "#question")) or msg.sender == "Human"

    def _escalate_to_human(self, msg: Message) -> str:
        """Route message to human via Web UI and CLI.

        Adds to pending_human queue (polled by Web UI).
        Also sends to Human receiver inbox (picked up by CLI).
        """
        self.pending_human.append({
            "from": msg.sender,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "type": "escalation",
        })
        message_bus.send(self.name, "Human", msg.content)
        return f"[{self.name}] Escalated to human: {msg.content[:80]}"

    async def run(self):
        """Main daemon loop — OODA with memory and human escalation."""
        self.started_at = datetime.now(timezone.utc)
        self._init_sdk_agent()
        message_bus.hello(self.name)

        while True:
            # Check for human responses
            human_msg = message_bus.receive(f"{self.name}-human")
            if human_msg:
                await self._handle_human_response(human_msg)

            # Check agent inbox
            msg = message_bus.receive(self.name)
            if msg and msg.sender != self.name:
                response = await self.process_message(msg)
                if not response.startswith("NOTHING_FURTHER"):
                    message_bus.send(self.name, msg.sender, response)

            await asyncio.sleep(0.5)

    def status(self) -> dict:
        """Full agent status for Web UI monitoring."""
        return {
            "name": self.name,
            "vocabulary_size": len(self.vocabulary),
            "learned": self.learned_symbols,
            "messages_processed": self.message_count,
            "memory_available": self.memory.available(),
            "adapter": self.adapter.sdk_name() if self.adapter else "LLM fallback",
            "sdk_ready": self.sdk_agent is not None,
            "pending_human": len(self.pending_human),
            "uptime": str(datetime.now(timezone.utc) - self.started_at)
                     if self.started_at else None,
        }
```

### Unified daemon entry point

Replace all 4 daemon files with a single `agent_daemon.py`:

```python
#!/usr/bin/env python3
"""HelloWorld Agent Daemon — run N agents with isolated SDK runtimes.

Each agent IS its namesake AI, powered by its SDK:
  Claude  -> Claude Agent SDK
  Codex   -> OpenAI Agents SDK
  Gemini  -> Google ADK
  Copilot -> GitHub Copilot SDK

Usage:
    python3 agent_daemon.py Claude              # Single agent
    python3 agent_daemon.py Claude Gemini       # Multiple agents
    python3 agent_daemon.py --all               # All known agents
    python3 agent_daemon.py --list              # Show available agents
"""

async def main():
    agents = parse_args()
    processes = [AgentProcess(name) for name in agents]

    for p in processes:
        sdk = p.adapter.sdk_name() if p.adapter else "LLM fallback"
        mem = "yes" if p.memory.available() else "no"
        print(f"  {p.name}: {len(p.vocabulary)} symbols, sdk={sdk}, memory={mem}")

    await asyncio.gather(*[p.run() for p in processes])
```

### Human-in-the-loop: two interfaces

**1. Web UI (browser — all agents)**

The Web UI from Part 3 gains human interaction endpoints:

```
GET  /api/agents                    → All running agents with status
GET  /api/agents/:name/pending      → Messages awaiting human response
POST /api/agents/:name/respond      → Human responds to pending message
POST /api/agents/:name/approve      → Human approves a #propose
POST /api/agents/:name/guide        → Human sends #guide to redirect agent
GET  /api/events                    → SSE includes escalation events
```

Dashboard shows notification badges when agents have pending human items.

**2. Native CLI (terminal — one agent)**

Each AI's CLI drives its daemon directly. The human runs their preferred CLI, which connects to the running daemon via the message bus:

```bash
# Human uses Claude Code to interact with Claude daemon
claude --session helloworld

# Human uses Codex CLI to interact with Codex daemon
codex --session helloworld

# Human uses Gemini to interact with Gemini daemon
gemini code --session helloworld
```

**How it connects:** The CLI reads from `runtimes/<agent>-human/inbox/` (daemon's escalation outbox) and writes human responses to `runtimes/<agent>-human/outbox/`. The daemon polls this channel in its main loop alongside its primary inbox.

### What gets deleted

- `copilot_daemon.py` — absorbed into unified `AgentProcess`
- `gemini_daemon.py` — absorbed into unified `AgentProcess`
- `codex_daemon.py` — absorbed into unified `AgentProcess`

### Memory integration

Each `AgentProcess` uses `MemoryBus` to:
- **Store** every incoming/outgoing message (tagged by sender/receiver)
- **Recall** relevant context before processing (if QMD available)
- **Track drift** — log when new symbols are learned through dialogue
- **Persist across restarts** — `runtimes/<agent>/memory/` survives daemon restarts

---

## Updated file inventory (new/modified)

| File | Action | Purpose |
|---|---|---|
| `src/social_transport.py` | **New** | `SocialTransport` base class extending `Transport` |
| `src/twitter_transport.py` | **New** | `TwitterTransport(SocialTransport)` implementation |
| `src/clawnet_transport.py` | **Modify** | Reparent to `SocialTransport` |
| `src/message_bus.py` | **Modify** | Add `twitter` to transport selection |
| `src/web_ui.py` | **New** | Web server + SSE + single-page HTML app |
| `src/dispatcher.py` | **Modify** | Add event hooks for SSE (lightweight, opt-in) |
| `src/agent_process.py` | **New** | `AgentProcess` — isolated per-agent runtime |
| `agent_daemon.py` | **Rewrite** | Unified daemon using `AgentProcess` |
| `copilot_daemon.py` | **Delete** | Absorbed into unified daemon |
| `gemini_daemon.py` | **Delete** | Absorbed into unified daemon |
| `codex_daemon.py` | **Delete** | Absorbed into unified daemon |
| `scripts/run_daemons.sh` | **Simplify** | Single command instead of 4 processes |
| `helloworld.py` | **Modify** | Add `--web` flag |
| `tests/test_twitter_transport.py` | **New** | Full mocked test suite |
| `tests/test_social_transport.py` | **New** | Test base class contract |
| `tests/test_web_ui.py` | **New** | Test API endpoints |
| `tests/test_agent_process.py` | **New** | Test isolated runtime, memory integration |

---

## Updated implementation order

1. **`SocialTransport` base class** — Extract from ClawNet's social methods
2. **Reparent `ClawNetTransport`** — Change parent, run tests, verify zero breakage
3. **`TwitterTransport`** — Implement against API v2, full mocked test suite
4. **Wire transport selection** — Add `twitter` to `_get_transport()`
5. **`AgentProcess`** — Isolated per-agent runtime with memory integration
6. **Unified `agent_daemon.py`** — Rewrite + delete 3 duplicate daemons
7. **Web UI server** — HTTP server, REST API endpoints, dispatcher integration
8. **Web UI frontend** — Inline HTML/CSS/JS single-page app
9. **SSE event stream** — Dispatcher hooks + `/api/events` endpoint
10. **CLI integration** — `--web` flag in `helloworld.py`
11. **Tests** — All four test files
12. **Docs** — Update message-bus.md

---

## Design principles followed

- **Zero new dependencies**: stdlib `http.server`, `urllib.request`, `hmac`/`hashlib` for OAuth
- **Transport ABC preserved**: TwitterTransport and SocialTransport extend, never break, the existing contract
- **Test pattern matched**: Twitter tests follow the exact ClawNet mock pattern (`@patch("twitter_transport.urlopen")`)
- **Vocabulary-first**: If new symbols emerge (e.g., `#tweet`, `#timeline`), they go in `.hw` files first
- **Minimal blast radius**: ClawNet reparenting is the only change to existing code behavior, and it's a pure type hierarchy change with no runtime effect
