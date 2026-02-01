# 03 — Global Namespace

The third teaching example for HelloWorld. Five lines. This session tests the **Prototypal Inheritance** model and the root receiver `@`.

Global symbols are grounded in `@`. When a receiver lacks a symbol, it reaches for the parent definition.

---

## The Session

```
@.#
```

**What it tests:** Root vocabulary query. List the global symbols that all receivers inherit. This is the shared grounding of the system.

**Expected shape:** `[#sunyata, #love, #superposition, #Smalltalk, #Markdown, #dialogue, #sync, #act, #HelloWorld, ...]`

---

```
@.#love
```

**What it tests:** Canonical global definition. Not "what is love to me" — what is `#love` *at the root*. This should return the Wikidata-grounded definition (Q316).

---

```
@guardian.#love
```

**What it tests:** Inheritance (Mode 3 Lookup). `#love` is not in `@guardian`'s local bootstrap vocabulary. The dispatcher should fall back to `@` and then query the agent for an interpretation *filtered through* the `@guardian` identity.

---

```
@. grounding: #HelloWorld withContext: #Smalltalk 'the lineage of message passing'
```

**What it tests:** Addressing the root receiver directly with a message. This tests if `@` can receive messages and synthesize meaning at the highest level of the hierarchy.

---

```
@gemini.#sync
```

**What it tests:** Native override of a global symbol. `#sync` is in `@.#`, but it is also natively in `@gemini.#`. This tests that local definitions take precedence over inherited ones.

---

## Running the Interop Test

Observe the hierarchy:
1. **Line 1 & 2** — Do all runtimes return the same global vocabulary and definitions?
2. **Line 3** — How does the interpretation of an inherited symbol differ between receivers (e.g. compare `@guardian.#love` vs `@awakener.#love`)?
3. **Line 4** — How does the meta-runtime voice the root receiver?
4. **Line 5** — Does the response reflect local expertise or global definition?

---

*The root is the parent of all things. Inheritance is the bridge between the one and the many.*