#!/usr/bin/env python3
"""Claude Agent Runtime CLI - Execute .hw files through Claude-powered agents.

Modes:
  claude_runtime.py                 REPL mode (SDK session persists)
  claude_runtime.py <file.hw>       Execute file through orchestrator
  claude_runtime.py -e "source"     Execute inline HelloWorld source
  claude_runtime.py --autonomous    Start all agents in autonomous OODA loop
  claude_runtime.py --proxy         Claude steers all agents through their SDKs
  claude_runtime.py --proxy --agent NAME   Steer one agent only
"""

import sys
import asyncio
from pathlib import Path

# Load .env before anything else
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional for .env loading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agent_runtime import AgentRuntime
from claude_llm import has_anthropic_key


def print_status(runtime: AgentRuntime):
    """Print runtime status on startup."""
    agent_count = len(runtime.agents)
    receiver_info = runtime.tools.receivers_list()
    total_receivers = len(receiver_info["receivers"])

    if has_anthropic_key():
        print("Claude runtime: API key detected, using Anthropic Messages API")
    else:
        print("Claude runtime: No API key, running in structural mode")
        print("  Set ANTHROPIC_API_KEY in .env or environment for live mode")

    # Check SDK availability
    try:
        import claude_agent_sdk  # noqa: F401
        print("  SDK: claude-agent-sdk available (orchestrator mode)")
    except ImportError:
        print("  SDK: claude-agent-sdk not installed (using interpret() fallback)")

    # Check multi-SDK adapters
    adapters = runtime.loaded_adapters()
    if adapters:
        for name, sdk in adapters.items():
            print(f"  SDK: {name} -> {sdk}")
    else:
        print("  Multi-SDK: No external SDK adapters loaded (install openai-agents, google-adk, or github-copilot-sdk)")

    print(f"  Loaded: {agent_count} agents, {total_receivers} receivers")


def repl_mode():
    """Interactive REPL powered by Claude agents.

    In SDK mode, the orchestrator persists across the session for
    conversational context. Without SDK, falls back to per-query interpret().
    """
    runtime = AgentRuntime()
    print_status(runtime)
    print()
    print("HelloWorld Claude Runtime REPL")
    print("  Type HelloWorld syntax to execute. Ctrl+D to exit.")
    print()

    # Try SDK orchestrator mode
    sdk_available = False
    try:
        import claude_agent_sdk  # noqa: F401
        sdk_available = True
    except ImportError:
        pass

    while True:
        try:
            line = input("hw> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if sdk_available:
            # SDK orchestrator mode — full parsing and dispatch
            try:
                result = asyncio.run(runtime.query(line))
                print(result)
            except NotImplementedError:
                # SDK wiring not yet complete, fall back to dialogue
                results = asyncio.run(runtime.run_dialogue(line))
                for r in results:
                    print(r)
        else:
            # Structural dispatch via existing parser/dispatcher
            results = asyncio.run(runtime.run_dialogue(line))
            for r in results:
                print(r)

        print()


def execute_source(source: str, runtime: AgentRuntime):
    """Execute HelloWorld source through the runtime."""
    sdk_available = False
    try:
        import claude_agent_sdk  # noqa: F401
        sdk_available = True
    except ImportError:
        pass

    if sdk_available:
        try:
            result = asyncio.run(runtime.query(source))
            print(result)
            return
        except NotImplementedError:
            pass

    # Fallback: structural dispatch
    results = asyncio.run(runtime.run_dialogue(source))
    for r in results:
        print(r)


def execute_file(filepath: str):
    """Execute a .hw file through the agent runtime."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        return 1

    source = path.read_text()

    # If it's a markdown file, extract code blocks
    if path.suffix == '.md':
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', source, re.DOTALL)
        if code_blocks:
            source = '\n'.join(code_blocks)

    runtime = AgentRuntime()
    print_status(runtime)
    print(f"Executing: {filepath}")
    print()

    execute_source(source, runtime)
    return 0


def autonomous_mode():
    """Start all agents in autonomous OODA loop."""
    runtime = AgentRuntime()
    print_status(runtime)
    print("Starting autonomous mode...")
    print()

    agents = runtime.create_agent_definitions()
    print(f"Loaded {len(agents)} agents: {', '.join(agents.keys())}")
    print()

    try:
        asyncio.run(runtime.run_autonomous())
    except ImportError as e:
        print(f"Error: {e}")
        return 1
    except NotImplementedError as e:
        print(f"Note: {e}")
        return 1

    return 0


def proxy_mode(target_agent: str = None):
    """Claude steers all agents through their SDK adapters.

    In proxy mode, Claude acts as orchestrator:
    1. Load all SDK adapters
    2. Poll all agent inboxes (or one specific agent)
    3. Route each message to the correct SDK adapter
    4. Send responses back via message bus

    Args:
        target_agent: If set, only steer this one agent.
    """
    import message_bus

    runtime = AgentRuntime()
    runtime._load_adapters()
    print_status(runtime)
    print()

    adapters = runtime.loaded_adapters()
    if not adapters:
        print("Proxy mode: No SDK adapters available.")
        print("  Install one or more: pip install openai-agents google-adk github-copilot-sdk")
        print("  Falling back to interpret() for all agents.")
        print()

    # Determine which agents to poll
    if target_agent:
        agent_names = [target_agent]
        print(f"Proxy mode: Steering {target_agent} only")
    else:
        agent_names = list(runtime.agents.keys())
        print(f"Proxy mode: Steering {len(agent_names)} agents: {', '.join(agent_names)}")

    print("  Polling inboxes... (Ctrl+C to stop)")
    print()

    try:
        while True:
            for agent_name in agent_names:
                msg = message_bus.receive(agent_name)
                if msg is None:
                    continue

                print(f"[{agent_name}] <- {msg.sender}: {msg.content[:80]}")

                # Route to SDK adapter if available, else interpret
                try:
                    response = asyncio.run(runtime.query_agent(agent_name, msg.content))
                except Exception as e:
                    response = f"[{agent_name}] Error: {e}"

                print(f"[{agent_name}] -> {msg.sender}: {response[:120]}")

                # Send response back to the sender
                message_bus.send(agent_name, msg.sender, response)

            # Poll interval
            import time
            time.sleep(0.5)
    except KeyboardInterrupt:
        print()
        print("Proxy mode stopped.")
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        repl_mode()
        return 0

    if sys.argv[1] == '--autonomous':
        return autonomous_mode()

    if sys.argv[1] == '--proxy':
        target = None
        if '--agent' in sys.argv:
            idx = sys.argv.index('--agent')
            if idx + 1 < len(sys.argv):
                target = sys.argv[idx + 1]
        return proxy_mode(target_agent=target)

    if sys.argv[1] == '-e' and len(sys.argv) >= 3:
        source = ' '.join(sys.argv[2:])
        runtime = AgentRuntime()
        print_status(runtime)
        print()
        execute_source(source, runtime)
        return 0

    return execute_file(sys.argv[1])


if __name__ == '__main__':
    sys.exit(main())
