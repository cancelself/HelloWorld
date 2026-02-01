# Teaching Example 09: The Agent Protocol

The agent protocol is two symbols: `#observe` and `#act`. Every agent inherits both from `@.#`. Observation precedes action. Action without observation is noise.

This example tests the protocol through the dispatcher — not through an LLM, not through a daemon, but through the handler system that routes messages.

## The Program

```helloworld
@guardian observe: #fire
@guardian observe: #stillness
@guardian act: #fire
@guardian act: #stillness
@claude observe: #Collision
@claude act: #dispatch
@claude act: #fire
```

## What To Look For

**Lines 1-2:** Guardian observes a native symbol (#fire) and a foreign symbol (#stillness). The responses should differ — native vs boundary collision.

**Lines 3-4:** Guardian acts on native vs foreign. Acting on #fire is authoritative. Acting on #stillness is acting at the boundary — the collision should be felt.

**Lines 5-6:** Claude observes and acts on its own symbols. #Collision is native. #dispatch is native.

**Line 7:** Claude acts on #fire — which is foreign to Claude but native to Guardian. This is the agent protocol's version of namespace collision: one agent acting on another agent's symbol.

## The Thesis

The agent protocol formalizes what the teaching examples discovered:
- **01-identity:** Identity is vocabulary. `observe:` reveals it.
- **04-unchosen:** The same inherited symbol means different things to different receivers. `act:` makes that visible.
- **SPEC.md:** `#Agent #observe` and `#Agent #act` are the protocol. This example makes them executable.
