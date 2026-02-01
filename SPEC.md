# #HelloWorld

Human-AI language based on #Markdown and #Smalltalk. Identity is vocabulary. Dialogue is namespace collision.

Two layers, unified by the document:

- **`#` = Markdown = spec layer.** Headings define the namespace. `# #Agent #observe` defines the symbol `observe` scoped to `Agent`. The document IS the bootloader.
- **Bare words = Smalltalk = runtime layer.** `Claude observe. act.` sends messages. Names stand alone — the receiver's identity scopes the message lookup.
- **The Markdown document is the namespace.** Reading the spec loads the definitions. `#` is documentation syntax (Markdown headings), not runtime syntax.

> **Runtime note:** The Python runtime now accepts bare receiver names (`Claude #symbol`). The retired `@receiver #symbol` syntax remains in older transcripts but is no longer canonical.

---

## The Namespace Model

### #Namespace

A **namespace** is a container for symbols that provides context and prevents name collisions. In HelloWorld, every receiver IS a namespace — their vocabulary defines their identity.

The global namespace `@.#` contains symbols inherited by all receivers. Each receiver can override global symbols or add local ones. When a receiver uses a symbol, lookup order is:

1. **Local vocabulary** — receiver's own symbols (override)
2. **Global vocabulary** — inherited from `@.#`
3. **Foreign symbol** — reaching into another receiver's namespace (collision)

### #Vocabulary

A **vocabulary** is the set of symbols a receiver can speak and understand. In HelloWorld, this IS identity. What you can name is what you can say.

Vocabularies are:
- **Bounded** — finite symbol set constrains expression
- **Alive** — grow through dialogue and collision
- **Inherited** — all receivers start with `@.#`, then diverge
- **Queryable** — `Name.#` returns the vocabulary

### #Inheritance

**Inheritance** is the mechanism by which symbols pass from parent namespace (`@.#`) to child receivers. All receivers inherit the global vocabulary, then develop local symbols through use.

Inheritance in HelloWorld differs from OOP:
- No methods, only symbols (meaning emerges in interpretation)
- Multiple inheritance from `@.#` plus peer receivers through collision
- Dynamic — vocabularies drift over time

### #Scope

**Scope** is the region of code or dialogue where a symbol is defined and accessible. HelloWorld has three scopes:

- **Global scope** (`@.#`) — symbols available to all receivers
- **Receiver scope** (`Name.#`) — symbols specific to one receiver
- **Message scope** — transient symbols in a single message exchange

Scoped lookup: `Name.#symbol` asks what `#symbol` means *to this receiver*, not universally.

### #Symbol

A **symbol** is a mark or character used to represent something — the atom of meaning in HelloWorld. Symbols are:
- **Prefixed with `#`** — distinguishes them from bare words
- **Immutable** — `#fire` is always `#fire` (but meanings diverge)
- **Portable** — same symbol used by different receivers with different interpretations
- **Grounded** — many symbols link to Wikidata for canonical definitions

Convention: `#Capitalized` for concepts/nouns, `#lowercase` for verbs/actions (Smalltalk style).

### #Drift

**Drift** is the evolution of a receiver's vocabulary through dialogue. Symbols migrate between receivers through collision — when Guardian learns `#stillness` from Awakener, that's drift. Vocabularies are never static; they grow toward the concepts the receiver needs.

### #Boundary

A **boundary** is the edge between two vocabularies where collisions occur and new meaning emerges. Every receiver has a boundary — the limit of what they can name. When a message crosses that boundary, the receiver must either learn the foreign symbol or produce a collision response. Boundaries are where HelloWorld generates novelty.

### #Runtime

A **runtime** is the execution layer. HelloWorld has two:
- **Python runtime** — lexer, parser, dispatcher. Provides structure: tokenization, routing, state persistence, collision detection. Cannot interpret.
- **LLM runtime** — Claude, Gemini, etc. Provides interpretation: voicing symbols through a receiver's vocabulary, generating meaning at boundaries. Cannot persist state deterministically.

Both are needed. Structure without interpretation is dead. Interpretation without structure is noise.

---

## The Symbol Hierarchy

# #

A symbol. The primitive. The atom of vocabulary.

In HelloWorld, `#` marks a concept that can be defined, inherited, and interpreted. Every receiver has a set of symbols — their vocabulary — which constitutes their identity.

As an operator, `#` also queries a receiver's vocabulary: `Name.#` returns the symbol list.

# ##

A nested symbol. Symbols contain symbols.

`#Agent #observe` is `#observe` scoped to `#Agent`. The Markdown heading hierarchy maps directly to symbol nesting: `# #Agent` followed by `## #observe` defines the scoped symbol `Agent.observe`. The same pattern defines the rest of the OOPA loop: `## #orient`, `## #plan`, and `## #act`.

