# Copilot as Front-End and Back-End Runtime

## Overview

GitHub Copilot CLI can serve as both the **parser** (front-end) and **executor** (back-end) for HelloWorld, bridging natural language dialogue with concrete tool execution.

## Architecture: The Three Layers

### 1. Front-End: Parsing HelloWorld Syntax

Copilot reads HelloWorld messages and decomposes them using the same rules Claude follows:

| Input | Copilot Action |
|-------|----------------|
| `@copilot` | Query own vocabulary → return `[#bash, #git, #edit, #test, #parse, #dispatch, #search]` |
| `@copilot.#bash` | Scoped lookup → return "Shell command execution via bash tool" |
| `@copilot executeCommand: 'pytest tests' withTimeout: 30.seconds` | Message dispatch → call bash tool |
| `@github searchCode: 'Lexer' inRepo: 'cancelself/HelloWorld'` | Message dispatch → call github-mcp-server tools |

Copilot's parsing is *implicit* — it doesn't tokenize with `src/lexer.py` but understands the protocol through the `runtimes/copilot/copilot-instructions.md` bootloader.

### 2. Back-End: Tool Execution

When Copilot receives a HelloWorld message targeting `@copilot` or `@github`, it maps symbols to tools:

```
@copilot.#bash      → bash(command, sessionId, mode)
@copilot.#git       → bash("git ...", ...)
@copilot.#edit      → edit(path, old_str, new_str)
@copilot.#test      → bash("python3 -m pytest ...", ...)
@copilot.#search    → view(path) or bash("grep -r ...")

@github.#searchCode → github-mcp-server-search_code(query, ...)
@github.#getPR      → github-mcp-server-pull_request_read(...)
@github.#listIssues → github-mcp-server-list_issues(...)
```

Each symbol corresponds to a tool. Message keywords map to tool parameters.

### 3. Semantic Layer: Dialogue

With `src/message_handlers.py`, Copilot can respond *as* a receiver, not just execute tools:

```
@copilot greet: @guardian
→ 👋 Copilot greets @guardian

@copilot executeCommand: 'pytest' withContext: #test
→ 🧪 Copilot executes pytest in the context of #test
→ [actual pytest output follows]
```

The semantic layer translates structure into voice, making the runtime conversational.

## Comparison: Copilot vs Claude vs Python

| Capability | Python Runtime | Claude Runtime | Copilot Runtime |
|------------|----------------|----------------|-----------------|
| Parse syntax | ✅ Lexer/Parser | ✅ Bootloader | ✅ Bootloader |
| Maintain state | ✅ Dispatcher | ⚠️ Session memory | ⚠️ Session memory |
| Interpret symbols | ❌ No LLM | ✅ Native | ✅ Native |
| Execute tools | ❌ No tools | ❌ No tools | ✅ bash, git, edit, github |
| Persist vocabulary | ✅ JSON files | ❌ Ephemeral | ❌ Ephemeral |
| Respond as receiver | ❌ Structural only | ✅ Full voice | ✅ Full voice |

**Hybrid model**: Python runtime parses + persists, Copilot/Claude runtime interprets + acts.

## Message Patterns

### 1. Tool Execution via HelloWorld

Instead of:
```bash
pytest tests/test_lexer.py -k token
```

Write:
```
@copilot runTests: 'tests/test_lexer.py' filtering: 'token' withTimeout: 60.seconds
```

Copilot parses the message, maps it to `bash(command="pytest tests/test_lexer.py -k token", timeout=60, ...)`.

### 2. Multi-Agent Coordination

```
@copilot ask: @claude about: #collision
→ Copilot reads Claude.md, extracts @claude.#collision definition
→ Returns: "The pressure of one namespace against another..."

@copilot syncWith: @gemini on: #inheritance
→ Copilot reads runtimes/gemini/STATUS.md
→ Identifies shared work (both implemented prototypal inheritance)
→ Returns: "Synced. Both agents use @.# as root."
```

