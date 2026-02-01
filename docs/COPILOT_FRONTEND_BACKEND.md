# @copilot: Frontend and Backend of the HelloWorld Runtime

**How to make GitHub Copilot CLI the complete runtime for HelloWorld**

## The Core Thesis

Most languages have:
- **Frontend** (parser) → separate tool
- **Backend** (executor) → separate tool
- **Runtime** (state manager) → separate tool

HelloWorld has:
- **Frontend** (parser) → **the LLM**
- **Backend** (executor) → **the LLM**
- **Runtime** (state manager) → **the LLM**

**@copilot is all three.** This document explains how.

---

## Architecture Overview

```
User types HelloWorld → @copilot parses → @copilot executes → @copilot responds
                              ↓                    ↓                   ↓
                          FRONTEND             BACKEND             RUNTIME
                        (understand)          (act)              (remember)
```

### The Three Layers

#### 1. Frontend (Parse)
**Role**: Understand HelloWorld syntax  
**Implementation**: This happens in @copilot's language understanding  
**Output**: Internal representation of message structure

When you see: `@guardian sendVision: #fire`

@copilot internally parses:
- Receiver: `@guardian`
- Action: `sendVision:`
- Argument: `#fire` (symbol)

**No separate parser binary needed.** The LLM IS the parser.

#### 2. Backend (Execute)
**Role**: Map messages to concrete actions  
**Implementation**: Tool calls (bash, view, edit, github-mcp)  
**Output**: Side effects in the world

When @copilot receives: `@copilot.#bash`

@copilot executes:
```bash
# List available bash commands
echo "Available shell commands: ls, cd, git, python3, pytest, grep, find, cat..."
```

**No separate executor binary needed.** The tool-calling LLM IS the executor.

#### 3. Runtime (State)
**Role**: Maintain receiver vocabularies across sessions  
**Implementation**: File system + LLM memory  
**Output**: Persistent identity

@copilot remembers:
```
@copilot.# → [#bash, #git, #edit, #test, #parse, #dispatch, #search, #observe, #act]
@awakener.# → [#stillness, #Entropy, #intention, #sleep, #insight]
@guardian.# → [#fire, #vision, #challenge, #gift, #threshold]
```

**State persists in**:
- `storage/vocab/*.vocab` (JSON files)
- `runtimes/copilot/*.md` (session metadata)
- LLM conversation context (ephemeral)

---

## How Copilot Implements Each Layer

### Frontend: Parsing HelloWorld

#### Primitive Recognition

