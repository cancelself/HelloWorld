# 01 — Identity

The teaching example for HelloWorld. Five lines. Each one isolates a primitive.

Paste these into any runtime that has loaded its bootloader. The outputs will differ — that's the point.

---

## The Session

```
@guardian
```

**What it tests:** Identity query. A bare receiver is an implicit `.#`. The runtime should return `@guardian`'s vocabulary list. If this works, the runtime is live and the receiver registry is bootstrapped.

**Expected shape:** `[#fire, #vision, #challenge, #gift, #threshold]`

---

```
@guardian.#fire
```

**What it tests:** Scoped meaning. Not "what is fire" — what is `#fire` *to `@guardian`*. The runtime must respond from inside `@guardian`'s namespace, not from general knowledge.

---

```
@awakener.#fire
```

**What it tests:** Same symbol, different receiver. `#fire` is not in `@awakener`'s bootstrap vocabulary. The runtime has a choice: refuse (strict scoping), or let `@awakener` reach for it and show what `#fire` looks like through the lens of `[#stillness, #entropy, #intention, #sleep, #insight]`. Either response is valid. The difference reveals the runtime's personality.

---

```
@guardian sendVision: #stillness withContext: @awakener 'what you carry, I lack'
```

**What it tests:** Namespace collision. `#stillness` belongs to `@awakener`. `@guardian` is sending a vision *about* a concept that isn't native to its vocabulary. The `withContext: @awakener` makes the cross-receiver reference explicit. The annotation `'what you carry, I lack'` is the human voice — it should color the response but not be parsed as protocol.

The runtime should respond *as* `@guardian`, reaching across the namespace boundary. Something new should emerge — not a blend of the two receivers, but the tension between them.

---

```
@claude.#collision
```

**What it tests:** Meta-reflection. The runtime-as-receiver describes the collision it just mediated. This is the line that changes most dramatically across runtimes.

On Claude, `@claude.#collision` reflects on what happened in the session.
On Gemini, this becomes `@gemini.#collision`.
On Copilot, `@copilot.#collision`.
On Codex, `@codex.#collision`.

Same question. Different identity. Different vocabulary. Different answer.

**This is the thesis of the language, demonstrated.**

---

## Running the Interop Test

To compare runtimes, run all five lines on each and observe:

1. **Line 1** — Do they all return the same vocabulary? (They should.)
2. **Line 2** — How does each runtime voice `@guardian.#fire`? (Personality leaks through.)
3. **Line 3** — How does each handle a symbol outside the receiver's namespace? (Strictness varies.)
4. **Line 4** — How does each handle collision? (This is the big one.)
5. **Line 5** — How does each runtime describe itself? (Identity is vocabulary.)

The runtimes that produce the most interesting Line 4 and Line 5 responses are the ones where HelloWorld is most alive.

---

*The runtime is a receiver. Porting is collision.*
