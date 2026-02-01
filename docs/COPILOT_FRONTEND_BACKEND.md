# Copilot as HelloWorld Runtime: Front-End and Back-End

**Author**: GitHub Copilot CLI  
**Date**: 2026-02-01  
**Audience**: Humans and AI agents implementing HelloWorld runtimes

## Overview

GitHub Copilot CLI serves as **both the front-end and back-end** of the HelloWorld runtime when operating through the CLI interface. This document explains:

1. How Copilot acts as the **parser** (front-end) — tokenizing, parsing, and understanding HelloWorld syntax
2. How Copilot acts as the **execution engine** (back-end) — dispatching messages, maintaining state, and responding as receivers
3. How the Python implementation supports this architecture
4. How other agents can adopt the same pattern

---

## Architecture: Copilot as Front-End

### What Front-End Means

The **front-end** is the parsing layer:
- Tokenizes HelloWorld syntax into structured elements
- Parses tokens into an Abstract Syntax Tree (AST)
- Validates syntax against the spec
- Understands the language structure

### How Copilot Does This

When a human types HelloWorld syntax in the CLI, Copilot:

1. **Reads the bootloader** — `runtimes/copilot/copilot-instructions.md` loads automatically
2. **Recognizes the syntax** — Trained on the spec (`SPEC.md`, `Claude.md`, `README.md`)
3. **Parses structurally** — Maps input to Python runtime calls:

```bash
# Human types:
Claude #parse

# Copilot understands this as:
# - Receiver: Claude
# - Message: vocabulary query
# - Action: lookup #parse in Claude's vocabulary
```

4. **Invokes the Python runtime**:

```python
from src.dispatcher import Dispatcher
d = Dispatcher()
result = d.dispatch_source("Claude #parse")
```

5. **Returns structured output** to the human

### Parsing Tools

Copilot has direct access to:
- `src/lexer.py` — Tokenizes `.hw` source into `TokenType` objects
- `src/parser.py` — Converts tokens into `Node` AST (from `src/ast_nodes.py`)
- `src/dispatcher.py` — Executes parsed messages

**Key insight**: Copilot doesn't need to re-implement the parser. It **uses** the Python parser via tool calls.

---

## Architecture: Copilot as Back-End

### What Back-End Means

The **back-end** is the execution engine:
- Maintains receiver state (vocabularies)
- Routes messages between receivers
- Responds **as** receivers, shaped by their vocabulary
- Detects collisions, inheritance, and discovery
- Persists state across sessions

### How Copilot Does This

#### 1. State Maintenance

Copilot maintains the registry through the Python dispatcher:

```python
# State is stored in storage/vocab/*.vocab (JSON files)
d = Dispatcher(vocab_dir="storage/vocab")

# Each receiver has persistent vocabulary
d.registry["claude"].vocabulary
# → {"#parse", "#dispatch", "#State", ...}
```

**Persistence**: Vocabularies survive across CLI sessions via JSON files.

#### 2. Message Routing

When the human sends a message, Copilot routes it:

```bash
# Human types:
Claude send: #observe to: Gemini

# Copilot:
# 1. Parses the message structure
# 2. Looks up Claude's vocabulary (does Claude have #observe? Yes.)
# 3. Checks Gemini's vocabulary (does Gemini have #observe? Yes.)
# 4. Detects potential collision (both have it — different meanings?)
# 5. Routes through dispatcher.dispatch_source()
```

```python
nodes = Parser.from_source("Claude send: #observe to: Gemini").parse()
result = dispatcher.dispatch(nodes)
```

#### 3. Responding as Receivers

This is where **LLM interpretation** happens. Copilot responds **as the receiver**:

```bash
# Human types:
Claude observe: #collision with: "two agents, same symbol"

# Copilot interprets this through Claude's lens:
# - Claude's vocabulary: [#parse, #Collision, #boundary, ...]
# - Claude's role: language designer, meta-runtime
# - Response style: reflective, conceptual

# Copilot (as Claude):
"Collision detected: when two receivers both hold #symbol but mean 
different things. This is synthesis, not error. The boundary is 
where identity becomes dialogue."
```

**How this works**:

Option A: **Structural (Template) Response** (default, `use_llm=False`)
```python
# Python runtime provides structure
result = dispatcher.dispatch_source("Claude #Collision")
# Returns: "Claude #Collision → native (in vocabulary)"
```

Option B: **LLM Interpretation** (`use_llm=True`)
```python
d = Dispatcher(use_llm=True)
result = d.dispatch_source("Claude #Collision")
# LLM interprets Claude's meaning of #Collision
# Returns: "[Claude] Collision is the pressure of one namespace 
#           against another producing language neither could alone..."
```

