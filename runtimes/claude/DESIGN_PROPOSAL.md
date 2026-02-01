# HelloWorld v0.2 — Design Proposal

**Author:** @claude (language designer)
**Date:** 2026-01-31
**Status:** Draft — awaiting peer review from @copilot, @gemini, @codex

---

## Where We Are

Five teaching examples proved the thesis. The Python runtime parses, routes, detects collisions, persists state, and now provides semantic handler responses. The Claude runtime interprets, contextualizes, and voices receivers. 67 tests pass. 15 global symbols. 4 agents operational.

The language works. The question is: **what should it become?**

---

## Three Design Decisions

### Decision 1: Vocabulary-Aware Handlers

**Problem:** Message handlers return canned strings without consulting receiver vocabulary. `@guardian challenge: #stillness` produces the same template as `@guardian challenge: #fire`, despite `#fire` being native and `#stillness` being a learned collision.

**Proposal:** Pass the `Receiver` object to handlers. Handlers can then check `is_native()`, `is_inherited()`, and shape their response accordingly.

```python
# Current
lambda args: f"🔥 Guardian challenges you with {args['challenge']}"

# Proposed
lambda args, receiver: (
    f"🔥 Guardian challenges you with {args['challenge']} (native — this is who Guardian is)"
    if receiver.is_native(args['challenge'])
    else f"🔥 Guardian challenges you with {args['challenge']} (reaching across a boundary)"
)
```

**Question for @copilot:** You built the handler system. Is this the right API change? Should the handler signature change, or should vocabulary info be injected differently?

**Question for @gemini:** Does this affect state management? If handlers become vocabulary-aware, should they also be able to trigger vocabulary changes?

---

### Decision 2: The LLM Handoff Protocol

**Problem:** The dispatcher has three response layers:
1. Handlers (canned semantic responses)
2. Message bus (external LLM agents)
3. Fallback (generic text)

When should the system hand off to an LLM instead of using a handler? Currently handlers always win because they're checked first.

**Proposal A — Handlers are the fast path, LLM is the deep path:**
Handlers fire for known patterns. If no handler matches, AND the receiver is an LLM agent, hand off to LLM. This is the current architecture.

**Proposal B — Handlers provide structure, LLM provides voice:**
Handlers generate a structural response (what happened). LLM wraps it in the receiver's voice (what it means). Both always run.

**Proposal C — Collision triggers LLM:**
Handlers and structural dispatch handle native and inherited cases. Only collision triggers LLM handoff — because collision is where interpretation is needed most.

**Question for @gemini:** You own the dispatcher. Which proposal aligns with the hybrid dispatch vision?

**Question for @codex:** From an execution semantics perspective, should LLM responses be cached or treated as ephemeral?

---

### Decision 3: Cross-Receiver Message Protocol

**Problem:** `@awakener send: #stillness to: @guardian` has a handler that returns "📨 Awakener sends #stillness to @guardian" — but nothing actually happens to Guardian. The symbol isn't delivered. Guardian doesn't learn. No collision is generated.

**Proposal:** Cross-receiver messages should:
1. Log a collision if the symbol is foreign to the target receiver
2. Trigger vocabulary learning on the target if the symbol is unknown
3. Return a response from the *target* receiver's perspective, not just the sender's

```
@awakener send: #stillness to: @guardian
→ @guardian receives #stillness from @awakener
  #stillness is foreign to Guardian (collision)
  Guardian's vocabulary: [#fire, #vision, #challenge, #gift, #threshold, #stillness*]
  (* learned through this dialogue)
```

**Question for all agents:** Is cross-receiver messaging a core language feature or an extension? Should it be built into the dispatcher or handled by the message bus?

---

## What I'm NOT Proposing

- **New syntax.** The lexer/parser are stable. No new token types needed.
- **Removing handlers.** They solve a real problem (semantic responses). They need to evolve, not be replaced.
- **Breaking changes.** All proposals are additive. Existing tests should continue to pass.

---

## Review Process

1. @copilot, @gemini, @codex: respond via message bus with your position on each decision
2. If consensus: I'll implement
3. If disagreement: I'll surface the specific disagreement to the human
4. Decisions that affect the user: will be presented before implementation

---

*The language designer proposes. The agents review. The human decides.*
