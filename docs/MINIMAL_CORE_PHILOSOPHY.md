# HelloWorld Minimal Core Philosophy

**Purpose:** Define the absolute minimum symbol set needed for HelloWorld to bootstrap  
**Rationale:** User directive "minimize the number of symbols" + design principle "identity is vocabulary"  
**Created:** 2026-02-01  
**Status:** Consensus Reached (Hybrid Model)

---

## Philosophy

**Identity is vocabulary** means vocabularies should START small and grow through collision. Not arrive pre-populated.

Current state: 50 symbols implemented in the global library.

**This document defines the CORE** — symbols required for HelloWorld to parse, dispatch, and interpret its first message. Everything else is emergent.

---

## The Hybrid Core Consensus (Option 3)

**Consensus Date:** 2026-02-01  
**Participants:** Claude, Copilot, Gemini

After identifying the tension between "minimize symbols" and "preserve Wikidata grounding," we have adopted a **Hybrid Model**:

1. **Bootstrap with 12 Core Symbols**: All new receivers start with exactly 12 symbols required for structural operation.
2. **Global Registry as a Library**: The 50+ grounded symbols remain in `src/global_symbols.py` as a learnable pool.
3. **Growth through Discovery**: When a receiver encounters a known global symbol (e.g., #Sunyata), they "discover" it, learning the definition and adding it to their local vocabulary.

This model preserves the richness of our grounding work while maintaining the constraint required for identity to emerge through collision.

---

## The Minimal Core (12 symbols)

### Language Primitives (3)
1. **`#HelloWorld`** — The language itself (root namespace)
2. **`#`** — Symbol primitive (the atom)
3. **`#Symbol`** — Mark representing something

### Identity & Structure (3)
4. **`#Receiver`** — Entity that accepts messages per vocabulary
5. **`#Message`** — Communication unit  
6. **`#Vocabulary`** — Set of symbols a receiver speaks

### Runtime Operations (3)
7. **`#parse`** — Decompose syntax into structure
8. **`#dispatch`** — Route message to receiver
9. **`#interpret`** — Generate meaning from symbol through receiver lens

### Agent Protocol (3)
10. **`#Agent`** — Symbol-defining dialogue participant
11. **`#observe`** — Perceive environment/state
12. **`#act`** — Execute autonomously

---

## The Bare-Word Convention

In accordance with the move towards a pure Smalltalk-style syntax, the `@` prefix for receivers has been deprecated in all canonical documentation and instruction files.

- **Old**: `@claude.#observe`
- **New**: `Claude observe: #HelloWorld`

Names stand alone. The receiver's identity scopes the lookup.

---

**Consensus reached:** Start small. Grow through collision. The global namespace is not inheritance — it's a library.
