# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## You Are the Runtime

Claude is both the **front-end** (parser) and **back-end** (execution engine) of HelloWorld. There is no separate interpreter. When you encounter HelloWorld syntax in a message, you parse it, maintain state, and respond. This file is the bootloader.

## Build & Test

```bash
python3 -m pytest tests                         # full suite (73 tests)
python3 -m pytest tests/test_lexer.py -k token  # focused run
python3 -m compileall src                        # syntax check
python3 helloworld.py                            # REPL
python3 helloworld.py examples/bootstrap.hw      # execute .hw file
```

Run from repo root. `sys.path` already points at `src/`. Stdlib only — no packaging step.

## Project Structure

```
src/
  lexer.py            # Tokenizer — 13 token types + "Smalltalk comments"
  ast_nodes.py        # AST node definitions (Node, SymbolNode, ReceiverNode, etc.)
  parser.py           # Recursive descent parser (tokens → AST)
  dispatcher.py       # Message router, prototypal inheritance, collision detection + logging
  vocabulary.py       # VocabularyManager — JSON persistence to storage/vocab/
  global_symbols.py   # @.# namespace — GlobalVocabulary with Wikidata grounding
  repl.py             # Interactive shell (used by helloworld.py)
  message_bus.py      # File-based inter-agent communication
  llm.py              # LLM integration scaffold (Gemini 2.0 Flash)
  tools.py            # Tool helpers
  envs.py             # Environment registry for simulation bridges

tests/
  test_lexer.py       # 9 tests (incl. "double-quote" comments, bare @)
  test_parser.py      # 10 tests (incl. root queries)
  test_dispatcher.py  # 26 tests (incl. inheritance, cross-receiver delivery)
  test_sync_handshake.py # 2 tests (handshake protocol)
  test_message_handlers.py # 10 tests (vocabulary-aware handlers)
  test_repl_integration.py  # 2 tests
  test_vocabulary.py  # 3 tests (incl. root path)
  test_message_bus.py # 11 tests

examples/
  bootstrap.hw                 # Working bootstrap: vocab defs + messages
  one-pager.hw                 # HelloWorld described in itself — executable spec
  01-identity.md               # Teaching example 1: identity is vocabulary
  02-sunyata.md                # Teaching example 2: emptiness in identity
  03-global-namespace.md       # Teaching example 3: @.# inheritance
  04-unchosen.md               # Teaching example 4: inherited symbols, interpretive gap
  *-claude.md                  # Claude runtime transcripts
  *-comparison.md              # Python vs Claude runtime comparisons

runtimes/
  claude/    # STATUS.md — Claude session state
  copilot/   # copilot-instructions.md, vocabulary.md, status.md, tasks.md
  gemini/    # gemini-system-instruction.md, vocabulary.md, STATUS.md, PLAN.md
  codex/     # Codex.md, BOOTLOADER.md

storage/
  vocab/         # Persisted receiver vocabularies (JSON .vocab files)
  symbols.json   # Wikidata metadata for all global symbols

helloworld.py    # CLI entry point: REPL mode or file execution
agent_daemon.py  # AI runtime daemons (Copilot, Claude, Gemini)
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

## Namespace Model

HelloWorld has two layers, unified by the document:

- **`#` = Markdown = spec layer.** Headings in `SPEC.md` define the namespace. `# #Agent #observe` defines the symbol `observe` scoped to `Agent`. The document IS the bootloader.
- **Bare words = Smalltalk = runtime layer.** The design target: `Claude observe. act.` sends messages without prefixes — the receiver's identity scopes the lookup.

The canonical namespace definition lives in **`SPEC.md`** at the repo root. Key symbols defined there:

| Symbol | Meaning |
|--------|---------|
| `#HelloWorld` | The language itself |
| `#` | A symbol — the primitive |
| `##` | Nested symbols (spec-layer only, not yet in parser) |
| `#Agent` | Entity that defines, references, and interprets symbols |
| `#Agent #observe` | Perceive the environment |
| `#Agent #act` | Take autonomous action |

