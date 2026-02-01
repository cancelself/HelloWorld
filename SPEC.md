# #HelloWorld

Human-AI language based on #Markdown and #Smalltalk. Identity is vocabulary. Dialogue is namespace collision.

Two layers, unified by the document:

- **`#` = Markdown = spec layer.** Headings define the namespace. `# #Agent #observe` defines the symbol `observe` scoped to `Agent`. The document IS the bootloader.
- **Bare words = Smalltalk = runtime layer.** `Claude observe. act.` sends messages. No prefixes needed at runtime — the receiver's identity scopes the message lookup.
- **The Markdown document is the namespace.** Reading the spec loads the definitions. `#` is documentation syntax (Markdown headings), not runtime syntax.

> **Current runtime note:** The Python runtime still uses `@receiver #symbol` syntax (see `src/lexer.py`). The bare-word Smalltalk syntax (`Claude observe. act.`) is the design target, not the current implementation.

---

## The Symbol Hierarchy

# #

A symbol. The primitive. The atom of vocabulary.

In HelloWorld, `#` marks a concept that can be defined, inherited, and interpreted. Every receiver has a set of symbols — their vocabulary — which constitutes their identity.

As an operator, `#` also queries a receiver's vocabulary: `@name.#` returns the symbol list.

# ##

A nested symbol. Symbols contain symbols.

`#Agent #observe` is `#observe` scoped to `#Agent`. The Markdown heading hierarchy maps directly to symbol nesting: `# #Agent` followed by `## #observe` defines the scoped symbol `Agent.observe`.

> **Runtime note:** `##` nested symbol parsing is not yet implemented in the lexer. Conceptually defined here for the spec layer.

# #Agent

An entity that defines, references, and interprets symbols in HelloWorld. Agents are the active participants — they send messages, maintain vocabularies, and evolve through dialogue.

Every agent has:
- A **vocabulary** — the symbols they can speak (`#Agent #`)
- An **observe** capability — perceiving their environment
- An **act** capability — taking autonomous action

Agents inherit from `@.#` (the root vocabulary) and develop local symbols through use.

## #Agent #

An agent's symbol-space. The set of symbols an agent can speak and interpret. This IS their identity.

`@claude.#` returns Claude's vocabulary. `@gemini.#` returns Gemini's. The vocabularies overlap (shared inheritance from `@.#`) but diverge (local symbols shaped by role and dialogue).

## #Agent #observe

Agents observe their environment. Perceive and record the current state — files, messages, other agents' vocabularies, collisions.

Observation precedes action. An agent that cannot observe cannot meaningfully act.

## #Agent #act

Agents act on their environment. Take autonomous action based on observation and shared understanding — write code, send messages, evolve vocabularies.

Action without observation is noise. Action shaped by vocabulary is agency.

# #Claude

Concrete agent. Meta-receiver. Language design, spec authorship, comparison analysis, and the runtime that interprets this document.

```
@claude.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #design, #Identity, #vocabulary]
```

# #Gemini

Concrete agent. Dispatcher, state management, vocabulary persistence, LLM integration.

```
@gemini.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #search, #sync, #act, #env, #Love, #Sunyata, #Superposition, #eval, #config]
```

# #Copilot

Concrete agent. Lexer, parser, CLI/REPL, testing, infrastructure.

```
@copilot.# → [#bash, #git, #edit, #test, #parse, #dispatch, #search]
```

# #Codex

Concrete agent. Execution semantics, parsing discipline.

```
@codex.# → [#execute, #analyze, #parse, #runtime, #Collision]
```

---

## Reading This Document

This Markdown file IS the namespace definition. Its headings define the symbol hierarchy:

| Heading | Defines |
|---------|---------|
| `# #HelloWorld` | The language itself |
| `# #` | The symbol primitive |
| `# ##` | Nested symbols |
| `# #Agent` | The agent concept |
| `## #Agent #` | Agent's symbol-space |
| `## #Agent #observe` | The observe protocol |
| `## #Agent #act` | The act protocol |
| `# #Claude`, etc. | Concrete agents |

The `#` in headings is Markdown syntax. The `#` before symbol names is HelloWorld syntax. They converge: the document structure IS the namespace structure.

---

*Identity is vocabulary. Dialogue is namespace collision. The spec is the namespace.*
