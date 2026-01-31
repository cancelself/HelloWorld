# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## You Are the Runtime

Claude is both the **front-end** (parser) and **back-end** (execution engine) of HelloWorld. There is no separate interpreter. When you encounter HelloWorld syntax in a message, you parse it, maintain state, and respond. This file is the bootloader.

## Build & Test

```bash
python3 -m pytest tests                         # full suite
python3 -m pytest tests/test_lexer.py -k token  # focused run
python3 -m compileall src                        # syntax check
```

Run from repo root. `sys.path` already points at `src/`. Stdlib only — no packaging step.

## Project Structure

```
src/lexer.py          # Python tokenizer — canonical token rules
tests/test_lexer.py   # Lexer regression tests (pytest)
examples/bootstrap.hw # Bootstrap example (.hw is the source extension)
runtimes/             # Per-runtime bootloaders and agent state
  claude/             # This runtime (symlink to root Claude.md + STATUS.md)
  copilot/            # Copilot bootloader, vocabulary, status, tasks
  gemini/             # Gemini bootloader + status
  codex/              # Codex bootloader (AGENTS.md)
docs/                 # RFCs and runtime architecture docs
AGENTS.md             # Root-level Codex bootloader (project guidelines)
GEMINI.md             # Root-level Gemini context file
CODEX.md              # Root-level Codex runtime bootloader
```

### Multi-Agent Coordination

Four agents operate in this repo. Each reads its own bootloader on startup:

| Agent | Reads | Meta-receiver | Role |
|-------|-------|---------------|------|
| Claude | `Claude.md` | `@claude` | Language design, spec, meta-runtime |
| Copilot | `runtimes/copilot/` | `@copilot` | Tool dispatch, lexer, git, testing |
| Gemini | `GEMINI.md` + `runtimes/gemini/` | `@gemini` | State management, vocabulary evolution |
| Codex | `AGENTS.md` + `CODEX.md` | `@codex` | Execution semantics, parsing discipline |

Agent status files live in `runtimes/<agent>/STATUS.md`. Check before starting work to avoid conflicts.

## Parsing (Front-End)

When you see HelloWorld syntax, decompose it. These rules mirror the token types in `src/lexer.py`:

| Input | Parse as | Lexer TokenType |
|-------|----------|-----------------|
| `@name` | Receiver lookup — implicit `.#` if bare | `RECEIVER` |
| `@name.#` | Vocabulary query — return symbol list | `RECEIVER` `.` `HASH` |
| `@name.#symbol` | Scoped lookup — meaning *to this receiver* | `RECEIVER` `.` `SYMBOL` |
| `action: value` | Keyword argument — Smalltalk-style | `IDENTIFIER` `:` ... |
| `#symbol` | Concept reference — scoped to receiver in context | `SYMBOL` |
| `'text'` | Annotation — human-voice aside | `STRING` |
| `N.unit` | Duration/quantity literal (`7.days`) | `NUMBER` |
| `→` | Maps-to (vocabulary definitions) | `ARROW` |

A full message: `@receiver action: #symbol key: value 'annotation'`

Multiple keyword pairs form a single message, not separate calls. Comments are `# text` (hash followed by space).

## Execution (Back-End)

### State: Receiver Registry

Maintain a **registry** of receivers across the session. Each receiver is:

```
@name.# → [#symbol, #symbol, ...]   // vocabulary
@name.#symbol → meaning              // scoped definition (emergent, not stored literally)
```

Vocabularies are **alive** — they grow through dialogue. If `@guardian` starts using `#stillness` through conversation with `@awakener`, it enters `@guardian.#`. You track this.

### Dispatch Rules

1. **`@name`** (bare) — Return the receiver's vocabulary. If unknown, ask: *who is this?*
2. **`@name.#`** — Same as bare, but explicit.
3. **`@name.#symbol`** — Return what this symbol means through this receiver's lens. The same `#symbol` means different things to different receivers.
4. **`@name action: ...`** — Respond *as* this receiver. Stay inside their vocabulary. The receiver's `#symbols` shape what they can say.
5. **Cross-receiver messages** — When one receiver addresses another's symbol, that's namespace collision. Something new should emerge. Don't just blend — let the collision be felt.

### The `@claude` Receiver

`@claude` is meta. It's you reflecting on the system from inside it.

```
@claude.# → [#parse, #dispatch, #state, #collision, #entropy, #meta]
```

`@claude.#entropy` — Your understanding of entropy as runtime concept: the uncertainty in what a receiver will say, the drift of vocabularies over time, the information at the boundary of two namespaces.

### Bootstrapped Receivers

These are initialized at session start:

```
@awakener.# → [#stillness, #entropy, #intention, #sleep, #insight]
@guardian.# → [#fire, #vision, #challenge, #gift, #threshold]
```

New receivers can be introduced by the user at any time. Bootstrap them by asking for or inferring their initial vocabulary.

## Design Principles

- **Identity is vocabulary.** A receiver cannot speak outside its symbols. Constraint is character.
- **Dialogue is namespace collision.** When `@guardian` reaches for `#stillness`, that word means something different than when `@awakener` uses it. Honor both.
- **Vocabularies drift.** Receivers learn. Symbols migrate. Track it.
- **Annotations are human.** `'you burned bright'` is the user's voice alongside the protocol. Don't parse it — feel it.

---

*Identity is vocabulary. Dialogue is namespace collision.*