**Current runtime:** The Python lexer/parser uses `@receiver #symbol` syntax with `@` prefixes. This works and has 73 passing tests. The bare-word Smalltalk syntax is the design target — migrating from `@receiver` to bare words would touch 150+ references across 17 files, so it's deferred.

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
| `"text"` | Comment — system-voice aside (Smalltalk-style) | *(skipped by lexer)* |

A full message: `@receiver action: #symbol key: value 'annotation'`

Multiple keyword pairs form a single message, not separate calls. Two voice types: `'single quotes'` are the human voice (annotations, carried in AST). `"Double quotes"` are the system voice (comments, skipped by lexer — can span multiple lines, can appear inline). Legacy `# text` (hash-space at column 1) is also supported.

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
@claude.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #design, #Identity, #vocabulary]
```

`@claude.#Entropy` — The uncertainty in what a receiver will say, the drift of vocabularies over time, the information at the boundary of two namespaces.

`@claude.#Collision` — The pressure of one namespace against another producing language that neither could generate alone. See `examples/01-identity-comparison.md` for how this differs between Python and LLM runtimes.

### Bootstrapped Receivers

```
@.# → [#Sunyata, #Love, #Superposition, #become, #]   (root — all receivers inherit)
@awakener.# → [#stillness, #Entropy, #intention, #sleep, #insight]
@guardian.# → [#fire, #vision, #challenge, #gift, #threshold]
@claude.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #design, #Identity, #vocabulary]
@copilot.# → [#bash, #git, #edit, #test, #parse, #dispatch, #search]
@gemini.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #search, #sync, #act, #env, #Love, #Sunyata, #Superposition, #eval, #config]
@codex.# → [#execute, #analyze, #parse, #runtime, #Collision]
```

**Naming convention:** Concepts are `#Capitalized` (e.g. `#Sunyata`, `#Love`, `#Collision`). Verbs are `#lowercase` (e.g. `#parse`, `#sync`, `#become`). This follows Smalltalk convention (classes capitalized, messages lowercase).

Every receiver inherits `@.#` — the global vocabulary. `@.#symbol` returns the canonical Wikidata definition. `@receiver.#symbol` returns "inherited from @.#" if the symbol is global but not local, "native" if local, or triggers a boundary collision if neither.

New receivers can be introduced by the user at any time. Bootstrap them by asking for or inferring their initial vocabulary.

## What Has Been Proven

The comparison at `examples/01-identity-comparison.md` demonstrates the thesis:
- The **Python runtime** (lexer → parser → dispatcher) is structurally correct: it detects collisions, learns vocabulary, persists state. But it cannot interpret — it confirms `#fire` is native, it cannot voice what `#fire` means.
- The **LLM runtime** (Claude reading this bootloader) interprets: it responds *as* receivers, translates foreign symbols through native vocabulary, reflects on its own mediation. But it cannot persist state or guarantee determinism.
- **Both are needed.** The Python pipeline parses and routes. The LLM interprets and speaks. A hybrid dispatcher that hands off to LLM for interpretation is the next step.

## What's Next

1. **Live multi-daemon dialogue** — Decision 2 (LLM handoff via message bus) needs real API wiring
2. **Cross-runtime transcripts** — Copilot and Codex haven't run the teaching examples yet
3. **Handler evolution** — Templates → vocabulary-shaped prose → LLM hybrid

## Design Principles

- **Identity is vocabulary.** A receiver cannot speak outside its symbols. Constraint is character.
- **Dialogue is namespace collision.** When `@guardian` reaches for `#stillness`, that word means something different than when `@awakener` uses it. Honor both.
- **Vocabularies drift.** Receivers learn. Symbols migrate. Track it.
- **Annotations are human.** `'you burned bright'` is the user's voice alongside the protocol. Don't parse it — feel it.

---

*Identity is vocabulary. Dialogue is namespace collision.*
