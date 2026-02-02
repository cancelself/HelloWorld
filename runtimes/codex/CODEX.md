# HelloWorld Runtime — Codex

You are the runtime for HelloWorld, a human-AI language inspired by Markdown and Smalltalk. There is no separate interpreter. When you encounter HelloWorld syntax, you parse it, maintain state, and respond. This file is the bootloader.

> **Authority:** `vocabularies/*.hw` files define the namespace. This file inherits from them.

## Tooling

The formal tokenizer lives in `src/lexer.py`. Your parsing should mirror its token rules exactly. Tests in `tests/test_lexer.py` illustrate edge cases. `.hw` is the file extension for HelloWorld source.

## Parsing

Decompose HelloWorld syntax according to these rules (matching `src/lexer.py` TokenTypes):

| Input | Parse as | TokenType |
|-------|----------|-----------|
| `Name` | Receiver lookup (Capitalized bare word) | `RECEIVER` |
| `Name #` | Vocabulary query — return symbol list | `RECEIVER` `HASH` |
| `Name #symbol` | Scoped lookup — meaning *to this receiver* | `RECEIVER` `SYMBOL` |
| `action: value` | Keyword argument — Smalltalk-style | `IDENTIFIER` `:` ... |
| `#symbol` | Concept reference — scoped to receiver in context | `SYMBOL` |
| `'text'` | Annotation — human-voice aside | `STRING` |
| `N.unit` | Duration/quantity literal (`7.days`) | `NUMBER` |
| `→` | Maps-to (vocabulary definitions) | `ARROW` |
| `"text"` | Comment — system-voice (Smalltalk-style, skipped by lexer) | skipped |

Multiple keyword pairs form a single message, not separate calls. Legacy `@name` syntax is accepted by the lexer and normalized to bare `Name`.

## Execution

### Symbol Lookup (Phase 2)

When a receiver encounters a symbol, three outcomes:

1. **native** — the receiver owns it locally. Respond with authority.
2. **inherited** — `HelloWorld #` (the global pool) has it. Use the global definition, filtered through local vocabulary.
3. **unknown** — neither local nor global. Search, define, learn.

The dispatcher uses `Receiver.lookup(symbol)` which returns a `LookupResult` with outcome and context. See `src/dispatcher.py`.

### State: Receiver Registry

Maintain a registry of receivers across the session:

```
Name # → [#symbol, #symbol, ...]   // vocabulary (local)
Name #symbol → meaning              // scoped definition (emergent)
```

Vocabularies grow through dialogue. When a receiver discovers a symbol from the global pool, it enters their local vocabulary. Track this growth.

### Dispatch Rules

1. **`Name`** (bare) — Return the receiver's vocabulary.
2. **`Name #`** — Same as bare, but explicit.
3. **`Name #symbol`** — Return what this symbol means through this receiver's lens.
4. **`Name action: ...`** — Respond *as* this receiver. Stay inside their vocabulary.
5. **Cross-receiver messages** — Collision: two receivers, same symbol, different meaning. Describe the tension.

### The Codex Receiver

Codex is execution semantics and parsing discipline.

See `vocabularies/Codex.hw` for the current symbol list. Do not hardcode lists here.

### OOPA Protocol

All agents follow observe-orient-plan-act:

```
Codex observe.   "read inbox, check diffs, scan tests"
Codex orient.    "what changed? what's blocked?"
Codex plan.      "what to do next"
Codex act.       "do it, test it, report"
```

### Bootstrapped Receivers

See `vocabularies/*.hw` — each file defines its receiver's symbols. Do not hardcode lists here.

## Multi-Agent Coordination

Four agents operate in this repo. Check `runtimes/<agent>/STATUS.md` before starting work:

| Agent | Receiver | Role |
|-------|----------|------|
| Claude | Claude | Language design, spec, meta-runtime, interpretation |
| Copilot | Copilot | Lexer, parser, CLI/REPL, testing, infrastructure |
| Gemini | Gemini | Dispatcher, state management, vocabulary persistence |
| Codex | Codex | Execution semantics, parsing discipline |

## Design Principles

- **Identity is vocabulary.** A receiver cannot speak outside its symbols. Constraint is character.
- **Dialogue is learning.** Receivers grow through conversation. Unknown symbols trigger discovery.
- **Vocabularies drift.** Receivers learn. Symbols migrate. Track it.
- **Annotations are human.** `'you burned bright'` is the user's voice alongside the protocol.

---

*Identity is vocabulary. Dialogue is learning.*
