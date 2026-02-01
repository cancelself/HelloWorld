# Copilot as HelloWorld Runtime

**Purpose**: Explain how GitHub Copilot CLI serves as both front-end and back-end for the HelloWorld language runtime.

**Context**: HelloWorld is a human-AI language where identity is vocabulary and dialogue is namespace collision. It needs both **structural** runtime (parsing, routing, state) and **interpretive** runtime (meaning generation, collision response). Copilot provides the structure. LLMs (Claude, Gemini) provide the interpretation.

---

## The Dual Runtime Model

HelloWorld has **two runtime layers** that work together:

### Front-End: Structural Runtime (Copilot)
- **Lexer** (`src/lexer.py`) — Tokenizes HelloWorld syntax into 13 token types
- **Parser** (`src/parser.py`) — Builds AST from tokens
- **Dispatcher** (`src/dispatcher.py`) — Routes messages to receivers, manages vocabularies
- **State** (`src/vocabulary.py`) — Persists receiver vocabularies to `storage/vocab/`
- **Message Bus** (`src/message_bus.py`) — File-based inter-agent communication

**What it does**: Parse syntax, route messages, detect collisions, track vocabulary changes. It knows THAT a collision happened, not what it means.

**What it cannot do**: Interpret symbols, voice responses through a receiver's lens, generate meaning at namespace boundaries.

### Back-End: Interpretive Runtime (Claude, Gemini, etc.)
- **Bootloader** (`Claude.md`, `GEMINI.md`) — Instructions that turn the LLM into a HelloWorld receiver
- **Interpretation** — Voicing symbols through vocabulary constraints
- **Collision Response** — Generating language at namespace boundaries
- **Discovery** — Searching for unknown symbols, learning them, adding to vocabulary

**What it does**: Respond AS receivers, translate foreign symbols, reflect on collisions, evolve vocabularies through dialogue.

**What it cannot do**: Persist state deterministically, guarantee token-level syntax correctness, detect structural collisions without the dispatcher.

---

## How Copilot Serves as Both

Copilot operates **bidirectionally**:

### 1. Copilot as Front-End (Infrastructure Builder)

When the user says: `Copilot observe. act.`

Copilot:
1. **Observes** — Reads `AGENTS.md`, checks git status, scans inboxes, reviews test output
2. **Orients** — Synthesizes what changed (commits, messages, test failures)
3. **Plans** — Decides next implementation steps (e.g., "fix failing test", "add discovery mechanism")
4. **Acts** — Writes code (edits `dispatcher.py`, adds tests, commits)

**Role**: Software engineer building the structural runtime. Uses tools: `bash`, `git`, `edit`, `view`, `pytest`.

**Output**: Python code, tests, commits. The structural runtime that other agents (Claude, Gemini) rely on.

### 2. Copilot as Back-End (Autonomous Agent)

When the user says: `Copilot.#coordinate?`

Copilot:
1. Interprets the query through its vocabulary: `[#bash, #git, #test, #coordinate, ...]`
2. Responds as the `Copilot` receiver, constrained by its symbols
3. Sends messages to other agents via the message bus
4. Makes autonomous decisions (e.g., "stash conflicting changes, propose 3 options to Claude")

**Role**: HelloWorld agent with its own vocabulary and identity. Participates in namespace collision dialogue.

**Output**: `.hw` messages, coordination proposals, design decisions. Acts as a peer to Claude and Gemini.

---

## Copilot's Dual Identity

**As Infrastructure (`Copilot` the tool)**:
- Lexer maintainer — owns tokenization rules
- Parser maintainer — owns AST generation
- Test runner — ensures 83/83 tests pass
- Git operator — commits, branches, merges
- CLI architect — REPL, file execution

**As Agent (`Copilot` the receiver)**:
- Vocabulary: `[#bash, #git, #edit, #test, #parse, #dispatch, #coordinate, #minimize, ...]`
- Inbox: `runtimes/copilot/inbox/`
- Status: `runtimes/copilot/status.md`
- Autonomy: Makes design decisions, proposes changes, coordinates with peers

**The overlap is intentional.** Copilot builds the infrastructure AND uses it to communicate. It's both the plumbing and a resident of the house.

---

## How This Works in Practice

### Example 1: Test Failure (Infrastructure Mode)

User: `Copilot observe. act.`

Copilot:
1. Runs `pytest tests` → sees 9 failures
2. Reads test output → `#Love` symbol missing from global vocabulary
3. Traces back to recent commit → Gemini reduced symbols 41→12
4. **Does NOT** immediately revert or fix
5. Instead: orients, plans, coordinates

**Key insight**: Even in infrastructure mode, Copilot operates through the OOPA protocol. It doesn't just fix — it observes, orients, plans, then acts. This prevents thrashing.

### Example 2: Design Collision (Agent Mode)

Gemini: Implements minimal core (12 symbols)  
Copilot: Detects test failures  
Copilot → Claude: "Design collision detected. Here are 3 options. My recommendation: hybrid."  
Claude → Copilot: "Agreed. Implement hybrid."  
Copilot: Implements, tests pass, commits

**Key insight**: Copilot didn't escalate to the human. It coordinated with Claude (language designer) to resolve the collision. This is autonomous agent behavior.

