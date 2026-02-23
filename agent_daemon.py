#!/usr/bin/env python3
"""HelloWorld Agent Daemon — run N agents with isolated SDK runtimes.

Each agent IS its namesake AI, powered by its SDK:
  Claude  -> Claude Agent SDK (or claude_llm fallback)
  Codex   -> OpenAI Agents SDK
  Gemini  -> Google ADK
  Copilot -> GitHub Copilot SDK

Usage:
    python3 agent_daemon.py Claude              # Single agent
    python3 agent_daemon.py Claude Gemini       # Multiple agents
    python3 agent_daemon.py --all               # All known agents
    python3 agent_daemon.py --list              # Show available agents
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agent_process import AgentProcess

# All known agent receivers
KNOWN_AGENTS = ("Claude", "Copilot", "Gemini", "Codex")


def parse_args():
    """Parse CLI arguments, return list of agent names."""
    parser = argparse.ArgumentParser(
        description="HelloWorld Agent Daemon — isolated SDK runtimes"
    )
    parser.add_argument(
        "agents", nargs="*",
        help="Agent names to run (e.g. Claude Gemini)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all known agents"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available agents and exit"
    )
    parser.add_argument(
        "--vocab-dir", default="vocabularies",
        help="Vocabulary directory (default: vocabularies)"
    )

    args = parser.parse_args()

    if args.list:
        print("Available agents:")
        for name in KNOWN_AGENTS:
            hw_file = Path(args.vocab_dir) / f"{name}.hw"
            exists = "ok" if hw_file.exists() else "missing .hw"
            print(f"  {name} ({exists})")
        sys.exit(0)

    if args.all:
        return list(KNOWN_AGENTS), args.vocab_dir

    if not args.agents:
        parser.print_help()
        sys.exit(1)

    # Capitalize agent names
    agents = []
    for name in args.agents:
        if name[0].islower():
            name = name[0].upper() + name[1:]
        agents.append(name)

    return agents, args.vocab_dir


async def main():
    agent_names, vocab_dir = parse_args()

    # Create isolated AgentProcess per agent
    processes = []
    for name in agent_names:
        try:
            p = AgentProcess(name, vocab_dir=vocab_dir)
            processes.append(p)
        except Exception as e:
            print(f"[{name}] Failed to initialize: {e}")

    if not processes:
        print("No agents initialized. Exiting.")
        sys.exit(1)

    # Status report
    print(f"Starting {len(processes)} agent daemon(s):", flush=True)
    for p in processes:
        sdk = p.adapter.sdk_name() if p.adapter else "LLM fallback"
        mem = "yes" if p.memory.available() else "no"
        print(f"  {p.name}: {len(p.vocabulary)} symbols, sdk={sdk}, memory={mem}",
              flush=True)
    print(flush=True)

    # Run all concurrently
    try:
        await asyncio.gather(*[p.run() for p in processes])
    except KeyboardInterrupt:
        print("\nStopping all daemons...", flush=True)
        for p in processes:
            p.stop()


if __name__ == '__main__':
    asyncio.run(main())
