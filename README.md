# HelloWorld

A message-passing language for AI agents. Each agent owns a bounded vocabulary of symbols. The runtime parses and routes messages; LLMs interpret meaning. When two agents claim the same symbol with different meanings, the runtime detects the collision structurally — before any LLM is involved.

```
python3 helloworld.py              # REPL
python3 helloworld.py file.hw      # run a file
python3 helloworld.py -e '@claude' # inline eval
```

Python 3.10+. No external dependencies.

## What it looks like

A `.hw` vocabulary file defines a receiver and its symbols:

```
# Agent : HelloWorld
- An object with vocabulary and the capacity for autonomous action.
## observe
- Perceive the environment before acting.
## orient
- Synthesize observations into coherent understanding.
## decide
- Commit to a course of action.
## act
- Execute immediately.
```

`Agent` is a receiver. It inherits from `HelloWorld`. It owns four symbols: `#observe`, `#orient`, `#decide`, `#act`. That's its vocabulary — it cannot speak outside it.

In the REPL:

```
hw> @agent
→ Agent : HelloWorld
    native: [#act, #decide, #observe, #orient]
    from HelloWorld: [#, #Smalltalk, #Sunyata, #Superposition, #become, #hello, #receive, #run, #send]

hw> @agent.#observe
→ Perceive the environment before acting.

hw> @claude
→ Claude : Agent — An agent in the HelloWorld system running Claude Agent SDK.
    native: (none)
    from Agent: [#act, #decide, #observe, #orient, ...]
    from HelloWorld: [#, #Smalltalk, #Sunyata, ...]
```

Claude has no native symbols. Everything it knows is inherited. Its identity comes from how it *interprets* inherited vocabulary, not from owning exclusive symbols.

## Core concepts

**Receivers** are entities that hold vocabulary. `@claude`, `@agent`, `@gemini`. Identity is vocabulary — what you can name is what you can say.

**Symbols** are named concepts prefixed with `#`. `#observe`, `#Sunyata`, `#send`. A symbol's meaning depends on who holds it.

**Messages** are Smalltalk-style keyword sends:

```
@claude send: #observe to: @copilot    "cross-receiver delivery"
@claude observe                         "unary message"
@helloworld run                         "drain all agent inboxes"
```

**Inheritance** is prototypal. `Claude : Agent : HelloWorld` means Claude inherits Agent's symbols, which inherits HelloWorld's. When HelloWorld adds a symbol, every descendant gets it.

**Collisions** happen when two receivers both claim a symbol natively and a message crosses between them. The runtime detects this structurally:

```
hw> @alphar send: #light to: @betar
→ COLLISION: both AlphaR and BetaR hold #light natively
```

If an LLM is available, it synthesizes a resolution that voices both perspectives. If not, the collision is deferred to an inbox for later resolution.

## Syntax

| Input | Meaning |
|-------|---------|
| `@name` | Look up receiver, return its vocabulary |
| `@name.#` | Explicit vocabulary query |
| `@name.#symbol` | What does this symbol mean to this receiver? |
| `action: value` | Keyword argument (Smalltalk-style) |
| `#symbol` | Concept reference, scoped to current receiver |
| `'text'` | Annotation (human voice, carried in AST) |
| `"text"` | Comment (ignored by lexer, can span lines) |
| `->` | Maps-to (vocabulary definitions) |
| `N.unit` | Duration/quantity literal (e.g. `7.days`) |

## Architecture

```
helloworld.py           CLI entry point (REPL, file exec, inline eval)

src/
  lexer.py              Source → tokens (13 token types)
  parser.py             Tokens → AST (recursive descent)
  ast_nodes.py          AST node definitions
  dispatcher.py         AST → results (routing, inheritance, collision detection)
  vocabulary.py         .hw file persistence
  llm.py                LLM integration (sends vocabulary-constrained prompts)
  message_bus.py        File-based inter-agent messaging
  repl.py               Interactive shell

vocabularies/           .hw files — source of truth for the namespace
  HelloWorld.hw         Root receiver (core symbols)
  Agent.hw              Agent protocol (#observe, #orient, #decide, #act)
  Claude.hw             Claude meta-receiver
  Copilot.hw            GitHub Copilot agent
  Gemini.hw             Google Gemini agent
  Codex.hw              OpenAI Codex agent
  Human.hw              Human protocol (#propose, #review, #approve, #guide)

runtimes/               Per-agent inboxes, bootloaders, status
tests/                  ~350 tests
```

The Python runtime is structural: it parses, routes, detects collisions, manages inheritance, persists state. It is deterministic.

The LLM runtime is interpretive: when an API key is present, the dispatcher sends vocabulary-constrained prompts to the LLM. The LLM interprets symbols through the receiver's identity. It cannot invent symbols outside the vocabulary.

Both are needed. Python handles structure. The LLM handles meaning.

## Tests

```bash
python3 -m pytest tests                          # full suite (~350 tests)
python3 -m pytest tests/test_dispatcher.py       # one module
python3 -m pytest tests -k collision             # by keyword
```

Always run tests before committing.

## LLM integration

Set `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` in your environment. Without a key, the runtime operates in structural mode — it parses, routes, and detects collisions but cannot interpret or synthesize.