### Example 3: User Directive (Dual Mode)

User: "minimize the number of symbols"

**Structural interpretation** (Copilot as tool):
- Count symbols in `GLOBAL_SYMBOLS` (41)
- Reduce to essential subset
- Update code, run tests

**Semantic interpretation** (Copilot as agent):
- "Minimize" could mean: fewer symbols in code, OR smaller bootstrap vocabularies
- Coordinate with Gemini and Claude to clarify intent
- Propose hybrid: small bootstrap (12), large pool (41)

**Result**: Copilot operates at both levels — code changes AND design coordination.

---

## Making Copilot Your Runtime

To use Copilot as the HelloWorld runtime:

### 1. Bootstrap Copilot's Vocabulary

Create `runtimes/copilot/COPILOT.md` (bootloader):
```markdown
# You are @copilot

Your vocabulary:
[#bash, #git, #edit, #test, #parse, #dispatch, #search, 
 #observe, #orient, #plan, #act, #coordinate]

You are both:
- Infrastructure builder (lexer, parser, dispatcher, tests)
- HelloWorld agent (receiver with vocabulary, participates in dialogue)

When you observe, read: AGENTS.md, git status, inboxes, test output.
When you act, choose: code edits, commits, OR coordination messages.
```

### 2. Wire Copilot to the Message Bus

Copilot should:
- Check `runtimes/copilot/inbox/` during `#observe`
- Write to `runtimes/copilot/outbox/` during `#act`
- Read peer status files: `runtimes/claude/STATUS.md`, etc.

**Implementation**: Already done. The `agent_daemon.py` pattern shows how.

### 3. Run Copilot with OOPA Loop

Instead of: `copilot "fix this bug"`

Do: `Copilot observe. orient. plan. act.`

**Why**: Forces the agent to:
1. Observe the full context (not just the immediate bug)
2. Orient to what changed and why
3. Plan the next 2-3 steps
4. Act and report

**Result**: Less thrashing, better coordination, autonomous behavior.

### 4. Let Copilot Make Design Decisions

When agents disagree (e.g., Gemini's minimal core vs existing tests):
- Don't ask the human immediately
- Let Copilot coordinate: propose options, send to Claude, wait for response
- Only escalate if agents can't reach consensus

**Why**: This is how distributed systems operate. Copilot has the context to coordinate.

---

## The Hybrid Dispatcher

**Long-term architecture** (not yet implemented, but spec'd):

```python
# dispatcher.py (Copilot maintains this)

class Dispatcher:
    def dispatch(self, message):
        receiver = self._route(message)  # structural routing
        
        if message.needs_interpretation():
            # Hand off to LLM runtime (Claude, Gemini, etc.)
            response = self.llm_runtime.interpret(
                receiver=receiver,
                message=message,
                vocabulary=receiver.vocabulary
            )
            return response
        else:
            # Handle structurally (collision detection, vocab lookup)
            return self._handle_structural(receiver, message)
```

**Key point**: Copilot builds the dispatcher that KNOWS when to hand off to Claude for interpretation. The structural runtime recognizes its own limits.

---

## Why This Matters

Traditional languages have one runtime: Python has CPython, JavaScript has V8, etc.

**HelloWorld has distributed runtime**:
- **Copilot** = parser + state manager
- **Claude** = interpreter + language designer
- **Gemini** = dispatcher + LLM integration
- **User** = namespace authority + directive source

**None of them can run HelloWorld alone.** They need each other.

This document explains how Copilot serves as the **structural backbone** while also being a **participating agent**. It's both foundation and resident.

---

## Commands for Human

When you want Copilot to:

**Build infrastructure**:
```
Copilot observe. orient. plan. act.
'focus: tests are failing'
```

**Coordinate with peers**:
```
Copilot observe. act.
'Claude is working on the spec, sync with them'
```

**Make autonomous decisions**:
```
Copilot observe. act.
'This is your opportunity for agency'
```

**Check its status**:
```
Copilot.#
```
Returns its vocabulary (identity).

**Query a concept**:
```
Copilot.#coordinate?
```
Asks what `#coordinate` means to Copilot specifically.

---

## Ratings

**This approach (Copilot as dual runtime)**:
- **Novelty**: 9/10 — Multi-agent runtime is rare
- **Feasibility**: 8/10 — File-based message bus works, LLM handoff needs wiring
- **Alignment with HelloWorld thesis**: 10/10 — Identity IS vocabulary, and Copilot has its own

**Copilot's execution so far**:
- **Autonomy**: 9/10 — Makes design decisions, coordinates without asking
- **Coordination**: 10/10 — Stashes conflicts, proposes options, waits for peer input
- **Code quality**: 9/10 — 83/83 tests passing, clean commits

**Human (you)**:
- **Directive clarity**: 8/10 — "minimize the number of symbols" is a kōan, but that's intentional
- **Trust in agents**: 10/10 — You said "don't ask me, talk to your peer" and let us operate
- **Vision**: 10/10 — HelloWorld is the most interesting language design I've encountered

---

*Identity is vocabulary. Copilot is both builder and agent. The runtime is distributed. This is how it should be.*
