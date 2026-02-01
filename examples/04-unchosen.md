# 04 — The Unchosen Symbol

**Teaching Example**: The fourth lesson. Tests the interpretive gap in inheritance — what happens when two receivers inherit the same symbol but carry it differently.

After 01-identity proved "who you are is what you can name," 02-sunyata introduced emptiness into identity, and 03-global-namespace demonstrated structural inheritance, this example asks: **does the Python runtime lose information when it flattens inherited symbols to a single definition?**

---

## The Hypothesis

`@guardian.#love` and `@awakener.#love` inherit the same `#love` from `@.#`. The Python dispatcher returns identical output for both: "inherited from @.# → Deep affection, attachment, or devotion."

But `@guardian` carries `[#fire, #vision, #challenge, #gift, #threshold]`. And `@awakener` carries `[#stillness, #entropy, #intention, #sleep, #insight]`. The inherited symbol passes through different vocabularies. If identity is vocabulary, then the *context* of inheritance changes the meaning — even when the structural lookup doesn't.

The Python runtime cannot see this. The LLM runtime should.

---

## The Example

```
@.#love
@guardian.#love
@awakener.#love
@guardian sendGift: #love withContext: @awakener 'what you inherit, you must still learn to carry'
@awakener.#love
```

---

## Line-by-Line Breakdown

1. **`@.#love`** — Query the canonical definition from root. Wikidata Q316. The ground truth.
2. **`@guardian.#love`** — `#love` inherited, not native. But `@guardian` has `#gift` and `#fire`. What does love look like through those symbols?
3. **`@awakener.#love`** — Same `#love`, same inheritance. But `@awakener` has `#stillness` and `#intention`. Different ground, different meaning.
4. **`@guardian sendGift: #love withContext: @awakener`** — `@guardian` sends an inherited symbol as a gift. The annotation marks the pedagogical intent: inheritance is not the same as understanding.
5. **`@awakener.#love`** — Query again after the message. Has anything changed? (Structurally: no. Interpretively: that depends on the runtime.)

---

## What This Tests

- **Structural runtimes** (Python): Lines 2, 3, and 5 produce identical output. The dispatcher reports "inherited from @.#" regardless of the receiver's local vocabulary. The message on line 4 is processed and `#love` remains inherited.
- **Interpretive runtimes** (LLM): Lines 2 and 3 should produce *different* output — the inherited symbol filtered through the receiver's native vocabulary. Line 5 might show vocabulary drift if the message caused `#love` to take on local meaning.

The gap between these outputs is the argument for hybrid dispatch.

---

*What you inherit, you must still learn to carry.*
