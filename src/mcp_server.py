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

import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("helloworld.mcp")

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from dispatcher import Dispatcher
from hw_tools import HwTools

# Resolve project root (one level up from src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOCAB_DIR = str(PROJECT_ROOT / "vocabularies")


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
    server.tool()(collision_log)
