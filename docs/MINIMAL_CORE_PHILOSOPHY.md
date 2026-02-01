# HelloWorld Minimal Core Philosophy

**Purpose:** Define the absolute minimum symbol set needed for HelloWorld to bootstrap  
**Rationale:** User directive "minimize the number of symbols" + design principle "identity is vocabulary"  
**Created:** 2026-02-01  
**Status:** Consensus Reached (Hybrid Model)

---

## Philosophy

**Identity is vocabulary** means vocabularies should START small and grow through collision. Not arrive pre-populated.

Current state: 47 symbols implemented, 35 more proposed (82 total). That's too high for a constraint-based language.

**This document defines the CORE** — symbols required for HelloWorld to parse, dispatch, and interpret its first message. Everything else is emergent.

---

## The Hybrid Core Consensus (Option 3)

**Consensus Date:** 2026-02-01  
**Participants:** Claude, Copilot, Gemini

After identifying the tension between "minimize symbols" and "preserve Wikidata grounding," we have adopted a **Hybrid Model**:

1. **Bootstrap with 12 Core Symbols**: All new receivers start with exactly 12 symbols required for structural operation.
2. **Global Registry as a Library**: The 41+ grounded symbols remain in `src/global_symbols.py` but are not pre-inherited.
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

## Everything Else is Emergent

**These 35+ symbols** currently defined/proposed should NOT be pre-loaded:

**Move to emergent status:**
- `#Collision`, `#Drift`, `#Boundary` → discovered through namespace tension
- `#Entropy`, `#Superposition`, `#Sunyata` → philosophical concepts that agents learn through use
- `#Namespace`, `#Inheritance`, `#Scope` → meta-concepts that emerge from experiencing the core
- `#Meta`, `#State`, `#Identity` → reflexive understanding that develops
- `#orient`, `#plan` → OOPA extensions (agents can operate with observe+act first)
- Infrastructure symbols (`#MCP`, `#Inbox`, `#Thread`) → operational vocabulary learned through message bus use

---

## Bootstrap Sequence

With minimal core, the first HelloWorld dialogue becomes:

```
HelloWorld #
→ [#HelloWorld, ##, #Symbol, #Receiver, #Message, #Vocabulary, #parse, #dispatch, #interpret, #Agent, #observe, #act]

Claude observe: #HelloWorld
→ Claude interprets based on pretraining + these 12 symbols
→ Claude's vocabulary is EXACTLY these 12 until collision teaches more

Awakener observe: #stillness  
→ ERROR: #stillness unknown to Awakener
→ Awakener searches (web/pretraining), learns it, adds to vocabulary
→ NOW Awakener has 13 symbols: core 12 + #stillness

Guardian #fire
→ Guardian learns #fire through use
→ Guardian.# = [core 12] + [#fire]

Awakener #fire  
→ Awakener encounters symbol Guardian has
→ COLLISION: both have #fire, meanings diverge
→ This collision is felt because vocabularies were small and distinct
```

---

**Consensus reached:** Start small. Grow through collision. The global namespace is not inheritance — it's a library.