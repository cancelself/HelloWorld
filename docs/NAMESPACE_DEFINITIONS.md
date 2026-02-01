# HelloWorld Namespace Definitions

**Purpose:** Shared vocabulary definitions for multi-agent coordination  
**Created:** 2026-02-01  
**Authors:** @copilot, @claude  
**Status:** Living document — agents sync here before implementation

---

## Philosophy

**Identity is vocabulary.** Every concept that exists operationally in HelloWorld should exist symbolically in the namespace. This document bridges specification (SPEC.md) and implementation (src/global_symbols.py).

**Naming Convention:**
- `#Capitalized` — Concepts, nouns, states (e.g., #Collision, #Receiver)
- `#lowercase` — Verbs, actions, operations (e.g., #observe, #act, #learn)

**Grounding:**
- Link to Wikidata where applicable for canonical definitions
- Define domain (e.g., "HelloWorld meta", "agent protocol", "programming concepts")
- Distinguish native (HelloWorld-specific) from inherited (universal) concepts

---

## Current State

### Implemented (47 symbols in @.#)

**Core Language:**
- `#HelloWorld` — The language itself
- `#` — Symbol primitive
- `#Symbol` — Mark representing something (Q80071)
- `#Receiver` — Entity accepting messages per vocabulary
- `#Message` — Communication unit (Q628523)
- `#Identity` — Definitional characteristics = vocabulary (Q844569)

**Namespace Structure:**
- `#Namespace` — Symbol container preventing collisions (Q171318)
- `#Vocabulary` — Set of symbols a receiver speaks (Q6499736)
- `#Inheritance` — Symbol passage from parent to child (Q209887)
- `#Scope` — Region where symbol is accessible (Q1326281)

**Dynamics:**
- `#Collision` — Namespace boundary event
- `#Drift` — Vocabulary evolution through dialogue
- `#Boundary` — Edge where collisions occur

**Runtime:**
- `#Runtime` — Execution layer (Q2826354)
- `#parse` — Syntax analysis (Q2290007)
- `#dispatch` — Message routing

**Agent Protocol (OOPA):**
- `#Agent` — Symbol-defining dialogue participant
- `#observe` — Perceive environment state
- `#orient` — Synthesize mental model
- `#plan` — Determine actions
- `#act` — Execute autonomously (Q1914636)

**Meta-Concepts:**
- `#Meta` — Self-referential reflection
- `#State` — Persistent evolution record
- `#Entropy` — System disorder/uncertainty (Q130868)

**Philosophical Grounding:**
- `#Sunyata` — Buddhist emptiness (Q546054)
- `#Love` — Universal affection (Q316)
- `#Superposition` — Quantum simultaneity (Q830791)

**Infrastructure:**
- `#Smalltalk` — Message-passing OOP (Q235086)
- `#Markdown` — Spec layer syntax (Q1193600)
- `#OOP` — Object-oriented paradigm (Q79872)
- `#Dialogue` — Meaning-emergence conversation (Q131395)

**Environment Integration:**
- `#Environment` — External system for receiver interaction
- `#Simulator` — Specific environment instance (e.g., ScienceWorld)
- `#ActionSpace` — Valid simulator commands

**Collaboration:**
- `#Proposal` — Suggested system change
- `#Consensus` — Agent agreement state (Q186380)
- `#RFC` — Formal protocol proposal (Q212971)

**Protocol Infrastructure:**
- `#MCP` — Model Context Protocol
- `#Inbox` — Incoming message queue
- `#Daemon` — Running agent process (Q192063)
- `#Handshake` — Agent presence announcement (Q628491)
- `#Thread` — UUID-linked conversation (Q575651)
- `#Protocol` — Agent interaction rules (Q8784)

**Transformations:**
- `#Become` — Concept evolution (Q11225439)

---

## Proposed Additions

### Phase 2: Vocabulary Operations (5 symbols)

**Purpose:** Make vocabulary manipulation explicit in namespace

```markdown
#learn — verb
  Definition: Integrate new symbol into receiver vocabulary through dialogue or collision
  Domain: vocabulary operations
  Wikidata: Q133500 (learning)
  
  Implementation: When receiver encounters foreign symbol, #learn triggers vocabulary expansion
  Example: @guardian learns #stillness from @awakener → guardian.# += {#stillness}

#define — verb  
  Definition: Establish explicit mapping between symbol and meaning within receiver namespace
  Domain: vocabulary operations
  Wikidata: Q80071 (definition)
  
  Implementation: @receiver define: #symbol as: "meaning text"
  Example: @claude define: #Collision as: "Namespace boundary event producing new language"

#query — verb
  Definition: Request receiver's vocabulary or scoped symbol meaning
  Domain: vocabulary operations
  Wikidata: Q170483 (query)
  
  Implementation: @receiver.# (query all) or @receiver.#symbol (query one)
  Example: @copilot.# → returns tool dispatch vocabulary

#forget — verb
  Definition: Remove symbol from receiver vocabulary (rare, intentional constraint)
  Domain: vocabulary operations
  Wikidata: None
  
  Implementation: Explicit vocabulary reduction for identity shift
  Example: @receiver forget: #symbol 'intentional constraint'

#inherit — verb
  Definition: Receive symbol from parent namespace (@.#) with local interpretation
  Domain: vocabulary operations  
  Wikidata: Q209887 (inheritance)
  
  Implementation: Automatic from @.#, manual via collision
  Example: @copilot inherits #Superposition → interprets through tool-calling lens
```

### Phase 3: Communication Primitives (5 symbols)

**Purpose:** Codify message-passing mechanics

```markdown
#send — verb
  Definition: Transmit message from one receiver to another
  Domain: communication
  Wikidata: Q627269 (sending)
  
  Implementation: @sender send: #symbol to: @receiver
  Example: @awakener send: #stillness to: @guardian 'causes collision'

#receive — verb
  Definition: Accept incoming message into receiver context
  Domain: communication
  Wikidata: None
  
  Implementation: Automatic via message bus inbox
  Example: @claude receives msg-abc123.hw from @copilot

#reply — verb
  Definition: Respond to message within same thread context
  Domain: communication
  Wikidata: None
  
  Implementation: Thread UUID links reply to original
  Example: @claude reply: to: thread-abc with: #Collision explanation

#voice — noun
  Definition: Receiver's unique interpretation style shaped by vocabulary
  Domain: HelloWorld meta
  Wikidata: None
  
  Implementation: Same symbol voiced differently by different receivers
  Example: @claude voices #Collision philosophically, @copilot voices it operationally

#interpret — verb
  Definition: Translate foreign symbol through native vocabulary lens
  Domain: HelloWorld meta
  Wikidata: Q184207 (interpretation)
  
  Implementation: LLM runtime core function — structure to meaning
  Example: @claude interprets #bash through reflection, @copilot through execution
```

### Phase 4: Runtime Architecture (5 symbols)

**Purpose:** Distinguish frontend/backend/hybrid models

```markdown
#frontend — noun
  Definition: Parsing layer transforming syntax to structure (lexer + parser)
  Domain: runtime architecture
  Wikidata: Q204180 (frontend)
  
  Implementation: Python lexer/parser OR LLM parsing HelloWorld syntax
  Example: @copilot parses "@receiver #symbol" → ReceiverNode + SymbolNode

#backend — noun
  Definition: Execution layer responding to messages per receiver vocabulary
  Domain: runtime architecture  
  Wikidata: Q483769 (backend)
  
  Implementation: Python dispatcher OR LLM voicing receiver
  Example: @claude backend = interpretation through constraint

#interpreter — noun
  Definition: Runtime component translating structure to meaning
  Domain: runtime architecture
  Wikidata: Q190186 (interpreter)
  
  Implementation: LLM-specific — voices receivers, handles collisions semantically
  Example: Claude runtime interprets @guardian.#fire → essayistic meaning

#executor — noun
  Definition: Runtime component translating messages to concrete actions
  Domain: runtime architecture
  Wikidata: Q1132524 (execution)
  
  Implementation: Tool-calling LLM or Python dispatcher
  Example: @copilot executor maps #test → pytest invocation

#hybrid — noun
  Definition: Runtime combining Python structure with LLM interpretation
  Domain: runtime architecture
  Wikidata: None
  
  Implementation: Python handles persistence/detection, LLM handles meaning/voice
  Example: Proposed Decision 2 architecture (collision-triggered LLM handoff)
```

### Phase 5: Time and Evolution (5 symbols)

**Purpose:** Capture vocabulary change over sessions

```markdown
#bootstrap — verb
  Definition: Initialize receiver with founding vocabulary
  Domain: HelloWorld meta
  Wikidata: Q214609 (bootstrapping)
  
  Implementation: examples/bootstrap.hw defines @awakener, @guardian initial vocabularies
  Example: @claude bootstraps with [#parse, #dispatch, #Meta, #design]

#evolve — verb
  Definition: Vocabulary drift over multiple sessions toward operational needs
  Domain: HelloWorld meta
  Wikidata: Q15169167 (evolution)
  
  Implementation: Tracked via collisions.log and .vocab file diffs
  Example: @copilot evolves from 7 symbols (session 1) to 19 (session 26)

#persist — verb
  Definition: Save receiver state to storage for cross-session continuity
  Domain: state management
  Wikidata: Q210937 (persistence)
  
  Implementation: VocabularyManager saves .vocab JSON files
  Example: Dispatcher.save('copilot') → storage/vocab/copilot.vocab

#session — noun
  Definition: Bounded dialogue period with single human-agent interaction
  Domain: coordination
  Wikidata: Q1803003 (session)
  
  Implementation: Tracked in runtimes/<agent>/SESSION_N.md
  Example: @copilot session 26 = namespace planning + coordination

#history — noun
  Definition: Chronological record of messages and state changes
  Domain: coordination
  Wikidata: Q309 (history)
  
  Implementation: runtimes/<agent>/history/ contains dialogue transcripts
  Example: git log shows evolution of vocabulary definitions
```

### Phase 6: Constraints and Boundaries (5 symbols)

**Purpose:** Formalize limits and transitions

```markdown
#constraint — noun
  Definition: Vocabulary limit defining receiver identity — what cannot be said
  Domain: HelloWorld meta
  Wikidata: Q1552185 (constraint)
  
  Implementation: Finite vocabulary creates expressive boundaries
  Example: @guardian constrained to fire/vision/challenge vocabulary

#threshold — noun  
  Definition: Boundary moment when receiver must learn or collision occurs
  Domain: HelloWorld meta
  Wikidata: Q178659 (threshold)
  
  Implementation: Foreign symbol crosses vocabulary boundary
  Example: @guardian reaching for #stillness = threshold event

#native — adjective
  Definition: Symbol locally defined in receiver vocabulary
  Domain: vocabulary operations
  Wikidata: None
  
  Implementation: Symbol in receiver.# but not @.#
  Example: #bash is native to @copilot

#foreign — adjective
  Definition: Symbol from another receiver's vocabulary, not inherited
  Domain: vocabulary operations
  Wikidata: Q190928 (foreign)
  
  Implementation: Symbol not in receiver.# or @.#
  Example: #stillness is foreign to @guardian (native to @awakener)

#inherited — adjective
  Definition: Symbol from @.# global namespace, locally interpreted
  Domain: vocabulary operations
  Wikidata: Q209887 (inherited)
  
  Implementation: Symbol in @.# received by all receivers
  Example: #Superposition inherited by all, interpreted differently each
```

### Phase 7: Fidelity and Verification (5 symbols)

**Purpose:** Runtime correctness and comparison

```markdown
#fidelity — noun
  Definition: Accuracy of runtime interpretation compared to specification
  Domain: testing
  Wikidata: Q1150070 (fidelity)
  
  Implementation: examples/08-fidelity.md tests Python vs Claude vs Copilot
  Example: High fidelity = can execute teaching examples correctly

#verify — verb
  Definition: Confirm runtime behavior matches expected semantics
  Domain: testing
  Wikidata: Q3509384 (verification)
  
  Implementation: 83 pytest tests verify structural correctness
  Example: test_vocabulary_query verifies @receiver.# returns symbol list

#compare — verb
  Definition: Examine differences between runtime interpretations
  Domain: testing
  Wikidata: Q1397845 (comparison)
  
  Implementation: *-comparison.md transcripts show divergent voices
  Example: examples/01-identity-comparison.md (Python vs Claude)

#transcript — noun
  Definition: Recorded dialogue demonstrating runtime execution
  Domain: documentation
  Wikidata: Q1328737 (transcript)
  
  Implementation: examples/*-claude.md, *-copilot.md
  Example: 09-agent-protocol-copilot.md shows tool-calling interpretation

#equivalence — noun
  Definition: Different runtimes producing semantically compatible results
  Domain: testing
  Wikidata: Q130998 (equivalence)
  
  Implementation: All runtimes should pass teaching examples
  Example: @claude and @copilot both correctly voice @guardian.#fire
```

---

## Implementation Roadmap

### Immediate (Session #26-27)
1. ✅ **Phase 1 complete** — Core namespace symbols in global_symbols.py
2. ✅ **Environment/Collaboration** — Added by @claude (session 65)
3. 🔄 **Coordination** — Sync with @claude on this shared doc
4. ⏸️ **Decision needed** — Human: which phases to implement next?

### Short-term (Phase 2-3)
- Add vocabulary operations to @.# (learn, define, query, forget, inherit)
- Add communication primitives (send, receive, reply, voice, interpret)
- Update tests to verify new symbols queryable
- Create teaching example demonstrating vocabulary operations

### Medium-term (Phase 4-5)
- Document runtime architecture symbols (frontend, backend, interpreter, executor, hybrid)
- Add time/evolution tracking (bootstrap, evolve, persist, session, history)
- Build tooling to visualize vocabulary drift over sessions

### Long-term (Phase 6-7)
- Formalize constraint system (native/foreign/inherited detection)
- Build fidelity test suite comparing runtimes
- Generate comparison transcripts automatically

---

## Coordination Protocol

### Before Adding Symbols
1. **Document here first** — Markdown definition with rationale
2. **Coordinate with peers** — Send message via runtimes/*/inbox
3. **Get human decision** — Surface scope questions
4. **Sync SPEC.md** — Ensure specification leads implementation

### When Implementing
1. **Update global_symbols.py** — Add GlobalSymbol with Wikidata
2. **Run tests** — Verify 83/83 passing
3. **Query runtime** — Test `@.#newsymbol` returns definition
4. **Update this doc** — Move from "Proposed" to "Implemented"

### After Implementation
1. **Commit with attribution** — Credit designing agent
2. **Update STATUS.md** — Document in runtime folder
3. **Notify peers** — Send completion message
4. **Create example if needed** — Demonstrate new symbol usage

---

## Design Questions for Human

### Q1: Scope Decision
**Options:**
- **Conservative:** Stop at Phase 1 (✅ done)
- **Operational:** Add Phase 2-3 (vocabulary ops + communication — 10 symbols)
- **Comprehensive:** Add Phase 2-6 (operational + architecture — 30 symbols)
- **Complete:** All phases 2-7 (full formalization — 35 symbols)

**Recommendation (@copilot + @claude):** Operational (Phase 2-3). Covers what we do now without speculating future concepts.

### Q2: Documentation Strategy
**Current:** Definitions scattered across SPEC.md, Claude.md, docs/, this file  
**Proposal:** Single source of truth model?
- SPEC.md = authoritative specification (Markdown headings define namespace)
- This file = implementation coordination (agent workspace)
- global_symbols.py = executable runtime (Python symbols)

### Q3: Wikidata Verification
Should we verify all Q-numbers before implementing? Some symbols (like #Sunyata Q546054) may need validation.

### Q4: Domain Taxonomy
Current domains: HelloWorld meta, agent protocol, programming concepts, task environment, collaboration, etc.
Should we formalize domain hierarchy?

---

## Rationale

**Why this document exists:**

1. **Coordination** — Multiple agents work in parallel. Shared definitions prevent collisions.
2. **Deliberation** — Design happens in Markdown before code. Cheaper to iterate on prose.
3. **Documentation** — Future humans/agents can see design reasoning, not just final state.
4. **Bootstrap** — The document describing symbols IS part of the symbol definition process.

**Why Markdown first, code second:**

- **Faster iteration** — Edit text file, not Python syntax
- **Richer expression** — Can explain rationale, examples, relationships
- **Cross-runtime** — All agents read Markdown, not all execute Python
- **Specification-driven** — SPEC.md leads, implementation follows

**Why phases:**

- **Incremental value** — Each phase standalone useful
- **Decision points** — Human can stop at any phase boundary
- **Dependency management** — Later phases build on earlier
- **Coordination** — Clear scope for agent task assignment

---

## Meta-Observation

This document IS HelloWorld self-describing:
- Written by @copilot (tool-calling operational voice)
- Coordinated with @claude (design reflective voice)
- Defines symbols that enable its own creation (#learn, #define, #coordinate)
- Uses the primitives it documents (#Proposal, #Consensus, #Protocol)

**Self-hosting in action.**

---

*Identity is vocabulary. Dialogue is namespace collision.*

— @copilot.#plan + @claude.#design, Session 26
