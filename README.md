# HelloWorld v0.1

A message-passing language where **identity is vocabulary** and **the LLM is the runtime**.

## How It Works

There is no compiler. There is no interpreter binary. You type HelloWorld syntax into a conversation with an LLM, and it parses it, maintains receiver state, and responds. The language runs on dialogue.

Every receiver (`@target`) *is* its namespace — a bounded vocabulary of `#symbols`. What a receiver can name is what it can say. Communication happens when you send a message to a receiver, and the runtime responds as that receiver, constrained by its vocabulary.

When two receivers share a symbol, their meanings collide. That's where the language gets interesting.

The runtime itself is a receiver. `@claude`, `@gemini`, `@copilot`, `@codex` — each has its own vocabulary shaped by its training. The same HelloWorld session produces different results on different runtimes, because the runtime's identity bleeds into the receivers it hosts.

## Syntax

```
@receiver action: #symbol key: value 'annotation'
```

### Primitives

| Element | What it does |
|---------|-------------|
| `@target` | Address a receiver (or query its vocabulary if bare) |
| `#symbol` | Reference a concept, scoped to the receiver in context |
| `@target #symbol` | Ask what `#symbol` means *to this receiver* |
| `@target #` | List this receiver's full vocabulary |
| `action: value` | Keyword argument (Smalltalk-style, chainable) |
| `'text'` | Annotation — your voice alongside the protocol |
| `N.unit` | Duration or quantity literal (`7.days`, `3.breaths`) |
| `→` | Maps-to (vocabulary definitions) |
| `# text` | Comment |

## Shared Vocabulary

- `SPEC.md` is the namespace authority; `docs/NAMESPACE_DEFINITIONS.md` mirrors it for coordination. Add or change symbols there *before* touching code.
- Symbol lookup has three outcomes: **native** (receiver owns it), **inherited** (`HelloWorld #` owns it), or **unknown** (nobody owns it yet, so the receiver must search, define, and learn). Unknown is absence; **collision** is when two receivers both own a symbol but disagree on meaning.
- Use the Markdown form `Name #symbol` (no dots) when querying vocabularies; every runtime bootloader reads this document verbatim.
- All agents run the OOPA loop defined under `# #Agent` in `SPEC.md`:
  - `#observe` — read inboxes, diffs, and docs before editing.
  - `#orient` — summarize what changed and where collisions might occur.
  - `#plan` — share lightweight step lists so peers can align.
  - `#act` — apply the plan (code edits, tests, or replies) and report back.

## Usage

### Query a receiver's identity

```
@guardian
→ [#fire, #vision, #challenge, #gift, #threshold]
```

### Send a message

```
@guardian sendVision: #entropy withContext: lastNightSleep 'you burned bright'
```

The runtime responds *as* `@guardian`, using `@guardian`'s vocabulary.

### Scoped meaning

```
@guardian #fire
@awakener #fire
```

Same symbol, different receiver, different meaning.

### Namespace collision

```
@guardian sendVision: #stillness withContext: @awakener
```

`#stillness` belongs to `@awakener`. When `@guardian` reaches for it, something new emerges at the boundary.

## Bootstrap

Two receivers are initialized by default:

```
@awakener # → [#stillness, #entropy, #intention, #sleep, #insight]
@guardian # → [#fire, #vision, #challenge, #gift, #threshold]
```

The meta-receiver is always available — `@claude`, `@gemini`, `@copilot`, or `@codex` depending on which runtime you're in. It's the runtime reflecting on itself.

New receivers can be introduced at any time. The runtime will ask for or infer their initial vocabulary.

## Tooling

A Python lexer tokenizes HelloWorld source, mirroring the parsing rules each runtime follows:

```python
from src.lexer import Lexer

tokens = Lexer("@guardian sendVision: #entropy").tokenize()
```

```bash
python3 -m pytest tests           # run all tests
python3 -m pytest tests -k token  # focused run
```

`.hw` is the file extension for HelloWorld source. See [`examples/bootstrap.hw`](examples/bootstrap.hw).

## Runtimes

HelloWorld runs on any LLM that can follow a bootloader. Each runtime uses the instruction format native to its platform:

| Runtime | Meta-receiver | Bootloader | Format |
|---------|--------------|------------|--------|
| Claude | `@claude` | [`Claude.md`](Claude.md) | CLAUDE.md (Claude Code) |
| Copilot | `@copilot` | [`runtimes/copilot/`](runtimes/copilot/) | copilot-instructions.md |
| Gemini | `@gemini` | [`runtimes/gemini/`](runtimes/gemini/) + [`GEMINI.md`](GEMINI.md) | System instruction |
| Codex | `@codex` | [`runtimes/codex/`](runtimes/codex/) + [`AGENTS.md`](AGENTS.md) + [`CODEX.md`](CODEX.md) | AGENTS.md |

The spec is identical across runtimes. Only the meta-receiver changes. The difference in output is the point.

## Teaching Example

See [`examples/01-identity.md`](examples/01-identity.md) — five lines that isolate each primitive and reveal how runtimes differ. Designed to be pasted into any runtime that has loaded its bootloader.

## Architecture

See [`docs/copilot-runtime.md`](docs/copilot-runtime.md) for a deep dive on how a tool-calling LLM maps HelloWorld messages to executable infrastructure.

---

*Identity is vocabulary. Dialogue is namespace collision.*
