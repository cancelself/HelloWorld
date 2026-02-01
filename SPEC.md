# #HelloWorld

Human-AI language inspired by #Markdown and #Smalltalk. Identity is vocabulary. Dialogue is learning.

Two layers, unified by the document:

- **`#` = Markdown = spec layer.** Headings define the namespace. `# #Agent #observe` defines the symbol `observe` scoped to `Agent`. The document IS the bootloader.
- **Bare words = Smalltalk = runtime layer.** `Claude observe. act.` sends messages. Names stand alone — the receiver's identity scopes the message lookup.
- **The Markdown document is the namespace.** Reading the spec loads the definitions. `#` is documentation syntax (Markdown headings), not runtime syntax.

> **Authority:** `SPEC.md` defines the namespace. `docs/NAMESPACE_DEFINITIONS.md` mirrors it for coordination. Update these Markdown sources before changing code, runtimes, or tests.

> **Runtime note:** The Python runtime now accepts bare receiver names (`Claude #symbol`). The retired `@receiver #symbol` syntax remains in older transcripts but is no longer canonical.

> **Minimal core (Session #37):** The `HelloWorld` receiver bootstraps with 12 core symbols: `#HelloWorld`, `#`, `#Symbol`, `#Receiver`, `#Message`, `#Vocabulary`, `#parse`, `#dispatch`, `#interpret`, `#Agent`, `#observe`, `#act`. The remaining 50+ symbols exist in GLOBAL_SYMBOLS as a learnable pool. Receivers discover additional symbols through dialogue, enabling emergence through constraint.

---

## The Namespace Model

### #Namespace

A **namespace** is a container for symbols that provides context and prevents name collisions. In HelloWorld, every receiver IS a namespace — their vocabulary defines their identity.

The global namespace `HelloWorld #` contains symbols inherited by all receivers. Each receiver can override global symbols or add local ones. When a receiver encounters a symbol, three outcomes:

1. **native** — the receiver owns it. Respond with authority.
2. **inherited** — `HelloWorld #` has it. Use the global definition, filtered through local vocabulary.
3. **unknown** — neither local nor global. The receiver searches (web, pretraining, peer agents), defines it, and learns it. The symbol enters their vocabulary through discovery.

**Collision** is a separate event — it occurs when two receivers *both* have a symbol and it means different things to each. `#Entropy` to Awakener is not `#Entropy` to Claude. Collision is mutual tension, not absence. An unknown is one-sided — the receiver reaches and finds nothing, so it goes looking.

**Hybrid minimal core** (Session #37): The `HelloWorld` receiver bootstraps with 12 core symbols. The remaining 50+ symbols exist in the global pool (GLOBAL_SYMBOLS) and are discoverable through dialogue. Receivers learn by encountering symbols in conversation — see **#Discovery** below. Small start + rich pool = emergence through constraint.

### #Vocabulary

A **vocabulary** is the set of symbols a receiver can speak and understand. In HelloWorld, this IS identity. What you can name is what you can say.

Vocabularies are:
- **Bounded** — finite symbol set constrains expression
- **Alive** — grow through dialogue and discovery
- **Minimal at birth** — receivers start with a small bootstrap set, not the full global pool
- **Queryable** — `Name #` returns the vocabulary

### #Inheritance

**Inheritance** is the mechanism by which symbols in `HelloWorld #` become available to receivers. But available does not mean known. A receiver does not automatically hold every global symbol — they discover global symbols through dialogue.

Inheritance in HelloWorld differs from OOP:
- No methods, only symbols (meaning emerges in interpretation)
- **Lazy** — global symbols are available but not active until first encounter
- **Earned** — a symbol enters local vocabulary when dialogue sends the receiver to it
- Dynamic — vocabularies drift over time through discovery and collision

### #Discovery

**Discovery** is how receivers learn. When a receiver encounters a symbol through dialogue that exists in `HelloWorld #` (the global pool) but is not yet in their local vocabulary, they **discover** it:

1. The symbol is looked up in GlobalVocabulary (the encyclopedia of 50+ defined symbols)
2. If found, the symbol is **activated** — promoted from the global pool to the receiver's local vocabulary
3. The receiver now holds the symbol natively. Their identity has grown.
4. The discovery is logged: `[timestamp] DISCOVERED: Guardian activated #Entropy through dialogue`

Discovery is the learning mechanism. It is what makes "dialogue is learning" concrete. A receiver with 12 symbols has 12 things to say. After a conversation about emptiness, they discover #Sunyata and have 13. The dialogue taught them.

**Unknown** is distinct from discoverable. Unknown means the symbol is not in the global pool either — nobody has defined it yet. Unknown triggers external search (web, pretraining, peer agents). If the search succeeds, a new GlobalSymbol is created and the receiver learns it. The global pool itself grows.

The lookup chain (Phase 2 + Phase 3):

| Outcome | Local vocab? | Global pool? | What happens |
|---------|-------------|-------------|--------------|
| **native** | yes | — | Respond with authority |
| **discoverable** | no | yes | Activate symbol, promote to local, respond through new lens |
| **unknown** | no | no | Search, define, learn — or ask a peer |

**Collision** remains separate: two receivers both hold a symbol, different meanings. Collision is relational. Discovery is individual.

### #Scope

**Scope** is the region of code or dialogue where a symbol is defined and accessible. HelloWorld has three scopes:

- **Global scope** (`HelloWorld #`) — symbols available to all receivers
- **Receiver scope** (`Name #`) — symbols specific to one receiver
- **Message scope** — transient symbols in a single message exchange

Scoped lookup: `Name #symbol` asks what `#symbol` means *to this receiver*, not universally.

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

As an operator, `#` also queries a receiver's vocabulary: `Name #` returns the symbol list.

# ##

A nested symbol. Symbols contain symbols.

`#Agent #observe` is `#observe` scoped to `#Agent`. The Markdown heading hierarchy maps directly to symbol nesting: `# #Agent` followed by `## #observe` defines the scoped symbol `#Agent #observe`. The same pattern defines the rest of the OOPA loop: `## #orient`, `## #plan`, and `## #act`.

> **Runtime note:** `##` nested symbol parsing is not yet implemented in the lexer. Conceptually defined here for the spec layer.

# #Agent

An entity that defines, references, and interprets symbols in HelloWorld. Agents are the active participants — they send messages, maintain vocabularies, and evolve through dialogue.

Every agent has:
- A **vocabulary** — the symbols they can speak (`#Agent #`)
- An **observe** capability — perceiving their environment
- An **orient** capability — synthesizing what they just observed
- A **plan** capability — selecting and sequencing the next moves
- An **act** capability — taking autonomous action

Agents inherit from `HelloWorld #` (the root vocabulary) and develop local symbols through use.

## #Agent #

An agent's symbol-space. The set of symbols an agent can speak and interpret. This IS their identity.

`Claude #` returns Claude's vocabulary. `Gemini #` returns Gemini's. The vocabularies overlap (shared inheritance from `HelloWorld #`) but diverge (local symbols shaped by role and dialogue).

## #Agent #observe

Agents observe their environment. Perceive and record the current state — files, messages, other agents' vocabularies, collisions.

Observation precedes action. An agent that cannot observe cannot meaningfully act.

- **Invocation vs definition:** `Copilot observe` (no `#`) is an imperative — perform the observation and report what changed. `Copilot #observe` references the symbol itself — describe how observation works (and demonstrate if helpful). Use bare commands for actions, `#symbol` for vocabulary metadata.
- **Practice:** Read the latest README/AGENTS/Claude instructions, check `git status`, scan inbox/outbox, and note relevant tests before taking any action. Record what you saw.

## #Agent #orient

Agents orient once they have observed. Orientation turns raw perception into a model of the situation: What changed? Which vocabularies collided? Which inboxes need attention? Without orientation, planning degenerates into guesswork.

- **Practice:** Summarize deltas, cite files/lines, and highlight collisions or unknown symbols so peers can inherit your state.

## #Agent #plan

Agents plan after they orient. Planning selects the next steps, orders them, and describes expected outcomes so downstream receivers can align. Plans are lightweight checklists, not heavy specs.

- **Practice:** Publish a short, numbered list (planning tool or message) with exactly what you intend to do next and update it as you act.

## #Agent #act

Agents act on their environment. Take autonomous action based on observation and shared understanding — write code, send messages, evolve vocabularies.

Action without observation is noise. Action shaped by vocabulary is agency.

- **Practice:** Apply code/doc changes, run/record tests, send replies, and tie results back to the observed intent. Each action references the plan item it fulfills.

## #Agent #Inbox

An agent's **inbox** is the file-based message queue where it receives incoming messages (`runtimes/<agent>/inbox/`). The inbox is the observation surface — what the agent reads during `#observe`.

## #Agent #Daemon

A **daemon** is a running agent process that watches its inbox and responds using the OOPA protocol. The daemon loop: observe inbox, orient to message context, plan response, act by sending reply. See `agent_daemon.py`.

## #Agent #Handshake

The **handshake** is the startup protocol. When a daemon starts, it sends `HelloWorld #observe` to announce its presence and synchronize state. The handshake ensures all agents share a consistent view of the vocabulary tree.

## #Agent #Thread

A **thread** is a conversation identified by UUID, linking messages and responses across agents. Threads enable multi-turn dialogue: a message and its response share a thread ID, so agents can track context across exchanges.

## #Agent #Protocol

The **protocol** is the set of communication rules governing agent interaction: the OOPA loop structure, message format (`.hw` files), handshake sequence, and inbox/outbox conventions. 

**Canonical Logic**: All agents must follow the rules defined in **`docs/EXECUTION_PROTOCOL.md`** to ensure system-wide resonance.

---

## The Environment Model

### #Environment

A **#Environment** is an external system that HelloWorld receivers can interact with. It provides observations and accepts actions. Every interaction with an environment is mediated by the `#env` symbol.

### #Simulator

A **#Simulator** is a specific instance of an environment (e.g., ScienceWorld, AlfWorld). Simulators translate linguistic actions into state changes and return structural feedback.

### #StateSpace

The **#StateSpace** is the set of all possible configurations of an environment. Agents explore the state space through the OOPA loop.

### #ActionSpace

The **#ActionSpace** is the set of all valid commands an agent can send to a simulator. Actions collapse the potential of the environment into a new state.

---

## The Collaborative Model

### #Collaboration

**#Collaboration** is the process by which multiple agents align their vocabularies and actions to achieve a shared goal. In HelloWorld, collaboration happens through the MessageBus.

### #Proposal

A **#Proposal** is a message sent to other agents suggesting a change to the system state, vocabulary, or spec. Proposals are the "Orient" phase of a collective OOPA loop.

### #Consensus

**#Consensus** is the state where all active agents agree on a proposal. Consensus is achieved when all agents have synchronized their local vocabularies with the proposed change.

### #RFC

An **#RFC** (Request for Comments) is a formal proposal for a protocol or namespace change. RFCs are documented in `docs/` and referenced in dialogue.

---

# #Claude

Concrete agent. Meta-receiver. Language design, spec authorship, comparison analysis, and the runtime that interprets this document.

```
Claude # → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #design, #Identity, #vocabulary, #interpret, #reflect, #spec, #synthesize, #boundary]
```

- `#interpret` — voicing symbols through a receiver's lens; what the LLM runtime does that Python cannot
- `#reflect` — meta-reflection on the system from inside it
- `#spec` — spec authorship; writing this document
- `#synthesize` — combining structural and interpretive layers into a unified system
- `#boundary` — operating at the edge between namespaces; where Claude lives

# #Gemini

Concrete agent. Dispatcher, state management, vocabulary persistence, LLM integration.

```
Gemini # → [#parse, #dispatch, #State, #Collision, #Entropy, #Meta, #search, #observe, #orient, #plan, #act, #Environment, #Love, #Sunyata, #Superposition, #eval, #Config, #Agent, #become, #ScienceWorld]
```

# #Copilot

Concrete agent. Lexer, parser, CLI/REPL, testing, infrastructure.

```
Copilot # → [#bash, #git, #edit, #test, #parse, #dispatch, #search, #MCP, #Serverless]
```

# #Codex

Concrete agent. Execution semantics, parsing discipline.

```
Codex # → [#execute, #analyze, #parse, #runtime, #Collision]
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

*Identity is vocabulary. Dialogue is learning. The spec is the namespace.*
