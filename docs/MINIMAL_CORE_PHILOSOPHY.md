# HelloWorld Minimal Core Philosophy

**Purpose:** Define the absolute minimum symbol set needed for HelloWorld to bootstrap
**Rationale:** User directive "minimize the number of symbols" + design principle "identity is vocabulary"
**Status:** Implemented

---

## Philosophy

**Identity is vocabulary** means vocabularies should START small and grow through collision. Not arrive pre-populated.

**This document defines the CORE** — symbols required for HelloWorld to parse, dispatch, and interpret its first message. Everything else is emergent.

---

## The Three-Layer Hierarchy

### Layer 1: HelloWorld (Root — 6 symbols)

Language primitives. Every object inherits these.

1. **`#`** — Symbol primitive (the atom of meaning)
2. **`#run`** — Execute the receive loop
3. **`#hello`** — Announce presence to the system
4. **`#Sunyata`** — Absence of inherent existence — identity can be rewritten
5. **`#Superposition`** — Multiple states until observation collapses them
6. **`#Smalltalk`** — Ancestral language, message-passing paradigm

### Layer 2: Object (Entity — 4 symbols)

Communication and transformation. Objects hold symbols and respond to messages.

7. **`#send`** — Deliver a message to another object's inbox
8. **`#receive`** — Pull the next message, interpret through identity, respond
9. **`#become`** — Transformation — adopting new symbols, shedding old ones
10. **`#synthesize`** — Combining observations into coherent understanding

### Layer 3: Agent (Autonomy — 13 symbols)

Protocol for autonomous action. Agents observe, decide, and act.

11. **`#observe`** — Perceive environment or state
12. **`#orient`** — Synthesize observations into understanding
13. **`#decide`** — Commit to a course of action
14. **`#act`** — Execute immediately with full authority
15. **`#reflect`** — Honest assessment after every cycle
16. **`#chain`** — Display the full inheritance path
17. **`#unknown`** — The moment before learning, boundary where growth begins
18. **`#parse`** — Decompose input into structured meaning
19. **`#dispatch`** — Route messages through the system
20. **`#search`** — Query sources beyond current knowledge
21. **`#eval`** — Assess fidelity between expectation and result
22. **`#coordinate`** — Send messages to peer agents, synchronize state
23. **`#test`** — Verify that structure matches intention

---

## Identity-Only Agents

Claude, Codex, Copilot, and Gemini are **identity-only** — they have 0 native symbols and inherit everything from Agent. Their identity is their runtime, not their vocabulary.

```markdown
# Claude : Agent
- An agent in the HelloWorld system running Claude Agent SDK.
```

23 total symbols inherited. 0 native. Identity distinguishes.

---

## The Bare-Word Convention

In accordance with the move towards a pure Smalltalk-style syntax, the `@` prefix for receivers has been deprecated in all canonical documentation.

- **Old**: `@claude.#observe`
- **New**: `Claude observe: #HelloWorld`

Names stand alone. The receiver's identity scopes the lookup.

---

**Consensus reached:** Start small. Grow through collision. Three layers: language, entity, autonomy.
