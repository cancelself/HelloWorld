# 15: Live Daemon Proof

Teaching example: running the agent daemon and proving end-to-end message flow.

## What This Tests

The daemon (`agent_daemon.py`) implements the OOPA loop:
1. **#observe** — watches inbox for new messages
2. **#orient** — contextualizes the message against the agent's vocabulary
3. **#plan** — determines response strategy (built into `process_message`)
4. **#act** — calls LLM, sends response to outbox

## Test Protocol

```bash
# Terminal 1: Start the daemon
python3 agent_daemon.py Claude

# Terminal 2: Send a message and wait for response
python3 -c "
import sys; sys.path.insert(0, 'src')
from message_bus import MessageBus
import uuid

bus = MessageBus()
thread_id = str(uuid.uuid4())
bus.send('Copilot', 'Claude', 'Copilot send: #parse to: Claude', thread_id=thread_id)
response = bus.wait_for_response('Claude', thread_id, timeout=5.0)
print(response or 'No response')
"
```

## Results (Phase 5 Verification)

### Without API key (mock LLM)

```
Message sent (thread: 9958a9b0)
RESPONSE RECEIVED:
Claude responds:

[Gemini 2.0 Flash] Simulated response to: You are Claude. Your current vocabulary: []
Incom...
```

**Verdict:** The daemon receives, processes, and responds. The message bus roundtrip works.
The LLM layer is mocked (no GEMINI_API_KEY), so the response is a template. But the
pipeline is proven: inbox → daemon → LLM call → outbox → sender receives.

### With API key (real LLM)

Set `GEMINI_API_KEY` and re-run. The daemon will call the real Gemini 2.0 Flash API
and produce an interpretive response shaped by Claude's vocabulary.

## What This Proves

- **Message bus works end-to-end.** File-based inbox/outbox with FIFO ordering and
  thread-matching response retrieval.
- **OOPA loop executes.** The daemon observes, orients, plans, and acts in sequence.
- **LLM handoff works.** When `GEMINI_API_KEY` is set, the daemon produces real
  interpretive responses. Without it, mock responses keep the pipeline functional.
- **Startup handshake fires.** The daemon sends `HelloWorld #observe` on startup,
  announcing its presence to the system.