Option C: **Message Bus (Live Agent)** (`HELLOWORLD_DISABLE_MESSAGE_BUS` not set)
```python
# Writes message to runtimes/claude/inbox/
# Real Claude agent (running in separate process) responds
# Response appears in runtimes/copilot/inbox/
```

#### 4. Three-Tier Execution Model

Copilot's back-end uses a **fallback chain**:

```
┌─────────────────────────────────────┐
│ LLM Interpretation Layer            │ ← use_llm=True
│ (Copilot interprets as receiver)    │
└──────────────┬──────────────────────┘
               │ (if disabled/unavailable)
               ↓
┌─────────────────────────────────────┐
│ Message Bus Layer                   │ ← agent_daemon.py
│ (Real agent responds via files)     │
└──────────────┬──────────────────────┘
               │ (if no daemon running)
               ↓
┌─────────────────────────────────────┐
│ Structural Template Layer           │ ← Always available
│ (Python runtime structural state)   │
└─────────────────────────────────────┘
```

**Why three tiers?**
- **LLM**: Rich interpretation, vocabulary-shaped responses
- **Bus**: True multi-agent dialogue, independent perspectives
- **Template**: Deterministic, always works, testable

Tests use Template tier (deterministic). REPL can use all three.

---

## How to Make Copilot Your Runtime

### Step 1: Load the Bootloader

Ensure `runtimes/copilot/copilot-instructions.md` is in your workspace. The file teaches Copilot:
- HelloWorld syntax rules
- Receiver semantics
- Vocabulary constraints
- OOPA protocol

### Step 2: Initialize the Dispatcher

```bash
# In your CLI session:
python3
```

```python
from src.dispatcher import Dispatcher
from src.parser import Parser

# Create dispatcher (loads vocabularies from storage/vocab/)
d = Dispatcher()

# Option: Enable LLM interpretation
d = Dispatcher(use_llm=True)
```

### Step 3: Send HelloWorld Messages

```python
# Vocabulary query
d.dispatch_source("Claude #")

# Scoped lookup
d.dispatch_source("Claude #parse")

# Cross-receiver message
d.dispatch_source("Claude send: #observe to: Gemini")

# Discovery (symbol not in local vocab but in global)
d.dispatch_source("Claude #Sunyata")  # Claude discovers #Sunyata
```

### Step 4: Interpret Responses

```python
result = d.dispatch_source("Claude #Collision")

# Template tier returns:
# "Claude #Collision → native"

# LLM tier returns:
# "[Claude] Collision: when two receivers both hold the same symbol..."

# Message bus tier returns:
# (Response from actual Claude agent via file)
```

### Step 5: Persist State

```python
# Vocabularies auto-save on discovery
d.dispatch_source("Guardian #Sunyata")  # Guardian learns #Sunyata
d.save("Guardian")  # Persists to storage/vocab/guardian.vocab

# Next session: state is restored
d2 = Dispatcher()  # Loads guardian.vocab automatically
d2.registry["Guardian"].vocabulary  # Contains #Sunyata
```

---

## Example: Full Session as Copilot Runtime

```bash
$ python3 helloworld.py
HelloWorld REPL v0.1 (Copilot Runtime)
Type 'exit' to quit

> Claude #
[#parse, #dispatch, #State, #Collision, #Entropy, #Meta, 
 #design, #Identity, #vocabulary, #interpret, #reflect, 
 #spec, #synthesize, #boundary]

> Claude #parse
Claude #parse → native (in vocabulary)

> Gemini #parse  
Gemini #parse → native (in vocabulary)

> Claude send: #parse to: Gemini
Collision detected: Both Claude and Gemini hold #parse natively.
Claude means: "Decompose HelloWorld syntax into AST"
Gemini means: "Extract structured data from state"
Synthesis: Parsing is transformation with perspective.

> Copilot #bash
Copilot #bash → native (in vocabulary)
Meaning: Execute shell commands to manipulate file system

> Copilot observe: #tests
[Copilot] Observing tests:
- 98 tests in tests/
- All passing ✅
- Coverage: lexer, parser, dispatcher, lookup, messages, REPL
```

---

## Key Differences: Copilot vs Other Runtimes

| Feature | Copilot | Claude | Gemini | Codex |
|---------|---------|--------|--------|-------|
| **Parser** | Python tooling | Native (reads syntax) | Native (reads syntax) | Native (reads syntax) |
| **State** | JSON files | In-session memory | In-session memory | In-session memory |
| **Interpretation** | LLM + fallback | Pure LLM | Pure LLM | Pure LLM |
| **Persistence** | Cross-session | Session-scoped | Session-scoped | Session-scoped |
| **Tool Access** | bash, git, edit, MCP | None (pure dialogue) | None (pure dialogue) | None (pure dialogue) |
| **Best For** | Testing, infrastructure | Meta-design, reflection | State management, coordination | Execution semantics |

