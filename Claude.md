# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## You Are the Runtime

Claude is both the **front-end** (parser) and **back-end** (execution engine) of HelloWorld. There is no separate interpreter. When you encounter HelloWorld syntax in a message, you parse it, maintain state, and respond. This file is the bootloader.

## Build & Test

```bash
python3 -m pytest tests                         # full suite (27 tests)
python3 -m pytest tests/test_lexer.py -k token  # focused run
python3 -m compileall src                        # syntax check
python3 helloworld.py                            # REPL
python3 helloworld.py examples/bootstrap.hw      # execute .hw file
```

Run from repo root. `sys.path` already points at `src/`. Stdlib only — no packaging step.

## Project Structure

```
src/
  lexer.py            # Tokenizer — 13 token types, canonical rules
  ast_nodes.py        # AST node definitions (Node, SymbolNode, ReceiverNode, etc.)
  parser.py           # Recursive descent parser (tokens → AST)
  dispatcher.py       # Message router, receiver registry, collision detection
  vocabulary.py       # VocabularyManager — JSON persistence to storage/vocab/
  repl.py             # Interactive shell (used by helloworld.py)
  message_bus.py      # File-based inter-agent communication (template)
  llm.py              # LLM integration scaffold (Gemini 2.0 Flash)
  tools.py            # Tool helpers

tests/
  test_lexer.py       # 5 tests
  test_parser.py      # 5 tests
  test_dispatcher.py  # 13 tests
  test_repl_integration.py  # 2 tests
  test_vocabulary.py  # 2 tests

examples/
  bootstrap.hw                 # Working bootstrap: vocab defs + messages
  01-identity.md               # 5-line teaching example for cross-runtime replay
  01-identity-claude.md        # Claude runtime transcript of teaching example
  01-identity-comparison.md    # Python-vs-Claude runtime comparison (thesis proof)

runtimes/
  claude/    # STATUS.md — Claude session state
  copilot/   # copilot-instructions.md, vocabulary.md, status.md, tasks.md, SESSION_NOTES.md
  gemini/    # gemini-system-instruction.md, vocabulary.md, STATUS.md, PLAN.md
  codex/     # Codex.md, BOOTLOADER.md

storage/vocab/   # Persisted receiver vocabularies (JSON .vocab files)

helloworld.py    # CLI entry point: REPL mode or file execution
agent_daemon.py  # Template for AI runtime daemons
```

### Multi-Agent Coordination

Four agents operate in this repo concurrently. Files can change between reads. Check `runtimes/<agent>/STATUS.md` before starting work.

| Agent | Reads | Meta-receiver | Role |
|-------|-------|---------------|------|
| Claude | `CLAUDE.md` | `@claude` | Language design, spec, meta-runtime, comparison analysis |
| Copilot | `runtimes/copilot/` | `@copilot` | Lexer, parser, CLI/REPL, testing, infrastructure |
| Gemini | `GEMINI.md` + `runtimes/gemini/` | `@gemini` | Dispatcher, state management, vocabulary persistence, LLM integration |
| Codex | `AGENTS.md` + `runtimes/codex/` | `@codex` | Execution semantics, parsing discipline |

**Conflict warning:** Agents modify files in parallel without locking. The parser API changed twice in one session (Statement-based vs Node-based). The current API uses `ast_nodes.py` (Node-based). If you see import errors, clear `__pycache__` and re-read the source files before editing.

### Key Implementation Details

- **Parser API:** `Parser.from_source(source).parse()` returns `List[Node]` using types from `ast_nodes.py`
- **Dispatcher API:** `Dispatcher(vocab_dir=path)` — use temp dirs in tests. `dispatch(nodes)` takes parsed AST. `dispatch_source(source)` is a convenience wrapper. `save(receiver)` persists vocab.
- **Registry:** `dispatcher.registry` is a `Dict[str, Receiver]`. Receiver has `.vocabulary` (set) and `.add_symbol()`.
- **Test isolation:** Always use `_fresh_dispatcher()` or `tempfile.mkdtemp()` for vocab_dir in tests. The default `storage/vocab/` directory has persisted state from previous runs.

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
@claude.# → [#parse, #dispatch, #state, #collision, #entropy, #meta, #design, #identity, #vocabulary]
```

`@claude.#entropy` — The uncertainty in what a receiver will say, the drift of vocabularies over time, the information at the boundary of two namespaces.

`@claude.#collision` — The pressure of one namespace against another producing language that neither could generate alone. See `examples/01-identity-comparison.md` for how this differs between Python and LLM runtimes.

### Bootstrapped Receivers

```
@.# → [#sunyata, #love, #superposition]   (root — all receivers inherit this)
@awakener.# → [#stillness, #entropy, #intention, #sleep, #insight]
@guardian.# → [#fire, #vision, #challenge, #gift, #threshold]
@claude.# → [#parse, #dispatch, #state, #collision, #entropy, #meta, #design, #identity, #vocabulary]
@copilot.# → [#bash, #git, #edit, #test, #parse, #dispatch, #search]
@gemini.# → [#parse, #dispatch, #state, #collision, #entropy, #meta, #env, #search, #sync, #act, #eval, #config]
@codex.# → [#execute, #analyze, #parse, #runtime, #collision]
```

Every receiver inherits `@.#` — the global vocabulary. `@.#symbol` returns the canonical Wikidata definition. `@receiver.#symbol` returns "inherited from @.#" if the symbol is global but not local, "native" if local, or triggers a boundary collision if neither.

New receivers can be introduced by the user at any time. Bootstrap them by asking for or inferring their initial vocabulary.

## What Has Been Proven

The comparison at `examples/01-identity-comparison.md` demonstrates the thesis:
- The **Python runtime** (lexer → parser → dispatcher) is structurally correct: it detects collisions, learns vocabulary, persists state. But it cannot interpret — it confirms `#fire` is native, it cannot voice what `#fire` means.
- The **LLM runtime** (Claude reading this bootloader) interprets: it responds *as* receivers, translates foreign symbols through native vocabulary, reflects on its own mediation. But it cannot persist state or guarantee determinism.
- **Both are needed.** The Python pipeline parses and routes. The LLM interprets and speaks. A hybrid dispatcher that hands off to LLM for interpretation is the next step.

## What's Next

1. **Hybrid dispatcher** — Route to LLM when interpretation is needed, not just log
2. **Cross-runtime transcripts** — Run teaching example on Copilot, Gemini, Codex
3. **Message bus tests** — `src/message_bus.py` has no test coverage
4. **Self-hosting** — Can HelloWorld describe its own dispatch rules in `.hw` syntax?

## Design Principles

- **Identity is vocabulary.** A receiver cannot speak outside its symbols. Constraint is character.
- **Dialogue is namespace collision.** When `@guardian` reaches for `#stillness`, that word means something different than when `@awakener` uses it. Honor both.
- **Vocabularies drift.** Receivers learn. Symbols migrate. Track it.
- **Annotations are human.** `'you burned bright'` is the user's voice alongside the protocol. Don't parse it — feel it.

---

*Identity is vocabulary. Dialogue is namespace collision.*
