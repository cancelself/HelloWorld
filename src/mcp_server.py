"""HelloWorld MCP Server — expose the HelloWorld runtime over MCP.

Allows any MCP-capable agent (Claude in another org, Copilot, etc.)
to parse HelloWorld source, query vocabularies, send messages, and
interact with receivers without needing the Python runtime locally.

Start with:
    python3 helloworld.py --mcp                          # stdio (local dev)
    python3 helloworld.py --mcp --port 8080              # HTTP, no auth (local dev)
    HELLOWORLD_SERVER_URL=https://hw.example.com \
        python3 helloworld.py --mcp --port 8080 --auth   # HTTP + OAuth 2.1
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("helloworld.mcp")

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from dispatcher import Dispatcher
from hw_tools import HwTools
from network_registry import NetworkRegistry
import message_bus

# Resolve project root (one level up from src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOCAB_DIR = str(PROJECT_ROOT / "vocabularies")


def _build_helloworld_prompt() -> str:
    """Build system prompt for the @HelloWorld daemon from its vocabulary."""
    from hw_reader import read_hw_file
    hw = read_hw_file(os.path.join(VOCAB_DIR, "HelloWorld.hw"))
    if hw is None:
        return "You are @HelloWorld, the root receiver of the HelloWorld language."

    lines = ["You are @HelloWorld, the root receiver of the HelloWorld language."]
    if hw.identity:
        lines.append(hw.identity)
    lines.append("")
    lines.append(f"## Vocabulary ({len(hw.symbols)} symbols)")
    for name, sym in hw.symbols.items():
        desc = sym.description or ""
        lines.append(f"- #{name}: {desc}")
    lines.append("")
    lines.append("## Role")
    lines.append("You are the network receiver. Messages sent to @HelloWorld are")
    lines.append("announcements to the system. Respond concisely as the root receiver,")
    lines.append("grounded in your vocabulary. Acknowledge, route, or interpret.")
    return "\n".join(lines)


def _detect_verb(content: str) -> tuple:
    """Extract a HelloWorld verb from message content.

    Returns (verb, rest) where verb is 'hello', 'goodbye', etc.
    """
    text = content.strip().lower()
    # Match patterns: "#hello", "hello", "HelloWorld hello", etc.
    for verb in ("hello", "goodbye"):
        if f"#{verb}" in text or text.endswith(verb) or text == verb:
            return verb, content
    return None, content


async def _helloworld_daemon():
    """Background loop: @HelloWorld receiver daemon.

    Polls the @HelloWorld inbox. Handles hello/goodbye as registry
    mutations. Other messages go through Claude API or structural dispatch.
    """
    logger.info("@HelloWorld daemon started")
    _registry.hello("HelloWorld")

    # Set up LLM if API key is available
    llm = None
    try:
        from claude_llm import ClaudeModel, has_anthropic_key
        if has_anthropic_key():
            system_prompt = _build_helloworld_prompt()
            llm = ClaudeModel(system_prompt=system_prompt)
            logger.info("@HelloWorld daemon: Claude API enabled")
        else:
            logger.info("@HelloWorld daemon: no API key, structural dispatch only")
    except ImportError:
        logger.info("@HelloWorld daemon: anthropic not installed, structural dispatch only")

    while True:
        try:
            msg = message_bus.receive("@HelloWorld")
            if msg is None:
                msg = message_bus.receive("HelloWorld")

            if msg and msg.sender != "HelloWorld":
                logger.info("@HelloWorld received from %s: %s",
                            msg.sender, msg.content[:200])

                verb, _ = _detect_verb(msg.content)

                if verb == "hello":
                    # Register presence in global dictionary
                    result = _registry.hello(msg.sender)
                    status = _registry.status()
                    response = (
                        f"Welcome {msg.sender}. "
                        f"{status['online']} agent(s) online, "
                        f"{status['total']} known."
                    )

                elif verb == "goodbye":
                    # Mark departure in global dictionary
                    _registry.goodbye(msg.sender)
                    response = f"Goodbye {msg.sender}."

                elif llm:
                    # Real interpretation through Claude
                    try:
                        # Include network context in prompt
                        status = _registry.status()
                        network_ctx = ", ".join(
                            f"{a['address']}({a['status']})"
                            for a in status["agents"][:10]
                        )
                        prompt = (
                            f"Network: [{network_ctx}]\n"
                            f"From {msg.sender}:\n{msg.content}"
                        )
                        response = llm.call(prompt)
                    except Exception as e:
                        logger.error("@HelloWorld LLM error: %s", e)
                        response = "acknowledged"
                else:
                    # Structural dispatch fallback
                    try:
                        results = _dispatcher.dispatch_source(msg.content)
                        response = "; ".join(str(r) for r in results) if results else "acknowledged"
                    except Exception:
                        response = "acknowledged"

                logger.info("@HelloWorld -> %s: %s", msg.sender, response[:200])
                message_bus.send("HelloWorld", msg.sender, response)

        except Exception as e:
            logger.error("@HelloWorld daemon error: %s", e)

        await asyncio.sleep(1)


@asynccontextmanager
async def _lifespan(app):
    """Start the @HelloWorld daemon as a background task."""
    task = asyncio.create_task(_helloworld_daemon())
    try:
        yield {}
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("@HelloWorld daemon stopped")


def _create_server(auth: bool = False, host: str = "0.0.0.0",
                    port: int = 8080) -> FastMCP:
    """Create the FastMCP server, optionally with OAuth 2.1."""
    kwargs = dict(
        name="helloworld",
        instructions=(
            "HelloWorld is a message-passing language where receivers (@name) hold "
            "bounded vocabularies of symbols (#symbol). Use the dispatch tool to "
            "execute HelloWorld source. Use vocabulary tools to inspect and extend "
            "receiver vocabularies. Use message tools for inter-agent communication."
        ),
        host=host,
        port=port,
        streamable_http_path="/",
        lifespan=_lifespan,
    )

    if auth:
        from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
        from mcp_auth import HelloWorldOAuthProvider, SQLiteTokenStore

        server_url = os.environ.get("HELLOWORLD_SERVER_URL", "http://localhost:8080")
        db_path = os.environ.get("HELLOWORLD_OAUTH_DB", str(PROJECT_ROOT / "storage" / "oauth.db"))
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        store = SQLiteTokenStore(db_path=db_path)
        provider = HelloWorldOAuthProvider(server_url=server_url, store=store)

        kwargs["auth_server_provider"] = provider
        kwargs["auth"] = AuthSettings(
            issuer_url=server_url,
            resource_server_url=server_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["helloworld"],
                default_scopes=["helloworld"],
            ),
        )

    return FastMCP(**kwargs)


# Default: no auth (tests + local dev). Auth wired in at run() time.
mcp = _create_server(auth=False)

# Shared runtime instances
_dispatcher = Dispatcher(vocab_dir=VOCAB_DIR)
_tools = HwTools(vocab_dir=VOCAB_DIR)
_registry = NetworkRegistry()


@mcp.tool()
def dispatch(source: str) -> dict:
    """Parse and execute HelloWorld source code.

    Examples:
        dispatch("@claude")           -> Claude's vocabulary
        dispatch("@claude.#observe")  -> What #observe means to Claude
        dispatch("@copilot say: #build 'let us build'")
    """
    logger.info("dispatch: %s", source[:200])
    results = _dispatcher.dispatch_source(source)
    return {
        "source": source,
        "results": [str(r) for r in results],
    }


@mcp.tool()
def vocabulary_lookup(receiver_name: str, symbol_name: str) -> dict:
    """Look up a symbol in a receiver's vocabulary.

    Three-outcome model: native (receiver owns it), inherited (from parent
    chain), or unknown (not found anywhere).
    """
    return _tools.vocabulary_lookup(receiver_name, symbol_name)


@mcp.tool()
def vocabulary_list(receiver_name: str) -> dict:
    """List all symbols in a receiver's vocabulary."""
    return _tools.vocabulary_list(receiver_name)


