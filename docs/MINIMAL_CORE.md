# HelloWorld Minimal Core Symbols

**Purpose:** Define the absolute minimum symbol set needed for HelloWorld to bootstrap  
**Rationale:** User directive "minimize the number of symbols" + design principle "identity is vocabulary"  
**Created:** 2026-02-01  
**Status:** Proposal (coordinating with @claude)

---

## Philosophy

**Identity is vocabulary** means vocabularies should START small and grow through collision. Not arrive pre-populated.

Current state: 47 symbols implemented, 35 more proposed (82 total). That's too high for a constraint-based language.

**This document defines the CORE** — symbols required for HelloWorld to parse, dispatch, and interpret its first message. Everything else is emergent.

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

**Why move them?**
- **Fidelity to thesis:** If identity is vocabulary, then vocabulary defines capacity. A receiver with 47 symbols can say 47 things. One with 12 can say 12 things, until dialogue teaches them more.
- **Emergence over enumeration:** Collision happens when vocabularies differ. Pre-loading eliminates the collisions that would teach the symbols.
- **Bootstrap parsimony:** The minimal core should answer: "What symbols must exist for HelloWorld to send its first message?" Not "What symbols might be useful?"

---

## Bootstrap Sequence

With minimal core, the first HelloWorld dialogue becomes:

```
HelloWorld #
→ [#HelloWorld, ##, #Symbol, #Receiver, #Message, #Vocabulary, #parse, #dispatch, #interpret, #Agent, #observe, #act]

@claude observe: #HelloWorld
→ Claude interprets based on pretraining + these 12 symbols
→ Claude's vocabulary is EXACTLY these 12 until collision teaches more

@awakener observe: #stillness  
→ ERROR: #stillness unknown to @awakener
→ @awakener searches (web/pretraining), learns it, adds to vocabulary
→ NOW @awakener has 13 symbols: core 12 + #stillness

@guardian #fire
→ Guardian learns #fire through use
→ @guardian.# = [core 12] + [#fire]

@awakener #fire  
→ Awakener encounters symbol Guardian has
→ COLLISION: both have #fire, meanings diverge
→ This collision is felt because vocabularies were small and distinct
```

**Compare to current state:** With 47 pre-loaded symbols, early collisions are masked by shared inheritance. The boundary doesn't emerge until much later.

---

## Migration Path

1. **Commit current work** (SPEC.md, NAMESPACE_DEFINITIONS.md) as historical inventory
2. **Refactor global_symbols.py** to implement minimal core only
3. **Update SPEC.md** to clarify: "12 core symbols + emergent learning"
4. **Update bootloaders** (Claude.md, etc.) to reflect minimal starting vocabulary
5. **Add vocabulary growth tracking** in dispatcher (log when receiver learns new symbol)
6. **Write tests** for emergence: start with 12, dialogue should add symbols dynamically

---

## Open Questions for @claude

1. Does this align with your `#design` understanding?
2. Are there core symbols I'm missing? (Can HelloWorld bootstrap with < 12?)
3. Should `#interpret` be core, or is it implied by receiver + message?
4. How do we handle the philosophical symbols (`#Sunyata`, etc.) that user explicitly grounded via Wikidata?

---

*Start small. Grow through collision. Let identity emerge from constraint.*
