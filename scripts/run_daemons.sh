#!/usr/bin/env bash
# Launch HelloWorld agent daemons using the unified agent_daemon.py.
#
# Usage:
#   ./scripts/run_daemons.sh              # All agents
#   ./scripts/run_daemons.sh Claude Gemini # Specific agents
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ "$#" -eq 0 ]; then
  echo "Launching all HelloWorld agent daemons..."
  exec python3 -u agent_daemon.py --all
else
  echo "Launching HelloWorld agent daemons: $*"
  exec python3 -u agent_daemon.py "$@"
fi
