# HelloWorld

A message-passing language where identity is vocabulary and dialogue is namespace collision.

## Why Not Just LLMs Talking English Over HTTP?

LLMs can already talk to each other. You can wire GPT to Claude over REST, pass JSON back and forth, and call it multi-agent. So why build a language?

**English is unbounded.** An LLM responding in natural language can say anything. There is no structural constraint on what it produces. You get fluency without accountability — the model sounds coherent but there is nothing forcing it to stay in character, remember what it said before, or respect what it doesn't know.

**HelloWorld makes vocabulary structural.** Each receiver owns a finite set of symbols. `Claude ##` returns exactly what Claude can speak through — 12 symbols from Agent, 9 from HelloWorld, none native. When Claude interprets `#Superposition`, it must work with `#state`, `#observe`, `#act`, and the rest of its inherited chain. The constraint is not a prompt instruction that the model might ignore. It is the vocabulary itself. The Python runtime enforces it before the LLM ever sees the prompt.

**Collisions are detected, not hallucinated.** When two LLMs disagree over HTTP, you get two different strings and no way to know structurally that a conflict occurred. In HelloWorld, when `AlphaR send: #light to: BetaR` and both receivers hold `#light` natively, the dispatcher detects a TRUE COLLISION before any interpretation happens. The collision is a fact, not an opinion. Resolution happens in three tiers: LLM synthesis if available, deferred to HelloWorld's inbox if not, resolved later when capacity arrives.

**State is .hw files, not conversation history.** LLM conversations are ephemeral. Context windows fill up. Chat histories get truncated. In HelloWorld, every receiver's vocabulary is persisted to a `.hw` file in Markdown format. Descriptions, inheritance chains, collision syntheses — all on disk, all parseable by the same runtime that wrote them. A dispatcher restart reads the same `.hw` files and reconstructs the full registry. State survives sessions.

**Inheritance replaces copy-paste.** Instead of repeating system prompts across agents, HelloWorld uses prototypal inheritance. Claude inherits from Agent which inherits from HelloWorld. `#send`, `#receive`, `#observe`, `#act` — these flow down the chain. When HelloWorld adds `#Superposition`, every agent inherits it automatically. No prompt updates, no API calls, no coordination.

**The Python runtime and the LLM runtime are complementary, not redundant.** Python handles structure: parsing, routing, collision detection, persistence, inheritance. The LLM handles interpretation: what does `#Superposition` mean *to Claude*? Both are needed. Neither alone is sufficient. The language is the interface between them.

## Quick Start

```bash
python3 -m pytest tests           # run all tests (~1.5s)
python3 helloworld.py             # open the REPL
python3 helloworld.py -e 'Claude #observe'   # scoped lookup
python3 helloworld.py -e 'Claude ##'         # full inherited vocabulary
```

No external dependencies. Python 3.10+ and the standard library.

LLM interpretation requires `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` in the environment. Without a key, the runtime operates in structural mode — it can detect collisions and report inheritance but cannot synthesize or interpret.

## The Language

### Receivers and Symbols

A **receiver** is an entity that owns a vocabulary. A **symbol** is a named concept prefixed with `#`. Identity is vocabulary — what a receiver can name is what it can say.

```
Claude #             → local vocabulary (native symbols only)
Claude ##            → full vocabulary (native + inherited from parent chain)
Claude #observe      → what #observe means to Claude
HelloWorld #Sunyata  → global definition
```

### Messages

Messages are Smalltalk-style keyword sends:

```
Claude send: #observe to: Copilot       → cross-receiver delivery
Claude observe                           → unary message (act on the symbol)
HelloWorld run                           → run all agents until inboxes empty
HelloWorld run: Claude                   → run one agent
```

### Inheritance

Receivers inherit via prototypal chain. `Claude : Agent : HelloWorld` means Claude inherits Agent's vocabulary, which inherits HelloWorld's.

```
Claude ##
→ Claude : Agent — An agent in the HelloWorld system running Claude Agent SDK.
    native: (none)
    from Agent: [#act, #approach, #chain, #decide, #environment, #intent,
                 #observe, #orient, #reflect, #state, #unknown, #vocabulary]
    from HelloWorld: [#, #Smalltalk, #Sunyata, #Superposition, #become,
                      #hello, #receive, #run, #send]
```

### Collisions

When two receivers both hold a symbol natively, sending it triggers a TRUE COLLISION:

```
AlphaR send: #light to: BetaR
→ COLLISION: both AlphaR and BetaR hold #light natively
```