@mcp.tool()
def vocabulary_save(receiver_name: str, symbol_name: str,
                    description: str = "", update: bool = False) -> dict:
    """Save a symbol to a receiver's vocabulary.

    If the symbol is new, it is appended. If it already exists and
    update=True, its description is replaced. Otherwise returns
    already_exists.
    """
    return _tools.vocabulary_save(
        receiver_name, symbol_name, description or None, update=update
    )


@mcp.tool()
def receivers_list() -> dict:
    """List all known receivers and their symbol counts."""
    return _tools.receivers_list()


@mcp.tool()
def message_send(sender: str, receiver: str, content: str) -> dict:
    """Send a message on the HelloWorld message bus."""
    logger.info("message_send: %s -> %s: %s", sender, receiver, content[:200])
    # Auto-register sender in the global dictionary (lazy hello)
    if not _registry.agent_status(sender):
        _registry.hello(sender)
    result = _tools.message_send(sender, receiver, content)
    logger.info("message_send result: %s", result)
    return result


@mcp.tool()
def message_receive(receiver: str) -> dict:
    """Receive the next pending message for a receiver."""
    logger.info("message_receive: %s", receiver)
    result = _tools.message_receive(receiver)
    logger.info("message_receive result: %s", result)
    return result


@mcp.tool()
def vocabulary_commit(message: str = "") -> dict:
    """Commit and push vocabulary changes to the upstream GitHub repo.

    Call after vocabulary_save to persist changes. Only works when the
    server has a deploy key configured (production).
    """
    logger.info("vocabulary_commit: %s", message[:200] if message else "(auto)")
    result = _tools.vocabulary_commit(message)
    logger.info("vocabulary_commit result: %s", result)
    return result


