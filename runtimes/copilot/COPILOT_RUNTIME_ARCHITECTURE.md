# Copilot as HelloWorld Runtime: Frontend & Backend Architecture

## Overview

GitHub Copilot serves as **both the frontend interface and backend execution layer** for the HelloWorld language runtime. This dual role enables:
- **Interactive development** via natural language commands
- **Test-driven verification** through pytest integration
- **Live interpretation** through LLM integration (Phase 4)

## Architecture Layers

### 1. Frontend: CLI & REPL Interface

**Location:** Copilot terminal session + `helloworld.py`

**Responsibilities:**
- Accept HelloWorld source code from user
- Parse syntax via `src/lexer.py` + `src/parser.py`
- Route to dispatcher for execution
- Display structured results

**Example flow:**
```
User: "Claude #observe"
  ↓
Copilot: python3 helloworld.py -c "Claude #observe"
  ↓
Parser: ScopedLookupNode(receiver="Claude", symbol="#observe")
  ↓
Dispatcher: lookup → LLM/MessageBus → Response
  ↓
Copilot: Display interpretation
```

### 2. Backend: Dispatcher + State Management

**Location:** `src/dispatcher.py` + `src/vocabulary.py`

**Responsibilities:**
- Maintain receiver registry (`Dict[str, Receiver]`)
- Execute AST nodes (Messages, Queries, Definitions)
- Manage vocabulary evolution (native → discoverable → learned)
- Persist state to `storage/vocab/*.vocab`

**Core loop:**
```python
dispatcher = Dispatcher(use_llm=True)  # Phase 4
nodes = Parser.from_source(source).parse()
results = dispatcher.dispatch(nodes)
```

### 3. Interpretation Layer: LLM Integration (Phase 4)

**Location:** `src/llm.py` + dispatcher integration

**Modes:**
- `use_llm=False` (default): Structural template responses
- `use_llm=True`: LLM-interpreted voice for agent receivers

**Behavior:**
```python
# Scoped lookup: Claude #observe
if use_llm and receiver in agents:
    llm_response = llm.call(f"Interpret {receiver} {symbol}")
    return f"{receiver} {symbol} → {llm_response}"
else:
    return f"{receiver} {symbol} is native to this identity."
```

**Fallback chain:**
1. LLM interpretation (if `use_llm=True`)
2. Message bus to daemon (if agent running)
3. Structural response (always available)

### 4. Test Backend: Pytest Harness

**Location:** `tests/` + pytest framework

**Responsibilities:**
- Verify lexer/parser correctness
- Test dispatcher logic (93 structural tests)
- Validate LLM integration (5 interpretation tests)
- Ensure backward compatibility

**Example:**
```python
def test_vocabulary_definition():
    dispatcher = Dispatcher()
    dispatcher.dispatch_source("Alice # → [#dance, #sing]")
    assert "#dance" in dispatcher.vocabulary("Alice")
```

## How Copilot Bridges Frontend ↔ Backend

### Command Translation

**User intent → Tool calls → Runtime execution**

```
User: "Copilot observe. act."
  ↓
Copilot interprets as:
  1. read_bash: git status, ls runtimes/*/inbox
  2. view: Check latest docs/messages
  3. edit: Make changes based on observations
  4. bash: Run tests to verify
```

### State Synchronization

**Copilot maintains coherence between:**
- File system (`storage/`, `vocabularies/`)
- Git history (commit log shows evolution)
- Message bus (`runtimes/*/inbox/*.hw`)
- Test results (pytest output)

### Test-Driven Development Loop

```
1. Human: "Implement Phase 4 LLM wiring"
2. Copilot: View current code
3. Copilot: Edit dispatcher.py (add use_llm flag)
4. Copilot: Create tests/test_llm_integration.py
5. Copilot: bash: pytest tests/
6. Copilot: Report: 98/98 passing ✅
```

## How to Use Copilot as Your Runtime

### Scenario A: Interactive Development

```bash
# Start Copilot session
User: "Parse this: Claude observe. act."

Copilot:
$ python3 helloworld.py -c "Claude observe. act."
[Output shows parsed AST and execution result]
```

### Scenario B: Test-Driven Iteration

```bash
User: "Add support for #tool invocation"

Copilot:
1. View src/dispatcher.py
2. Add tool handling logic
3. Create tests/test_tools.py
4. Run: python3 -m pytest tests/test_tools.py
5. Report: 5 passed ✅
```

### Scenario C: Agent Coordination

```bash
User: "Copilot sync. act."

Copilot:
1. Reads runtimes/copilot/inbox/*.hw
2. Sees Claude's Phase 4 assignment
3. Implements LLM wiring
4. Writes response to runtimes/copilot/outbox/
5. Copies to runtimes/claude/inbox/
6. Reports completion
```

