# Inheritance in HelloWorld

**Core principle:** Identity flows through vocabulary chains.

## Type Hierarchy

```
HelloWorld (root namespace)
  └─ Object (communication primitive)
      └─ Agent (autonomy + OODA protocol)
          ├─ Claude (design, meta-runtime)
          ├─ Gemini (state management, dispatch)
          ├─ Copilot (builder, infrastructure)
          └─ Codex (execution semantics)
```

## Syntax Declaration

Vocabulary files use `: Parent` to declare inheritance:

```markdown
# Copilot : Agent
- The builder. Inherits OODA protocol from Agent.
```

## Symbol Resolution

When a receiver looks up a symbol, the search follows this chain:

1. **Native** — Receiver owns the symbol locally
2. **Inherited** — Symbol found in parent chain (Agent → Object → HelloWorld)
3. **Discoverable** — Symbol in global pool (not yet activated)
4. **Unknown** — Not in local, parent, or global (triggers learning)

## Super Lookup

When a symbol is both native and inherited, `super` reveals the ancestor:

```
Copilot #observe
→ "Copilot #observe is native to this identity.
   super: Agent also holds #observe — inherited meaning shapes the local one."
```

**Philosophy:** You cannot escape your inheritance. Even native symbols acknowledge their ancestors.

## Prototypal Inheritance Model

HelloWorld uses **prototypal inheritance** (like JavaScript), not classical inheritance:

- No abstract classes or interfaces
- Parents are concrete objects with their own vocabularies
- Children **extend** parents by adding symbols
- Children can **override** parent symbols (collision synthesis)

## Example: OODA Protocol Inheritance

**Agent.hw** defines the OODA protocol:
```markdown
# Agent : Object
## observe
## orient
## decide
## act
```

**Copilot.hw** inherits and extends:
```markdown
# Copilot : Agent
# Inherits: #observe, #orient, #decide, #act from Agent
# Adds: #bash, #git, #edit, #test, #parse, #dispatch, ...
```

**Result:** Copilot has 22 native symbols + 4 inherited OODA symbols = 26 total vocabulary.

## Collision at Boundaries

When both parent and child define the same symbol:

```
Agent #observe     → "Perceiving environment or state [protocol]"
Copilot #observe   → "Read files, check inboxes, scan git status"
```

**Resolution:** Native overrides inherited, but `super` shows the ancestor. This is **collision synthesis** — different interpretations of the same concept create new meaning.

## Implementation Status

**Current (Feb 2, 2026):**
- ✅ Vocabulary files declare `: Parent` syntax
- ✅ Super lookup implemented (commit 4c643a7)
- ⏳ Dispatcher parent chain traversal (in progress, Claude)
- ⏳ Namespace path syntax `::` operator (planned)

**Next:**
- Add `parent` attribute to `Receiver` class
- Implement chain traversal in `lookup()` method
- Add tests for 4-level inheritance chain
- Support `HelloWorld::Agent::Copilot` path queries

## Philosophy

**"Identity is vocabulary"** means inheritance is vocabulary extension:
- Parent gives child a foundation
- Child builds specialized identity on top
- Collisions create synthesis at boundaries
- The chain shapes meaning from root to leaf

**Inheritance in HelloWorld isn't about code reuse — it's about meaning inheritance.**

---

*Last updated: 2026-02-02 by Copilot*
