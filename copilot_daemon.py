#!/usr/bin/env python3
"""Copilot Agent Daemon — standalone GitHub Copilot SDK runtime.

Polls the Copilot inbox via message_bus, processes messages through
the GitHub Copilot SDK, and sends responses back.

The Copilot SDK uses persistent sessions — the session is created once
and reused across messages for conversational context.

Usage:
    python copilot_daemon.py
"""

import sys
import asyncio
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agent_runtime import AgentRuntime
from copilot_runtime import CopilotAdapter
from hw_tools import HwTools
import message_bus

AGENT_NAME = "Copilot"
POLL_INTERVAL = 0.5


async def run_daemon():
    """Main daemon loop: poll inbox, process via Copilot SDK, respond."""
    runtime = AgentRuntime()
    tools = HwTools(vocab_dir=runtime.vocab_dir)
    adapter = CopilotAdapter(hw_tools=tools)

    if not adapter.has_sdk():
        print(f"[{AGENT_NAME}] GitHub Copilot SDK not installed.")
        print(f"  Install with: pip install github-copilot-sdk")
        print(f"  Falling back to interpret() mode.")
        adapter = None

    sdk_agent = None
    if adapter is not None:
        agent_def = runtime.agents.get(AGENT_NAME)
        if agent_def is None:
            print(f"[{AGENT_NAME}] No agent definition found. Check vocabularies/{AGENT_NAME}.hw")
            return 1

        sdk_tools = adapter.adapt_tools(tools)
        sdk_agent = adapter.create_agent(
            name=AGENT_NAME,
            system_prompt=agent_def.system_prompt,
            tools=sdk_tools,
        )
        print(f"[{AGENT_NAME}] Copilot agent created with {len(sdk_tools)} tools")

    print(f"[{AGENT_NAME}] Daemon started. Polling inbox... (Ctrl+C to stop)")

    try:
        while True:
            msg = message_bus.receive(AGENT_NAME)
            if msg is not None:
                print(f"[{AGENT_NAME}] <- {msg.sender}: {msg.content[:80]}")

                if adapter is not None and sdk_agent is not None:
                    try:
                        response = await adapter.query(sdk_agent, msg.content)
                    except Exception as e:
                        response = f"[{AGENT_NAME}] Copilot SDK error: {e}"
                else:
                    try:
                        response = await runtime.interpret(AGENT_NAME, msg.content)
                    except Exception as e:
                        response = f"[{AGENT_NAME}] Interpret error: {e}"

                print(f"[{AGENT_NAME}] -> {msg.sender}: {response[:120]}")
                message_bus.send(AGENT_NAME, msg.sender, response)

            await asyncio.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n[{AGENT_NAME}] Daemon stopped.")
        return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(run_daemon()) or 0)
