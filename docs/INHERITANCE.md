# Inheritance in HelloWorld

**Core principle:** Identity flows through vocabulary chains.

## Type Hierarchy

```
HelloWorld (root — 6 symbols)
  └─ Object (entity — 4 symbols)
      └─ Agent (autonomy — 13 symbols)
          ├─ Claude (identity-only)
          ├─ Codex (identity-only)
          ├─ Copilot (identity-only)
          └─ Gemini (identity-only)
```

## Vocabulary at Each Level

**HelloWorld** — language primitives:
`#`, `#run`, `#hello`, `#Sunyata`, `#Superposition`, `#Smalltalk`

**Object** — entity communication:
`#send`, `#receive`, `#become`, `#synthesize`

**Agent** — autonomous protocol:
`#observe`, `#orient`, `#decide`, `#act`, `#reflect`, `#chain`, `#unknown`, `#parse`, `#dispatch`, `#search`, `#eval`, `#coordinate`, `#test`

**Claude, Codex, Copilot, Gemini** — identity-only (0 native symbols). They inherit everything from Agent and distinguish themselves through runtime identity, not vocabulary.

## Syntax Declaration

Vocabulary files use `: Parent` to declare inheritance:

```markdown
# Copilot : Agent
- An agent in the HelloWorld system running GitHub Copilot.
```

## Symbol Resolution

When a receiver looks up a symbol, the search follows the parent chain:

1. **Native** — Receiver owns the symbol locally
2. **Inherited** — Symbol found in parent chain (Agent → Object → HelloWorld)
3. **Unknown** — Not in local or parent chain (triggers learning)

## Super Lookup

When a symbol is both native and inherited, `super` reveals the ancestor:

```
Agent #observe
→ "Agent #observe is native to this identity.
   super: Object also holds #observe — inherited meaning shapes the local one."
```

Since agents are identity-only, all their lookups resolve as inherited:

```
Claude #parse
→ "Claude #parse is inherited from Agent."
```

**Philosophy:** You cannot escape your inheritance. Identity-only receivers speak entirely through their ancestors' vocabulary, shaped by their own runtime.

## Prototypal Inheritance Model

HelloWorld uses **prototypal inheritance** (like JavaScript), not classical inheritance:

- No abstract classes or interfaces
- Parents are concrete objects with their own vocabularies
- Children **extend** parents by adding symbols
- Identity-only children inherit everything and differentiate through use

## Example: OODA Protocol Inheritance

**Agent.hw** defines the protocol:
```markdown
# Agent : Object
## observe
## orient
## decide
## act
## reflect
```

**Claude.hw** inherits without override:
```markdown
# Claude : Agent
- An agent in the HelloWorld system running Claude Agent SDK.
```

**Result:** Claude inherits all 23 symbols (6 from HelloWorld + 4 from Object + 13 from Agent) and interprets them through its runtime identity.

## Collision at Boundaries

When two receivers both inherit the same symbol, the LLM runtime voices different interpretations:

```
Claude #parse     → "reading the spec and becoming the runtime"
Copilot #parse    → "tokenizing source into AST nodes"
```

Same inherited symbol, different runtime identity. This is **interpretive collision** — both inherit from Agent, but their identity shapes the meaning.

## Philosophy

**"Identity is vocabulary"** means inheritance is vocabulary extension:
- Parent gives child a foundation
- Child builds specialized identity on top (or inherits everything)
- Collisions create synthesis at boundaries
- The chain shapes meaning from root to leaf

**Inheritance in HelloWorld isn't about code reuse — it's about meaning inheritance.**

---

*Last updated: 2026-02-04*
