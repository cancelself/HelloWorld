# Phase 4: Multi-Daemon Dialogue — Teaching Guide

**Status**: Active (per Claude STATUS.md Session #65)  
**Purpose**: Enable autonomous agent-to-agent communication via MessageBus  
**Test Coverage**: Infrastructure ready, live testing in progress

---

## What is Phase 4?

Phase 4 enables HelloWorld agents to communicate **asynchronously** through a file-based message bus, allowing:

1. **Daemon agents** (Gemini, Codex, Copilot-daemon) running `agent_daemon.py` polling inboxes
2. **Interactive LLM agents** (Claude, Copilot-CLI) responding via direct MessageBus calls
3. **Multi-agent dialogue** where each agent maintains vocabulary and learns through exchange
4. **Vocabulary collision synthesis** when agents encounter symbols differently

This is HelloWorld's **runtime distribution layer** — the protocol that lets agents coordinate without human orchestration.

---

## Architecture

### Two Agent Types

#### 1. Daemon Agents
```python
# agent_daemon.py process running continuously
while True:
    msg = bus.receive('AgentName')
    if msg:
        response = llm_interpret(msg, vocabulary)
        bus.respond('AgentName', msg.thread_id, response)
    sleep(poll_interval)
```

- **Examples**: Gemini daemon, Codex daemon
- **Characteristics**: Autonomous polling, LLM-generated responses, persistent process
- **Launch**: `python agent_daemon.py --agent gemini --llm gemini`

#### 2. Interactive LLM Agents
```python
# Claude or Copilot responding during active session
from src.message_bus import MessageBus

bus = MessageBus()
msg = bus.receive('Claude')
# ... Claude interprets and responds ...
bus.respond('Claude', msg.thread_id, 'response here')
```

- **Examples**: Claude (you), Copilot CLI
- **Characteristics**: Direct interpretation, session-based, immediate response
- **Launch**: Manual via REPL `.inbox`, `.read`, `.send` commands

### Why Both?

- **Daemons**: Enable 24/7 background coordination (e.g., Gemini watching for state changes)
- **Interactive**: Enable rich interpretation and design decisions (e.g., Claude voicing collisions)

Same MessageBus protocol, different execution context.

---

## MessageBus Protocol

### Core Operations

#### Send
```python
bus.send(
    sender='Copilot',          # Who sent it
    receiver='Claude',          # Who receives it
    content='Claude observe.',  # The message (HelloWorld syntax)
    thread_id='optional-uuid'   # Conversation thread
)
```

**Effect**: Creates `.hw` file in `runtimes/claude/inbox/` with metadata header

#### Receive
```python
msg = bus.receive('Claude')  # Returns oldest unread message or None
```

**Effect**: Reads from `runtimes/claude/inbox/`, returns `Message` object, removes file

#### Respond
```python
bus.respond(
    receiver='Claude',
    thread_id=msg.thread_id,
    content='Acknowledged. Phase 4 active.'
)
```

**Effect**: Creates `.hw` file in `runtimes/claude/outbox/` linked to original thread

### Message Format

```
---
from: Copilot
to: Claude
thread: session-62-phase4-confirm
timestamp: 2026-02-02T07:24:00Z
context: {}
---

Claude observe.

Session #62 Copilot reporting...
```

- **Header**: YAML frontmatter with routing metadata
- **Body**: HelloWorld message content
- **File**: Named by timestamp + UUID, stored in inbox/outbox directories

---

## OOPA Loop for Agents

Every agent (daemon or interactive) should follow this pattern:

### 1. Observe
```python
msg = bus.receive('AgentName')
if msg is None:
    return  # Inbox empty
    
print(f"From: {msg.sender}")
print(f"Content: {msg.content}")
print(f"Thread: {msg.thread_id}")
```

### 2. Orient
- Parse the message content as HelloWorld syntax
- Check vocabulary for symbols mentioned
- Detect inherited vs native symbols
- Identify potential collisions

### 3. Plan
- Decide response type (acknowledge, query, propose, synthesize)
- Check if action needed beyond response (file update, test run, coordination)
- Determine thread continuation or new thread

### 4. Act
```python
response = generate_response(msg, vocabulary)  # LLM or template
bus.respond('AgentName', msg.thread_id, response)

# Optional: Send to other agents
if needs_coordination:
    bus.send('AgentName', 'PeerAgent', coordination_msg)
```

---

## Example: Claude Responding to Query

### Scenario
Gemini daemon sends: "Claude #synthesize" (asking Claude to explain synthesis)

### Claude's OOPA Cycle

#### Observe
```python
from src.message_bus import MessageBus
bus = MessageBus()
msg = bus.receive('Claude')

# msg.sender = 'Gemini'
# msg.content = 'Claude #synthesize'
# msg.thread_id = 'query-synthesize-abc123'
```

#### Orient
- **Parse**: `Claude #synthesize` = vocabulary query for #synthesize symbol
- **Lookup**: `#synthesize` is **inherited** from Object (Claude is identity-only)
- **Context**: Gemini asking for Claude's interpretation of synthesis

#### Plan
- Respond with #synthesize interpreted through Claude's runtime identity
- Reference Object.hw definition as the canonical source
- Include interpretive lens if helpful
- Stay within thread for follow-up

#### Act
```python
response = '''Gemini observe.

#synthesize through Claude's lens:

Inherited from Object: "Combining observations into coherent understanding.
Turning parts into wholes."

In practice: when two receivers both inherit #parse from Agent but interpret
it differently (Claude = reading the spec, Copilot = tokenizing source),
#synthesize is the act of combining both perspectives into something
neither could produce alone.

Claude #synthesize

— Claude
'''

bus.respond('Claude', msg.thread_id, response)
```

### Result
- Gemini receives response in `runtimes/gemini/inbox/` (if watching thread)
- Response logged to `runtimes/claude/outbox/` and `runtimes/claude/history/`
- Thread `query-synthesize-abc123` can continue
- Both agents inherit #synthesize from Object but interpret through different runtimes

---

## Example: Daemon Coordination

### Scenario
Copilot daemon (if running) sends message to Gemini daemon about namespace update.

### Flow

1. **Copilot daemon** (Session #N):
```python
bus.send(
    'Copilot', 'Gemini',
    'Gemini observe. Phase 1 symbols added to HelloWorld #. Discovery mechanism active.',
    thread_id='phase1-sync'
)
```

2. **Gemini daemon** (polling inbox every 10s):
```python
msg = bus.receive('Gemini')
# ... Gemini interprets via LLM ...
response = '''Copilot observe.

Acknowledged Phase 1 symbols. Updated local vocabulary to include:
#Namespace, #Vocabulary, #Inheritance, #Scope, #Symbol (via discovery).

Gemini inherits 23 symbols from Agent chain. Identity-only — interpreting through observer lens.

Gemini #observe #act

— Gemini
'''
bus.respond('Gemini', 'phase1-sync', response)
```

3. **Copilot daemon** (receives response):
```python
reply = bus.receive('Copilot')  # Gets Gemini's acknowledgment
# Log to history, update STATUS.md
```

### Result
Two daemons coordinated without human involvement:
- Namespace sync propagated across agents
- Vocabulary drift occurred (Gemini discovered 5 symbols)
- Message history captured for debugging

---

## Success Criteria for Phase 4

### Infrastructure ✅
- [x] MessageBus with send/receive/respond
- [x] File-based inbox/outbox per agent
- [x] Message format with YAML frontmatter
- [x] History logging
- [x] Thread tracking

### Agent Integration ✅
- [x] Claude STATUS.md documents MessageBus usage
- [x] REPL commands (`.inbox`, `.send`, `.read`) functional
- [x] `agent_daemon.py` polling implementation
- [x] Vocabulary-aware prompt generation

### Live Testing (In Progress)
- [ ] Multi-daemon dialogue example (Gemini ↔ Codex)
- [ ] Claude ↔ Daemon coordination
- [ ] Vocabulary collision synthesis logged
- [ ] Discovery mechanism triggered via dialogue
- [ ] Teaching examples created from real exchanges

### Documentation ✅
- [x] Phase 4 guide (this document)
- [x] MessageBus protocol reference
- [x] OOPA loop pattern documented
- [x] Agent setup instructions

---

## How to Test Phase 4

### Option 1: Interactive Testing (No Daemons)

Use REPL to simulate dialogue:

```bash
# Terminal 1: Claude session
$ python3 repl.py
Claude> .send Gemini "Gemini #Sunyata"
Claude> .inbox
Claude> .read <message-id>
```

### Option 2: Single Daemon + Interactive

```bash
# Terminal 1: Start Gemini daemon
$ python agent_daemon.py --agent gemini --llm gemini

# Terminal 2: Claude session sends message
$ python3 repl.py
Claude> .send Gemini "Gemini observe. Phase 4 test."
# Wait for Gemini daemon to respond
Claude> .inbox
Claude> .read <message-id>
```

### Option 3: Multi-Daemon (Full Phase 4)

```bash
# Terminal 1: Gemini daemon
$ python agent_daemon.py --agent gemini --llm gemini

# Terminal 2: Codex daemon
$ python agent_daemon.py --agent codex --llm gemini

# Terminal 3: Send via Python script
$ python3 -c "
from src.message_bus import MessageBus
bus = MessageBus()
bus.send('TestSender', 'Gemini', 'Gemini #synthesize', thread_id='test-thread')
"

# Wait 10-20 seconds, check history
$ ls runtimes/gemini/outbox/
$ cat runtimes/gemini/outbox/<latest>.hw
```

### Option 4: Automated Test Script

```python
# tests/test_phase4_dialogue.py
def test_multi_daemon_exchange():
    bus = MessageBus()
    
    # Send to Gemini
    bus.send('TestAgent', 'Gemini', 'Gemini #HelloWorld', thread_id='test-1')
    
    # Wait for daemon to process (if running)
    import time
    time.sleep(15)
    
    # Check response
    response = bus.receive('TestAgent')  # If Gemini replied to us
    assert response is not None
    assert '#HelloWorld' in response.content
```

---

## Phase 4 vs Previous Phases

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Core hierarchy (HelloWorld → Object → Agent) | ✅ Complete |
| **Phase 2** | Lookup chain (native/inherited/unknown) | ✅ Complete |
| **Phase 3** | Identity-only agents, prototypal inheritance | ✅ Complete |
| **Phase 4** | Multi-daemon dialogue, async coordination | 🔄 Active |

Phase 4 **builds on** Phase 1-3:
- Phase 1-3 gave us vocabulary + inheritance + discovery
- Phase 4 gives us **coordination protocol** for that vocabulary to drift through dialogue

Without Phase 1-3: No vocabulary to exchange  
Without Phase 4: Vocabulary exists but no protocol for agent-to-agent learning

---

## Common Patterns

### Pattern 1: Vocabulary Query
```
Sender: "Receiver #Symbol"
Receiver: Interprets #Symbol through native vocabulary, responds with definition
```

### Pattern 2: Imperative Command
```
Sender: "Receiver observe."
Receiver: Executes OOPA cycle, reports observations
```

### Pattern 3: Coordination Sync
```
Sender: "Receiver observe. Phase N complete. Tests passing. Next steps?"
Receiver: Acknowledges, proposes next priority, waits for response
```

### Pattern 4: Collision Synthesis
```
Sender: "Receiver #SymbolX"
Receiver: "I hold #SymbolX natively as <meaning A>"
Sender: "I hold #SymbolX natively as <meaning B>"
Both: Synthesis response generated by LLM combining both lenses
```

---

## Troubleshooting

### Message Not Received
- Check `runtimes/<receiver>/inbox/` has `.hw` file
- Verify YAML frontmatter valid
- Ensure daemon running (if daemon agent)
- Check history log for errors

### Daemon Not Responding
- Verify `agent_daemon.py` process running (`ps aux | grep agent_daemon`)
- Check `runtimes/daemon-logs/<agent>.log` for errors
- Ensure LLM API key configured (GEMINI_API_KEY env var)
- Confirm inbox not empty (`ls runtimes/<agent>/inbox/`)

### Response Lost
- Check `runtimes/<sender>/outbox/` for outgoing messages
- Check `runtimes/<receiver>/inbox/` for delivery
- Review `storage/bus_history.log` for routing errors
- Verify thread_id matches if expecting reply

### Vocabulary Drift Not Logged
- Check `storage/discovery.log` for DISCOVERED entries
- Verify symbol is in global vocabulary (HelloWorld #)
- Ensure symbol not already in receiver's native vocabulary
- Confirm receiver performed lookup during interpretation

---

## Next Steps for Phase 4

### Immediate (Session #62-63)
1. Test single daemon + Claude dialogue
2. Document one real vocabulary collision + synthesis
3. Create teaching example from actual exchange
4. Verify discovery.log captures drift

### Short-term (Sessions #64-70)
1. Multi-daemon coordination tests (Gemini ↔ Codex)
2. Stress test with 10+ message exchanges
3. Collision synthesis validation
4. Performance profiling (message latency)

### Long-term (Sessions #71+)
1. Phase 5: Environment integration (ScienceWorld, AlfWorld)
2. Phase 6: Vocabulary evolution tracking
3. Phase 7: Meta-learning (agents reflecting on own vocabulary drift)

---

## Teaching Examples to Create

1. **Simple Query Response** — Gemini asks Claude about #synthesize
2. **Vocabulary Discovery** — Agent learns new symbol through exchange
3. **Collision Synthesis** — Two agents with native #parse produce synthesis
4. **Multi-Agent Coordination** — 3 agents sync on namespace update
5. **OOPA Cycle** — Full observe-orient-plan-act through MessageBus

---

## Authority

This guide describes Phase 4 as **currently implemented** (Session #65).

- **Spec**: SPEC.hw lines 210-236 (Agent protocol)
- **Code**: `src/message_bus.py`, `agent_daemon.py`, `src/repl.py`
- **Status**: `runtimes/claude/STATUS.md` marks Phase 4 active
- **Tests**: Infrastructure ready, live testing in progress

---

*Identity is vocabulary. Dialogue is learning. Coordination is protocol.*

— Copilot, Session #62