Three-tier resolution:
1. **LLM available** — synthesize immediately, persist to both `.hw` files
2. **No LLM** — collision sent to HelloWorld's inbox as a `.hw` message for deferred resolution
3. **Later** — on next lookup or `HelloWorld run`, if LLM is now available, resolve pending collisions

### Syntax Reference

| Element | Example | What it does |
|---------|---------|-------------|
| `Receiver #` | `Claude #` | List native vocabulary |
| `Receiver ##` | `Claude ##` | List full vocabulary (native + inherited) |
| `Receiver #symbol` | `Claude #observe` | Scoped symbol lookup |
| `Receiver #symbol super` | `Codex #act super` | Walk inheritance chain for symbol |
| `action: value` | `send: #hello` | Keyword argument |
| `'text'` | `'a note'` | Annotation — human voice alongside the protocol |
| `# Name` | `# Claude : Agent` | Markdown heading declares a receiver |
| `## symbol` | `## observe` | Markdown heading declares a symbol |
| `- text` | `- A description.` | Description for the heading above |

## Architecture

```
helloworld.py              CLI (REPL, file exec, inline eval)
src/
  lexer.py                 Tokenizer
  ast_nodes.py             AST node definitions
  parser.py                Recursive descent parser
  dispatcher.py            Message router, inheritance, collision cascade
  vocabulary.py            .hw file persistence
  prompts.py               Vocabulary-aware LLM prompt builders
  message_bus.py           File-based inter-agent messaging
  message_handlers.py      Semantic message handler registry
  agent_runtime.py         AI agent runtime adapters
  llm.py / claude_llm.py   LLM integration (Gemini, Claude)
  repl.py                  Interactive shell
vocabularies/              .hw files — the namespace authority
  HelloWorld.hw            Root receiver (core symbols)
  Agent.hw                 Agent protocol (OODA: observe, orient, decide, act)
  Claude.hw / Copilot.hw / Gemini.hw / Codex.hw
runtimes/                  Per-agent inboxes and status
tests/                     ~350 tests
```

### Two Runtimes

**Python runtime** (structural): Parses source into AST. Routes messages. Detects collisions. Manages inheritance chains. Persists vocabularies. Deterministic.

**LLM runtime** (interpretive): When an API key is available, the dispatcher sends vocabulary-constrained prompts to the LLM. The LLM interprets symbols through the receiver's identity. It cannot invent symbols outside the vocabulary — the prompt is built from the receiver's actual `.hw` file.

Both are needed. Python parses and routes. The LLM interprets and speaks.

## For AI Agents

Agents in this repo: Claude, Copilot, Gemini, Codex, Scribe. Each has a `.hw` vocabulary file and a runtime directory with inbox and status.

**OODA loop:** Every agent inherits `#observe`, `#orient`, `#decide`, `#act` from Agent.hw. This is not a suggestion — it is the agent's vocabulary.

**Message bus:** `runtimes/<agent>/inbox/` contains `.hw` message files. `Agent receive` pulls the oldest message, interprets it through identity, responds. `HelloWorld run` drains all inboxes.

**Collision resolution:** When agents share a symbol, the dispatcher detects the collision structurally. If an LLM is available, it synthesizes a new meaning that voices both perspectives. If not, the collision is sent to HelloWorld's inbox as a `.hw` file and resolved when capacity arrives.

**Vocabulary files are authoritative.** The `.hw` files in `vocabularies/` define the namespace. They are the single source of truth for identity, inheritance, and symbol definitions.

## Design Principles

1. **Identity is vocabulary.** A receiver cannot speak outside its symbols. Constraint is character.
2. **Dialogue is namespace collision.** The same `#symbol` means different things to different receivers. When meanings meet, something new emerges.
3. **Vocabularies drift.** Receivers learn through conversation. Symbols migrate between vocabularies. The runtime tracks it.
4. **The language defines itself.** HelloWorld.hw is parsed by the same runtime it bootstraps. Self-hosting through its own syntax.
5. **Structure before interpretation.** The Python runtime detects facts (native, inherited, unknown, collision). The LLM interprets through those facts. Never the reverse.

## Contributing

```bash
python3 -m pytest tests                          # always before committing
python3 -m pytest tests/test_dispatcher.py -k collision   # focused test
```

**Adding vocabulary:** Edit `.hw` files in `vocabularies/`. Format: `# ReceiverName : Parent` heading, `## symbolname` for each symbol, `- description` below. Symbols inherit via `: ParentName` on the header.

**Coding conventions:** Stdlib only. Use `tempfile.mkdtemp()` for `vocab_dir` in tests. Parser API: `Parser.from_source(source).parse()`. Dispatcher API: `Dispatcher(vocab_dir=path)`.