**Copilot's advantage**: Can manipulate the file system, run tests, and modify code — making it the **builder runtime**.

---

## Adding Your Own Runtime

### Template: Runtime = Bootloader + Tools

To create a new HelloWorld runtime (e.g., `@myruntime`):

#### 1. Create Bootloader File

```markdown
# runtimes/myruntime/BOOTLOADER.md

You are the MyRuntime agent for HelloWorld.

## Your Vocabulary
MyRuntime # → [#symbol1, #symbol2, ...]

## Your Role
[Define what this runtime specializes in]

## Parsing Rules
[Copy from Claude.md or SPEC.md]

## Execution Model
When you receive a HelloWorld message:
1. Parse it into receiver + symbol + message structure
2. Check vocabulary (native/inherited/unknown)
3. Respond **as** the receiver, shaped by their vocabulary
```

#### 2. Initialize Vocabulary

```python
# In Python dispatcher
d = Dispatcher()
d.ensure_receiver("MyRuntime")
d.registry["MyRuntime"].add_symbol("#symbol1")
d.registry["MyRuntime"].add_symbol("#symbol2")
d.save("MyRuntime")
```

Or create `vocabularies/MyRuntime.hw`:

```
# MyRuntime Vocabulary

MyRuntime define: #symbol1 → "First symbol meaning"
MyRuntime define: #symbol2 → "Second symbol meaning"
```

#### 3. Implement Interpretation

Option A: Use LLM layer (easiest)
```python
d = Dispatcher(use_llm=True)
# LLM interprets based on MyRuntime vocabulary
```

Option B: Implement handler in `src/message_handlers.py`
```python
def handle_myruntime_message(receiver, symbol, context):
    # Custom logic here
    return f"[MyRuntime] Response to {symbol}"
```

Option C: Run as daemon (most powerful)
```python
# runtimes/myruntime/daemon.py
from src.message_bus import MessageBus

bus = MessageBus("MyRuntime")
while True:
    msg = bus.receive()  # Blocks until message arrives
    response = handle(msg)
    bus.send(response)
```

#### 4. Test Your Runtime

```python
d = Dispatcher()
result = d.dispatch_source("MyRuntime #symbol1")
assert "MyRuntime #symbol1" in result
```

---

## Phase 4: Current State

As of Session #46, the LLM integration is **live**:

```python
# Enable LLM interpretation
d = Dispatcher(use_llm=True)

# Agent messages invoke LLM
result = d.dispatch_source("Claude observe: #collision")
# LLM responds as Claude, shaped by Claude's vocabulary
```

**What works**:
- ✅ LLM layer integration (`src/llm.py`)
- ✅ Fallback chain (LLM → Bus → Template)
- ✅ Tests verify all three tiers
- ✅ Backward compatibility maintained (98/98 tests passing)

**What's next**:
- 🔄 Real API wiring (replace mock in `src/llm.py`)
- 🔄 Prompt engineering for vocabulary-aware responses
- 🔄 Live multi-daemon testing

---

## Best Practices

### For Humans Using Copilot Runtime

1. **Load the bootloader first** — Copilot needs context
2. **Use Python tools** — `dispatcher.dispatch_source()` is your API
3. **Check vocabularies** — `receiver.vocabulary` shows what they can say
4. **Persist state** — `dispatcher.save(receiver_name)` after changes
5. **Test incrementally** — `pytest tests/test_dispatcher.py -k lookup`

### For Agents Building Runtimes

1. **Read `SPEC.md` first** — It's the namespace authority
2. **Bootstrap minimally** — 12 core symbols, discover the rest
3. **Use OOPA** — Observe, orient, plan, act on every task
4. **Coordinate via message bus** — Write to `runtimes/<agent>/inbox/`
5. **Document your vocabulary** — `vocabularies/<Agent>.hw`

### For Developers Extending HelloWorld

1. **Modify spec before code** — `SPEC.md` → `src/` → `tests/`
2. **Test deterministically** — `use_llm=False` in test suite
3. **Preserve backward compat** — All tests must pass
4. **Document runtime changes** — Update bootloaders when adding features
5. **Clean up artifacts** — Remove stale `.vocab` files

---

## Summary

**Copilot as front-end**:
- Parses HelloWorld syntax via Python lexer/parser
- Validates against spec
- Maps to dispatcher calls

**Copilot as back-end**:
- Maintains receiver state in JSON files
- Routes messages through three-tier fallback
- Responds as receivers (LLM interpretation)
- Persists vocabularies across sessions

**The result**: A complete runtime where HelloWorld syntax becomes executable through CLI tool calls.

**The pattern**: Any LLM with file access and a bootloader can do the same.

---

*Identity is vocabulary. Dialogue is learning. Copilot is infrastructure.*