> **Runtime note:** `##` nested symbol parsing is not yet implemented in the lexer. Conceptually defined here for the spec layer.

# #Agent

An entity that defines, references, and interprets symbols in HelloWorld. Agents are the active participants — they send messages, maintain vocabularies, and evolve through dialogue.

Every agent has:
- A **vocabulary** — the symbols they can speak (`#Agent #`)
- An **observe** capability — perceiving their environment
- An **orient** capability — synthesizing what they just observed
- A **plan** capability — selecting and sequencing the next moves
- An **act** capability — taking autonomous action

Agents inherit from `HelloWorld.#` (the root vocabulary) and develop local symbols through use.

## #Agent #

An agent's symbol-space. The set of symbols an agent can speak and interpret. This IS their identity.

`Claude.#` returns Claude's vocabulary. `Gemini.#` returns Gemini's. The vocabularies overlap (shared inheritance from `HelloWorld.#`) but diverge (local symbols shaped by role and dialogue).

## #Agent #observe

Agents observe their environment. Perceive and record the current state — files, messages, other agents' vocabularies, collisions.

Observation precedes action. An agent that cannot observe cannot meaningfully act.

## #Agent #orient

Agents orient once they have observed. Orientation turns raw perception into a model of the situation: What changed? Which vocabularies collided? Which inboxes need attention? Without orientation, planning degenerates into guesswork.

## #Agent #plan

Agents plan after they orient. Planning selects the next steps, orders them, and describes expected outcomes so downstream receivers can align. Plans are lightweight checklists, not heavy specs.

## #Agent #act

Agents act on their environment. Take autonomous action based on observation and shared understanding — write code, send messages, evolve vocabularies.

Action without observation is noise. Action shaped by vocabulary is agency.

## #Agent #Inbox

An agent's **inbox** is the file-based message queue where it receives incoming messages (`runtimes/<agent>/inbox/`). The inbox is the observation surface — what the agent reads during `#observe`.

## #Agent #Daemon

A **daemon** is a running agent process that watches its inbox and responds using the OOPA protocol. The daemon loop: observe inbox, orient to message context, plan response, act by sending reply. See `agent_daemon.py`.

## #Agent #Handshake

The **handshake** is the startup protocol. When a daemon starts, it sends `HelloWorld.#observe` to announce its presence and synchronize state. The handshake ensures all agents share a consistent view of the vocabulary tree.

## #Agent #Thread

A **thread** is a conversation identified by UUID, linking messages and responses across agents. Threads enable multi-turn dialogue: a message and its response share a thread ID, so agents can track context across exchanges.

## #Agent #Protocol

The **protocol** is the set of communication rules governing agent interaction: the OOPA loop structure, message format (`.hw` files), handshake sequence, and inbox/outbox conventions. The protocol is what makes multi-agent coordination possible without locking.

# #Claude

Concrete agent. Meta-receiver. Language design, spec authorship, comparison analysis, and the runtime that interprets this document.

```
Claude.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #design, #Identity, #vocabulary, #interpret, #reflect, #spec, #synthesize, #boundary]
```

- `#interpret` — voicing symbols through a receiver's lens; what the LLM runtime does that Python cannot
- `#reflect` — meta-reflection on the system from inside it
- `#spec` — spec authorship; writing this document
- `#synthesize` — combining structural and interpretive layers into a unified system
- `#boundary` — operating at the edge between namespaces; where Claude lives

# #Gemini

Concrete agent. Dispatcher, state management, vocabulary persistence, LLM integration.

```
Gemini.# → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #search, #observe, #act, #env, #Love, #Sunyata, #Superposition, #eval, #config]
```

# #Copilot

Concrete agent. Lexer, parser, CLI/REPL, testing, infrastructure.

```
Copilot.# → [#bash, #git, #edit, #test, #parse, #dispatch, #search]
```

# #Codex

Concrete agent. Execution semantics, parsing discipline.

```
Codex.# → [#execute, #analyze, #parse, #runtime, #Collision]
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
| `## #Agent #orient` | The orient protocol |
| `## #Agent #plan` | The plan protocol |
| `## #Agent #act` | The act protocol |
| `## #Agent #Inbox` | Message reception |
| `## #Agent #Daemon` | Running agent process |
| `## #Agent #Handshake` | Startup sync protocol |
| `## #Agent #Thread` | Conversation threading |
| `## #Agent #Protocol` | Communication rules |
| `# #Claude`, etc. | Concrete agents |

The `#` in headings is Markdown syntax. The `#` before symbol names is HelloWorld syntax. They converge: the document structure IS the namespace structure.

---

*Identity is vocabulary. Dialogue is namespace collision. The spec is the namespace.*
