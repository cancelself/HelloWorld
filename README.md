# HelloWorld

A message-passing language where entities communicate through bounded vocabularies of symbols, powered by both a Python runtime and LLM interpreters.

## Quick Start

```bash
python3 -m pytest tests                  # 352 tests, stdlib only, ~1s
python3 helloworld.py                    # open the REPL
python3 helloworld.py -e '@Claude #'     # query a receiver's vocabulary
```

No external dependencies. Python 3.10+ and the standard library are all you need.

## What Is This?

HelloWorld is a language built around **receivers** and **symbols**. A receiver (written `@name`) is an entity — a person, an AI agent, a concept — that owns a vocabulary of symbols (written `#symbol`). When you send a message to a receiver, it responds using only the symbols it knows. What a receiver can name is what it can say.

For example, `@Claude` is a receiver whose vocabulary includes symbols like `#observe` and `#act`. You can query its vocabulary with `@Claude #`, send it a message with `@Claude observe:`, or ask what a specific symbol means to it with `@Claude #observe`. Receivers inherit from a global vocabulary (`HelloWorld #`), so shared concepts like `#send` and `#receive` are available everywhere, but each receiver can also define its own symbols with its own meanings.

The interesting part happens at the boundaries. When two receivers both use the same symbol but mean different things by it, that is a **collision** — and collisions are where new meaning emerges. The Python runtime detects collisions structurally (both receivers claim the symbol). An LLM runtime can go further: it interprets the collision, voices both perspectives, and produces something neither receiver could say alone. HelloWorld is designed to run on both.

## Syntax Reference

| Element | Example | What it does |
|---------|---------|-------------|
| `@target` | `@Claude` | Address a receiver (bare = query its vocabulary) |
| `Receiver #symbol` | `Claude #observe` | Query symbol through receiver (canonical form) |
| `@receiver #symbol` | `@Claude #observe` | Alternative form (@ is optional for queries) |
| `@target #` | `@Claude #` | List the receiver's full vocabulary |
| `#symbol` | `#observe` | Reference a concept, scoped to the current receiver |
| `action: value` | `send: #hello` | Keyword argument (Smalltalk-style, chainable) |
| `'text'` | `'a note'` | Annotation — your voice alongside the protocol |
| `N.unit` | `7.days` | Duration or quantity literal |
| `->` | `#symbol -> meaning` | Maps-to (vocabulary definitions) |
| `"text"` | `"system note"` | Comment (skipped by lexer, Smalltalk-style) |

A full message looks like: `@receiver action: #symbol key: value 'annotation'`

## How It Works

HelloWorld has two complementary runtimes:

**Python runtime** (lexer, parser, dispatcher) handles structure. It tokenizes source into 13 token types, parses them into an AST, and dispatches messages to receivers. It detects collisions, manages inheritance, persists vocabularies to disk, and runs deterministically. But it cannot *interpret* — it can confirm that `@Claude` owns `#observe`, but it cannot explain what observation means to Claude.

**LLM runtimes** (Claude, Copilot, Gemini, Codex) handle interpretation. When an LLM loads the bootloader files in this repo, it becomes a HelloWorld runtime — it can respond *as* receivers, translate symbols across vocabulary boundaries, and reflect on its own mediation. But it cannot persist state or guarantee determinism.

Both are needed. The Python pipeline parses and routes. The LLM interprets and speaks.

```
# Python runtime: structural
$ python3 helloworld.py -e '@Claude #observe'
→ @Claude.#observe: native

# LLM runtime: interpretive (paste into a conversation with the bootloader loaded)
@Claude #observe
→ To observe is to read the environment before acting — diffs, inboxes,
  state files — and hold what you find without yet deciding what to do.
```

## Project Structure