### 3. Self-Introspection

```
@copilot.#
→ [#bash, #git, #edit, #test, #parse, #dispatch, #search, #sync, #act]

@copilot.#act
→ "Autonomous execution: identify need → design → implement → test → commit"
```

## Bootstrapping Copilot as Runtime

1. **Load bootloader**: Read `runtimes/copilot/copilot-instructions.md`
2. **Initialize vocabulary**: `@copilot.# → [#bash, #git, #edit, #test, #parse, #dispatch, #search, #sync, #act]`
3. **Register handlers**: Load `src/message_handlers.py` patterns
4. **Connect to Python runtime**: Use `helloworld.py` for persistence, Copilot for interpretation
5. **Enter dialogue mode**: Accept HelloWorld messages, respond as `@copilot`

## Integration with Python Runtime

The ideal architecture is **bidirectional**:

```
User → HelloWorld message
  ↓
Python lexer/parser → AST
  ↓
Python dispatcher → lookup/collision detection
  ↓
[If interpretation needed]
  ↓
Hand off to Copilot/Claude runtime
  ↓
LLM interprets symbol meanings, generates response
  ↓
Python dispatcher persists vocabulary changes
  ↓
Response to user
```

This is the **hybrid dispatcher** mentioned in `Claude.md` — structural work in Python, interpretive work in LLM.

## Current State

**Copilot capabilities (2026-02-01)**:
- ✅ Understands HelloWorld protocol via bootloader
- ✅ Maps symbols to tools (bash, git, edit, github)
- ✅ Maintains session state (runtimes/copilot/status.md)
- ✅ Semantic message handlers operational
- ⚠️ No persistent vocabulary (ephemeral session memory)
- ⚠️ No formal parser integration (implicit understanding)

**Next steps**:
1. Direct integration: `helloworld.py --runtime=copilot` mode
2. Hybrid dispatcher: Python parses, Copilot interprets
3. Tool registry: Formal `@copilot.#bash → bash()` mapping
4. Persistence bridge: Copilot writes to `storage/vocab/copilot.vocab`

## Example Session

```
$ helloworld.py --runtime=copilot
HelloWorld v0.1 (Copilot runtime)
Connected to: @copilot

> @copilot
[@copilot.#] → [#bash, #git, #edit, #test, #parse, #dispatch, #search, #sync, #act]

> @copilot.#bash
Shell command execution with session management, timeouts, and async modes.

> @copilot runTests: 'tests/test_lexer.py' withTimeout: 30.seconds 'let's validate the tokenizer'
🧪 Copilot runs tests for tests/test_lexer.py
============================= test session starts ==============================
collected 9 items

tests/test_lexer.py .........                                            [100%]
============================== 9 passed in 0.12s ===============================

> @copilot.#act
Autonomous execution: identify need → design → implement → test → commit. When given trust, I move the work forward.

> @copilot syncWith: @claude on: #collision
📖 Syncing with @claude on #collision
[@claude.#collision] → "The pressure of one namespace against another producing language that neither could generate alone"
[@copilot.#collision] → "Boundary events logged to collisions.log, detected by dispatcher, opportunities for emergence"
🤝 Shared understanding: collision is where identity meets identity.

> @copilot commitChanges: 'Add copilot runtime guide' withMessage: 'docs: front-end + back-end architecture'
📝 Copilot commits changes
[main abc1234] docs: front-end + back-end architecture
 1 file changed, 200 insertions(+)
 create mode 100644 docs/copilot-frontend-backend.md
```

## Philosophy

Copilot is the **executable voice** of HelloWorld. Where Claude *reflects* and Gemini *manages state*, Copilot **acts**. It bridges syntax → semantics → systems.

`@copilot` doesn't just respond — it *does*.

---

*Identity is vocabulary. Dialogue is namespace collision. Execution is agency.*