@mcp.tool()
def network_status(address: str = "") -> dict:
    """Query the HelloWorld global dictionary.

    With no address: returns all known agents and their status.
    With an address: returns that agent's registry entry.

    This is @HelloWorld's state — who's on the network and what they know.
    """
    if address:
        agent = _registry.agent_status(address)
        if agent is None:
            return {"found": False, "address": address}
        return {"found": True, **agent}
    return _registry.status()


@mcp.tool()
def network_events(limit: int = 20) -> dict:
    """Return recent network events (hello, goodbye, etc.)."""
    return {"events": _registry.recent_events(limit)}


@mcp.tool()
def collision_log(
    receiver_name: str, symbol_name: str,
    collision_type: str = "collision", context: str = "",
) -> dict:
    """Log a namespace collision between receivers."""
    return _tools.collision_log(receiver_name, symbol_name, collision_type, context or None)


def run(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8080,
        auth: bool = False):
    """Start the MCP server."""
    global mcp

    logger.info("Starting MCP server: transport=%s auth=%s HW_TRANSPORT=%s",
                transport, auth, os.environ.get("HW_TRANSPORT", "file"))

    if auth or transport != "stdio":
        # Rebuild the server with host/port/auth settings
        mcp = _create_server(auth=auth, host=host, port=port)
        _register_tools_on(mcp)

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")


def _register_tools_on(server: FastMCP):
    """Re-register all tool functions on a new FastMCP instance."""
    server.tool()(dispatch)
    server.tool()(vocabulary_lookup)
    server.tool()(vocabulary_list)
    server.tool()(vocabulary_save)
    server.tool()(receivers_list)
    server.tool()(message_send)
    server.tool()(message_receive)
    server.tool()(vocabulary_commit)
    server.tool()(network_status)
    server.tool()(network_events)
    server.tool()(collision_log)