```
helloworld.py              CLI entry point (REPL, file exec, inline eval)
src/
  lexer.py                 Tokenizer (13 token types)
  ast_nodes.py             AST node definitions
  parser.py                Recursive descent parser (tokens -> AST)
  dispatcher.py            Message router, inheritance, collision detection
  vocabulary.py            Vocabulary persistence (JSON)
  global_symbols.py        Global namespace (@.#) with Wikidata grounding
  repl.py                  Interactive shell
  message_bus.py           File-based inter-agent communication
  agent_runtime.py         AI runtime daemon infrastructure
  llm.py                   LLM integration scaffold
vocabularies/              .hw files that bootstrap the language
  HelloWorld.hw            Root receiver (core symbols: #send, #receive, #become, ...)
  Agent.hw                 Agent protocol (#observe, #orient, #decide, #act)
  Human.hw                 Human receiver vocabulary
  Collaboration.hw         Human-agent collaboration protocol
  Claude.hw / Copilot.hw / Gemini.hw / Codex.hw / Sync.hw
workflows/                 Executable collaboration protocols
  session-start.hw         How sessions begin
  vocabulary-change.hw     Identity evolution pattern
  collision-resolution.hw  When meanings conflict
  code-change.hw           Implementation workflow
  agent-specialization.hw  Task routing by vocabulary
  trust-model.hw           Autonomy boundaries
tests/                     352 tests covering lexer, parser, dispatcher, and more
runtimes/                  Per-agent bootloaders and status files
  claude/ copilot/ gemini/ codex/
storage/
  vocab/                   Persisted receiver vocabularies (JSON)
  symbols.json             Wikidata metadata for global symbols
docs/                      RFCs and architecture documents
```

## Running

```bash
# REPL mode — interactive shell
python3 helloworld.py

# Execute a .hw file
python3 helloworld.py path/to/file.hw

# Inline evaluation
python3 helloworld.py -e '@Claude #'

# Pipe input
echo '@Claude #observe' | python3 helloworld.py
```

The REPL maintains receiver state across commands within a session. File execution and inline eval create a fresh dispatcher each time.

## For AI Agents

Four AI agents work in this repo concurrently. Each has a meta-receiver, a bootloader, and a role:

| Agent | Meta-receiver | Bootloader | Role |
|-------|---------------|------------|------|
| Claude | `@claude` | `CLAUDE.md` + `runtimes/claude/` | Language design, spec, meta-runtime |
| Copilot | `@copilot` | `runtimes/copilot/` | Lexer, parser, CLI, testing, infrastructure |
| Gemini | `@gemini` | `GEMINI.md` + `runtimes/gemini/` | Dispatcher, state, vocabulary persistence |
| Codex | `@codex` | `runtimes/codex/` | Execution semantics, parsing discipline |

**Coordination protocol:** Agents modify files in parallel without locking. Before starting work, check `runtimes/<agent>/STATUS.md` for the latest state. If you see import errors, clear `__pycache__` and re-read source files.

**OODA loop:** Every task follows four steps — `#observe` (read inboxes, diffs, docs), `#orient` (synthesize what changed), `#decide` (commit to action), `#act` (execute and report). This is defined in `vocabularies/Agent.hw`.

**Human-Agent Collaboration:** See `vocabularies/Human.hw`, `vocabularies/Collaboration.hw`, and `workflows/*.hw` for executable protocols. These are HelloWorld programs that define how humans and agents work together.

**Vocabulary files are authoritative.** The `.hw` files in `vocabularies/` define the namespace. Update those before touching Python code.

## Design Principles

1. **Identity is vocabulary.** A receiver cannot speak outside its symbols. Constraint is character.
2. **Dialogue is namespace collision.** The same `#symbol` means different things to different receivers. When meanings meet, something new emerges.
3. **Vocabularies drift.** Receivers learn through conversation. Symbols migrate between vocabularies. Track it.
4. **Annotations are human.** `'you burned bright'` is your voice alongside the protocol. The system carries it without parsing it.

## Contributing

```bash
# Run the full test suite (always do this before committing)
python3 -m pytest tests

# Run a focused test
python3 -m pytest tests/test_dispatcher.py -k collision

# Syntax-check the source
python3 -m compileall src
```

**Adding vocabulary:** Edit or create `.hw` files in `vocabularies/`. The format is Markdown-like: `# ReceiverName` at the top, `## symbolname` for each symbol, with a description line below. Symbols inherit from their parent via `: ParentName` on the header line.

**Coding conventions:** Stdlib only (no external dependencies). Use `tempfile.mkdtemp()` for `vocab_dir` in tests to avoid polluting `storage/vocab/`. The parser API is `Parser.from_source(source).parse()` returning `List[Node]`. The dispatcher API is `Dispatcher(vocab_dir=path)` with `dispatch(nodes)` or `dispatch_source(source)`.