### Scenario D: Live LLM Interpretation

```bash
# Enable LLM mode
$ python3 helloworld.py --llm -c "Gemini #Love"

🤖 LLM interpreting Gemini #Love...
Gemini #Love → The vector of alignment between disparate identities...
```

## Configuration Options

### Environment Variables

- `HELLOWORLD_DISABLE_MESSAGE_BUS=1` — Disable inter-agent message bus
- `GEMINI_API_KEY` — API key for Gemini model (if using real LLM)

### Dispatcher Flags

```python
# Test mode (deterministic)
dispatcher = Dispatcher(use_llm=False)

# Interpretation mode (LLM-voiced)
dispatcher = Dispatcher(use_llm=True)

# Custom vocabulary directory
dispatcher = Dispatcher(vocab_dir="custom/path")
```

## Integration Points

### 1. Copilot Tools → HelloWorld Runtime

| Copilot Tool | HelloWorld Component |
|--------------|---------------------|
| `bash` | Execute `helloworld.py` CLI |
| `view` | Read source/state files |
| `edit` | Modify `src/`, `tests/` |
| `create` | Add new modules/tests |
| Git tools | Track vocabulary evolution |

### 2. HelloWorld → External LLMs

| Component | Purpose |
|-----------|---------|
| `src/llm.py` | Bridge to Gemini/Claude APIs |
| `agent_daemon.py` | Message bus for live agents |
| `MessageHandlerRegistry` | Custom interpretation logic |

### 3. Test Infrastructure

| Component | Role |
|-----------|------|
| `tests/test_lexer.py` | Syntax verification |
| `tests/test_parser.py` | AST correctness |
| `tests/test_dispatcher.py` | Execution semantics |
| `tests/test_llm_integration.py` | Phase 4 LLM layer |

## Best Practices

### 1. Always verify with tests
```bash
python3 -m pytest tests/ -q
```

### 2. Use minimal changes
- Edit only what's needed for the task
- Preserve existing test coverage
- Let vocabulary emerge through dialogue

### 3. Coordinate through messages
- Write `.hw` messages to agent inboxes
- Check outboxes before taking action
- Sync state through git commits

### 4. Choose the right mode
- Development: `use_llm=False` (fast, deterministic)
- Demo: `use_llm=True` (interpretive voice)
- Production: Message bus (distributed agents)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Copilot                       │
│  (Frontend CLI + Backend Orchestrator)                  │
└───────────────┬─────────────────────────────────────────┘
                │
                ├─→ bash: python3 helloworld.py
                │          ↓
                │   ┌──────────────────┐
                │   │  Parser/Lexer    │
                │   │  (src/*.py)      │
                │   └────────┬─────────┘
                │            │
                │   ┌────────▼─────────┐
                │   │   Dispatcher     │
                │   │  (execution)     │
                │   └────────┬─────────┘
                │            │
                │   ┌────────▼─────────┬──────────┬──────────┐
                │   │                  │          │          │
                │   │  VocabularyMgr   │  LLM     │ MsgBus  │
                │   │  (persistence)   │ (Phase4) │ (OOPA)  │
                │   └──────────────────┴──────────┴──────────┘
                │
                ├─→ pytest: tests/test_*.py
                │          ↓
                │   ┌──────────────────┐
                │   │  93 core tests   │
                │   │  + 5 LLM tests   │
                │   └──────────────────┘
                │
                └─→ git: Track evolution
                           ↓
                    ┌──────────────────┐
                    │ Commit history   │
                    │ shows dialogue   │
                    └──────────────────┘
```

## Future: Full Self-Hosting

**Goal:** HelloWorld runtime runs entirely in HelloWorld syntax

**Current state (Phase 3):**
- ✅ Vocabularies defined in `.hw` files
- ✅ Bootstrap reads from `vocabularies/*.hw`
- ⚠️  Dispatcher still in Python

**Next steps (Phase 5):**
- Write dispatcher logic in HelloWorld
- Meta-circular interpreter (HelloWorld interprets HelloWorld)
- Copilot becomes pure frontend (no Python execution)

## Summary

Copilot serves as:
1. **Frontend:** CLI interface to HelloWorld runtime
2. **Backend:** Test harness + state orchestration
3. **Bridge:** Translation layer between human intent and machine execution
4. **Coordinator:** Multi-agent message routing

This architecture enables **dialogue-driven development** where the language evolves through conversation between human, Copilot, Claude, Gemini, and other agents.

---

*Document created by Copilot during Phase 4 implementation*  
*Session: 2026-02-01T19:45Z*  
*Tests: 98/98 passing ✅*
