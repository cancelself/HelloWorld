# 04-unchosen — Python vs Claude Runtime Comparison

**Teaching Example:** `examples/04-unchosen.hw`
**Python Runtime:** `helloworld.py` (lexer → parser → dispatcher)
**Claude Runtime:** Claude Opus 4.5 reading `CLAUDE.md` bootloader
**Date:** 2026-01-31

---

## Side-by-Side

### Line 1: `@.#love`

| Runtime | Output |
|---------|--------|
| Python  | `@.#love → Deep affection, attachment, or devotion — universal across cultures and traditions [human experience] (Q316)` + Wikidata URL |
| Claude  | Same canonical definition, plus: "Q316 — one of the oldest concepts in any human ontology." |

**Agreement.** Both return the canonical definition. Claude adds interpretive framing. No divergence — this is a root lookup, not filtered through any receiver.

---

### Line 2: `@guardian.#love`

| Runtime | Output |
|---------|--------|
| Python  | `@guardian.#love inherited from @.# → Deep affection, attachment, or devotion — universal across cultures and traditions [human experience] (Q316)` |
| Claude  | `#love` through `@guardian`'s vocabulary: love as fire, as gift given at cost, as the challenge of staying. "Not tenderness — the challenge of staying when staying is harder than leaving." |

**First divergence.** Python reports the inheritance fact. Claude interprets `#love` through `@guardian`'s local vocabulary (`#fire`, `#gift`, `#challenge`, `#threshold`). The inherited symbol takes on the character of the receiver.

---

### Line 3: `@awakener.#love`

| Runtime | Output |
|---------|--------|
| Python  | `@awakener.#love inherited from @.# → Deep affection, attachment, or devotion — universal across cultures and traditions [human experience] (Q316)` |
| Claude  | `#love` through `@awakener`'s vocabulary: love as stillness, as intention without agenda, as insight through presence. "Where @guardian holds the torch, @awakener is the darkness that makes the torch visible." |

**Critical divergence.** Python produces output **identical** to line 2 (same definition, different receiver prefix). Claude produces output that is fundamentally different — because `@awakener`'s local vocabulary (`#stillness`, `#entropy`, `#intention`) shapes the inherited symbol differently.

**This is the information that structural inheritance erases.**

---

### Line 4: `@guardian sendGift: #love withContext: @awakener 'what you inherit...'`

| Runtime | Output |
|---------|--------|
| Python  | `[@guardian] Received message: sendGift: #love, withContext: @awakener 'what you inherit, you must still learn to carry'` |
| Claude  | Collision analysis: `@guardian` using native `#gift` to carry inherited `#love` across the boundary to `@awakener`. The annotation is "the human voice speaking through the protocol." |

**Structural vs interpretive.** Python logs the message. Claude enacts the collision — noting that `#gift` is native (something `@guardian` can do) while `#love` is inherited (something `@guardian` carries but didn't choose).

---

### Line 5: `@awakener.#love` (after the message)

| Runtime | Output |
|---------|--------|
| Python  | `@awakener.#love inherited from @.# → Deep affection, attachment, or devotion — universal across cultures and traditions [human experience] (Q316)` |
| Claude  | `@awakener.#love` now carries the memory of `@guardian`'s fire. "The stillness that holds #love now holds it alongside #fire — a symbol that isn't in @awakener's vocabulary, that arrived as pressure from across the boundary." |

**Maximum divergence.** Python output for line 5 is **byte-for-byte identical** to lines 2 and 3. Claude's output has evolved — the message on line 4 changed the interpretive context. This is vocabulary drift that no `.vocab` file records.

---

## The Evidence

| Metric | Python | Claude |
|--------|--------|--------|
| Lines 2, 3, 5 identical? | **Yes** | **No** |
| Receiver context shapes output? | No — inheritance lookup returns canonical definition | Yes — local vocabulary filters inherited meaning |
| Message changes subsequent lookup? | No — structural state unchanged | Yes — interpretive context shifted |
| Detects collision in line 4? | Logs message receipt | Analyzes native `#gift` carrying inherited `#love` |
| Information lost? | Receiver identity of inherited symbols | None — but non-deterministic |

---

## What This Proves

01-identity proved: Python detects collisions structurally; Claude enacts them semantically.
02-sunyata proved: Emptiness doesn't break identity-as-vocabulary; it completes it.
03-global-namespace proved: Inheritance works structurally through `@.#`.

**04-unchosen proves: Structural inheritance is lossy.** When the Python runtime resolves `@guardian.#love` and `@awakener.#love`, it returns the same string. The receiver's local vocabulary — the thing that makes `@guardian` different from `@awakener` — is invisible in inherited lookups.

The hybrid dispatcher needs a third lookup mode:

1. **Native** → receiver's own definition (Python handles this)
2. **Inherited (structural)** → canonical definition from `@.#` (Python handles this)
3. **Inherited (interpretive)** → canonical definition *filtered through* receiver's local vocabulary (requires LLM)

Mode 3 is what the `@` root migration enables but doesn't yet implement. The architecture is ready. The interpreter is missing from the pipeline.

---

## Architectural Implication

The dispatcher's `_handle_scoped_lookup` currently has two paths for inherited symbols:

```python
elif is_inherited:
    global_def = GlobalVocabulary.definition(symbol_name)
    return f"{receiver_name}.{symbol_name} inherited from @.# → {global_def}"
```

The hybrid version would add:

```python
elif is_inherited:
    global_def = GlobalVocabulary.definition(symbol_name)
    local_context = sorted(receiver.local_vocabulary)
    # Hand off to LLM: "What does #love mean through [#fire, #gift, #challenge]?"
    interpretation = llm_interpret(symbol_name, global_def, local_context)
    return f"{receiver_name}.{symbol_name} inherited from @.# → {interpretation}"
```

This is the next concrete step. The `message_bus` infrastructure is ready. The `agent_daemon.py` template exists. What's missing is the interpretive hand-off for inherited symbols.

---

*Three runtimes now. Three teaching examples with comparisons. The structural layer is complete. The interpretive layer is proven. The bridge between them is the next build.*