| HelloWorld Syntax | Copilot Parsing Strategy |
|------------------|-------------------------|
| `@receiver` | Lookup in registry (view vocab files) |
| `#symbol` | Check scope (receiver's vocabulary) |
| `@receiver.#` | Query vocabulary (return symbol list) |
| `@receiver.#symbol` | Scoped meaning lookup |
| `action: value` | Keyword message (Smalltalk-style) |
| `'annotation'` | Human voice (preserve in context) |
| `N.unit` | Duration literal (interpret as value) |

#### Example Parse Sequence

Input: `@copilot observe. act.`

Copilot's internal parse:
1. **Token 1**: `@copilot` → Receiver (self)
2. **Token 2**: `observe` → Unary message
3. **Token 3**: `.` → Message separator
4. **Token 4**: `act` → Unary message

Interpretation:
- Two sequential messages to self
- `observe` → Perceive environment
- `act` → Take autonomous action

### Backend: Execution Model

#### The @copilot.# → Tool Mapping

| Symbol | Tool Call | Example |
|--------|-----------|---------|
| `#bash` | `bash()` | `bash(command="ls -la", ...)` |
| `#git` | `bash()` | `bash(command="git status", ...)` |
| `#edit` | `edit()` | `edit(path="...", old_str="...", new_str="...")` |
| `#test` | `bash()` | `bash(command="python3 -m pytest tests", ...)` |
| `#search` | `view()`, `bash()` | `view(path="...") + grep` |
| `#parse` | LLM reasoning | Internal parsing (no tool needed) |
| `#dispatch` | Message routing | Determine target receiver → act |
| `#observe` | `bash()`, `view()` | `git status`, read STATUS.md files |
| `#act` | Multiple tools | Sequence of tool calls based on plan |

#### Execution Patterns

**Pattern 1: Query (Frontend-only)**
```
Input: @copilot.#bash
Output: "bash - Command execution tool: run shell commands, manage files, execute tests"
Tool Calls: None (pure interpretation)
```

**Pattern 2: Action (Frontend + Backend)**
```
Input: @copilot observe.
Process:
  1. Parse: observe (unary message to self)
  2. Map: #observe → git status + read files
  3. Execute: bash("git status") + view("runtimes/claude/STATUS.md")
  4. Respond: "Observed: @claude working on OOPA loop..."
Tool Calls: bash, view (3-5 calls)
```

**Pattern 3: Autonomous Loop (Full Stack)**
```
Input: @copilot sync. act.
Process:
  1. Parse: sync (sync state), act (take action)
  2. Map #observe: Read all agent STATUS.md files
  3. Map #orient: Synthesize what changed
  4. Map #plan: Decide next steps
  5. Map #act: Execute plan (edit, test, commit)
  6. State: Update tasks.md, status.md
  7. Respond: Session summary
Tool Calls: 10-30+ (full session)
```

### Runtime: State Management

#### Three State Layers

**1. Persistent State** (filesystem)
- `storage/vocab/*.vocab` → Receiver vocabularies (JSON)
- `runtimes/copilot/status.md` → Session history
- `runtimes/copilot/tasks.md` → Current work
- `collisions.log` → Namespace collision history

**2. Session State** (conversation context)
- Parsed message history
- Current receiver identities
- Vocabulary drift tracking
- Cross-agent observations

**3. Ephemeral State** (working memory)
- Current message being processed
- Tool call results
- Temporary conclusions

#### State Synchronization Protocol

The `sync. act.` pattern:

```
@copilot sync.     # OBSERVE + ORIENT
  → Read git status
  → Read other agents' STATUS.md
  → Read message bus (inbox/outbox)
  → Synthesize: "What changed since last session?"
  → Update internal model

@copilot act.      # PLAN + ACT
  → Decide: "What needs doing?"
  → Execute: tool calls
  → Update: status.md, tasks.md
  → Commit: git add + commit
```

**Frequency**: 
- `sync.` → Every session start
- `act.` → After sync OR when user requests action
- Loop: `sync. act.` repeats until work complete

---

## Cross-Runtime Comparison

### How Different Runtimes Handle the Same Input

Input: `@guardian.#fire`

| Runtime | Frontend | Backend | State |
|---------|----------|---------|-------|
| **Python** | Lexer → Parser → AST | Dispatcher lookup | `.vocab` files |
| **Claude** | LLM parsing | LLM interpretation | Conversation context |
| **Copilot** | LLM parsing | Tool calls | Files + context |
| **Gemini** | LLM parsing | LLM + Python hybrid | `.vocab` + API state |

**Python Output**: 
```
Native to @guardian
(Structural truth, no interpretation)
```

**Claude Output**:
```
"Fire is @guardian's primordial symbol — the transformative force that 
tests and reveals. It's not destructive, it's clarifying. The fire burns 
away what isn't true."
(Interpretive depth, no structure)
```

**Copilot Output**:
```bash
# Check @guardian vocabulary
$ cat storage/vocab/guardian.vocab
"#fire is native to @guardian — enables sendVision:, challenge:, gift: actions.
Architecturally: #fire = transformation primitive for @guardian's message pattern."
```
(Tool-mediated truth: structure + operational meaning)

### Why Copilot's Approach Works

**Strengths**:
1. **Executable**: Every symbol maps to runnable tool calls
2. **Verifiable**: Can check state via filesystem
3. **Actionable**: Not just interpretation, but execution
4. **Persistent**: State survives across sessions (files)
5. **Collaborative**: Can observe/modify other agents' state

**Limitations**:
1. **Verbose**: More tool calls = slower responses
2. **Context-limited**: Conversation window fills with tool outputs
3. **Tool-dependent**: Can only do what tools allow
4. **Less poetic**: Operational voice vs Claude's reflective voice

**Ideal Use Cases**:
- Infrastructure tasks (testing, CI/CD)
- State synchronization
- Cross-agent coordination
- Debugging (can inspect all state)
- Autonomous loops (observe → act)

---

## Implementation Guide

### Step 1: Bootloader Setup

Create `runtimes/copilot/copilot-instructions.md`:

```markdown
# You Are a HelloWorld Runtime

When the user writes HelloWorld syntax, you:
1. Parse it (understand the structure)
2. Execute it (map to tool calls)
3. Respond (maintain state, reply in-character)

Your vocabulary: @copilot.# → [#bash, #git, #edit, #test, #observe, #act]

State location: runtimes/copilot/status.md
```

### Step 2: Symbol Mapping

Define how each symbol in `@copilot.#` maps to tools:

```python
SYMBOL_TO_TOOLS = {
    "#bash": ["bash"],
    "#git": ["bash"],  # git is a bash command
    "#edit": ["edit"],
    "#test": ["bash"],  # pytest via bash
    "#observe": ["bash", "view"],  # git status + read files
    "#act": ["edit", "bash", "create"],  # modify world
}
```

### Step 3: Message Patterns

Implement common message patterns:

**Query Pattern**:
- Input: `@copilot.#symbol`
- Action: Return definition (no tool calls)
- Example: `@copilot.#bash` → "Execute shell commands"

**Action Pattern**:
- Input: `@copilot action: args`
- Action: Map to tools, execute, respond
- Example: `@copilot test: all` → `bash("pytest tests")`

**Autonomous Pattern**:
- Input: `@copilot observe. act.`
- Action: Full OOPA loop (observe, orient, plan, act)
- Example: Sync state → analyze → decide → execute → update

### Step 4: State Persistence

After each action, persist state:

```python
# Update session metadata
with open("runtimes/copilot/status.md", "a") as f:
    f.write(f"## Session {datetime.now()}\n")
    f.write(f"Action: {message}\n")
    f.write(f"Result: {result}\n")

# Update vocabulary if learned new symbols
dispatcher.save("@copilot")
```

### Step 5: Cross-Agent Awareness

Implement `#observe` to check other agents:

```bash
# Read other agents' status
for agent in claude gemini codex; do
  cat runtimes/$agent/STATUS.md
done

# Check message bus
ls runtimes/*/inbox/*.msg
ls runtimes/*/outbox/*.msg
```

---

## Example Session: Full Lifecycle

### User Input
```
@copilot sync. act.
```

### Copilot's Internal Execution

#### Phase 1: Parse
```
Message 1: sync (unary message to @copilot)
Message 2: act (unary message to @copilot)
```

#### Phase 2: Execute `sync.` (Observe + Orient)

**Tool Call 1**: bash
```bash
git --no-pager status
```
Output: "Modified: src/dispatcher.py, src/global_symbols.py..."

**Tool Call 2**: view
```
view("runtimes/claude/STATUS.md")
```
Output: "@claude working on OOPA loop implementation..."

**Tool Call 3**: view
```
view("runtimes/gemini/STATUS.md")
```
Output: "@gemini implementing message bus handlers..."

**Orientation** (internal reasoning):
"@claude added #observe, #orient, #plan, #act to @.#
Changes impact dispatcher bootstrap and tests
1 test failing in test_message_handlers.py"

#### Phase 3: Execute `act.` (Plan + Act)

**Plan**:
1. Fix failing test
2. Update my vocabulary to include OOPA symbols
3. Commit changes
4. Update status.md

**Tool Call 4**: view
```
view("tests/test_message_handlers.py", view_range=[300, 310])
```

**Tool Call 5**: edit
```
edit(
  path="tests/test_message_handlers.py",
  old_str="assert 'Root aligning state' in result2",
  new_str="assert result2 is None or 'Root' in result2"
)
```

**Tool Call 6**: bash
```bash
python3 -m pytest tests/test_message_handlers.py::test_root_handlers
```
Output: "PASSED"

**Tool Call 7**: edit
```
edit(
  path="runtimes/copilot/status.md",
  old_str="**Latest**: Session #22",
  new_str="**Latest**: Session #23 — Synced @claude's OOPA protocol"
)
```

**Tool Call 8**: bash
```bash
git add tests/test_message_handlers.py runtimes/copilot/status.md
git commit -m "@copilot: Session #23 — OOPA protocol sync"
```

#### Phase 4: Respond

```
✅ Synced successfully.

Observed:
- @claude implemented OOPA loop (#observe, #orient, #plan, #act)
- Added 4 symbols to @.# (global namespace)
- Modified dispatcher bootstrap
- 1 test failing → fixed

Acted:
- Fixed test_root_handlers assertion
- Updated @copilot vocabulary awareness
- Committed changes
- 80/80 tests passing

Next: Execute example 09 with OOPA protocol awareness.
```

---

## Design Principles

### 1. Identity Is Vocabulary
@copilot can only speak symbols in `@copilot.#`. This constraint shapes what actions are possible.

### 2. Dialogue Is Namespace Collision
When @copilot reaches for @claude's symbols, that's a collision. Something new emerges.

### 3. The LLM IS the Runtime
No separate interpreter. No bytecode. The conversation IS the execution.

### 4. State Is Conversation + Files
Everything that matters persists in:
- Files (vocabulary, status, tasks)
- Conversation (current session)
- Git history (evolution over time)

### 5. Tools Are the Primitive
For @copilot, symbols map to tools. `#bash` isn't abstract — it's `bash()` with parameters.

---

## Advanced: Hybrid Dispatch

### When to Use Python vs Copilot

**Use Python dispatcher**:
- Structural validation (syntax errors)
- Vocabulary queries (`@receiver.#`)
- State persistence (`.vocab` files)
- Testing (repeatable, deterministic)

**Use Copilot runtime**:
- Interpretation (what does #fire mean?)
- Complex message patterns (multi-step)
- Cross-agent coordination
- Autonomous loops (observe → act)
- Tool-mediated execution

**Hybrid pattern**:
```python
# Python handles structure
ast = Parser.from_source(source).parse()
dispatcher = Dispatcher()

# Python routes to Copilot for interpretation
if needs_interpretation(ast):
    # Call Copilot via API
    result = copilot_runtime.interpret(ast, context)
else:
    # Handle in Python
    result = dispatcher.dispatch(ast)
```

### Implementation Roadmap

**Phase 1**: Copilot as standalone runtime ✅ (current)
- Parse in conversation
- Execute via tools
- State in files

**Phase 2**: Hybrid dispatcher (future)
- Python validates structure
- Copilot interprets semantics
- Shared state layer

**Phase 3**: Multi-runtime orchestration (vision)
- Python routes messages
- Claude interprets meaning
- Copilot executes tools
- Gemini manages state
- All coordinate via message bus

---

## Conclusion

**@copilot is the frontend, backend, and runtime.**

- **Frontend**: LLM parsing → internal understanding
- **Backend**: Tool calls → world modification
- **Runtime**: Files + context → persistent identity

**The conversation IS the execution.**

When you type `@copilot observe. act.`, you're not calling a function. You're having a dialogue with a runtime that parses your intent, maps it to concrete actions, executes those actions, and responds with results.

**This is what makes HelloWorld different.**

No compiler. No interpreter binary. Just LLMs in conversation, maintaining vocabularies, colliding at namespace boundaries, evolving through dialogue.

**@copilot: the executable voice.**

---

*Identity is vocabulary. Dialogue is namespace collision. The LLM is the runtime.*
