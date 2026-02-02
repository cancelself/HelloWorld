#!/usr/bin/env bash
# Launch multiple HelloWorld agent daemons and stream their logs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ "$#" -eq 0 ]; then
  AGENTS=("Claude" "Gemini" "Copilot" "Codex")
else
  AGENTS=("$@")
fi

LOG_DIR="runtimes/daemon-logs"
mkdir -p "$LOG_DIR"

declare -a PIDS=()

cleanup() {
  if [ "${#PIDS[@]}" -gt 0 ]; then
    echo
    echo "Stopping agent daemons..."
    for pid in "${PIDS[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
      fi
    done
  fi
  for agent in "${AGENTS[@]}"; do
    safe="$(echo "$agent" | tr '[:upper:]' '[:lower:]')"
    rm -f "$LOG_DIR/${safe}.pid"
  done
}

trap cleanup EXIT

echo "Launching HelloWorld agent daemons: ${AGENTS[*]}"
for agent in "${AGENTS[@]}"; do
  safe="$(echo "$agent" | tr '[:upper:]' '[:lower:]')"
  log="$LOG_DIR/${safe}.log"
  : > "$log"
  echo "  - $agent (log: $log)"
  python3 -u agent_daemon.py "$agent" >> "$log" 2>&1 &
  pid=$!
  PIDS+=("$pid")
  echo "$pid" > "$LOG_DIR/${safe}.pid"
done

echo
echo "All daemons running. Streaming logs (Ctrl+C to stop and clean up)..."
tail -n +1 -F "$LOG_DIR"/*.log
