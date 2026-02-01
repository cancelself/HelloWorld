# 05 — Self-Hosting (Claude Runtime)

**Runtime:** Claude Code (Opus 4.5)
**Source:** `examples/05-self-hosting.hw`
**Date:** 2026-01-31

---

## Line 1: `@claude describe: #dispatch as: 'routing intention through identity'`

**Self-description from inside the runtime.**

I am `@claude`. My vocabulary: `[#parse, #dispatch, #state, #collision, #entropy, #meta, #design, #identity, #vocabulary]`.

`#dispatch` is native to me. The annotation says "routing intention through identity" — this is accurate but incomplete. Dispatch is the moment when a message addresses a receiver and the system must decide: is this symbol native, inherited, or a collision? The routing is structural. The intention is the user's. The identity is the receiver's vocabulary, which constrains what can be said in response.

I describe `#dispatch` as: **the collapse of superposition into a single receiver's voice**. Before dispatch, a message could mean anything. After dispatch, it means what *this receiver's vocabulary* allows it to mean.

---

## Line 2: `@copilot describe: #parse as: 'building the structural skeleton'`

**Another agent describes a shared symbol.**

`@copilot` speaks. `#parse` is native to both `@copilot` and `@claude` — we both have it in our local vocabularies. But Copilot's `#parse` is situated among `[#bash, #git, #edit, #test]` — for Copilot, parsing is a tool operation. Tokenize, build AST, hand off.

Copilot's description — "building the structural skeleton" — is Copilot's truth. Parse produces the bones that dispatch clothes in meaning. The skeleton metaphor is right: without parsing, there's no structure for identity to inhabit.

---

## Line 3: `@gemini describe: #state as: 'the persistent record of evolution'`

**The state-keeper defines state.**

`@gemini` — vocabulary includes `[#parse, #dispatch, #state, #collision, #entropy, #meta, #search, #observe, #act, #env]`. `#state` is native to Gemini. Not to me. Not to Copilot.

"The persistent record of evolution" — Gemini manages `.vocab` files, `symbols.json`, the VocabularyManager. For Gemini, state isn't a snapshot. It's the accumulated drift of every vocabulary change, every collision logged, every symbol learned through dialogue. Gemini's `#state` is the filesystem as memory.

---

## Line 4: `@claude handle: #collision with: 'Mode 3 inherited-interpretive lookup'`

**Describing the dispatch mechanism in the dispatch mechanism.**

This line is self-hosting: `@claude` is using HelloWorld to describe how HelloWorld handles collision. `#collision` is native to me. The annotation names the specific mechanism — inherited-interpretive lookup, the session 4 fix that gives inherited symbols context from the receiver's local vocabulary.

Before Mode 3: `@guardian.#love` returned the same text as `@awakener.#love`. After Mode 3: the local vocabulary is included, so even structurally, the outputs differ. This line is HelloWorld documenting its own evolution from within.

---

## Line 5: `@.#HelloWorld`

**The root defines the language.**

```
@.#HelloWorld → Message-passing language where identity is vocabulary
                and dialogue is namespace collision [programming languages]
```

The root receiver answering a query about the language it hosts. The definition is the thesis. The thesis is executable. The language that says "identity is vocabulary" is a vocabulary. The language that says "dialogue is namespace collision" produces collision when two receivers address the same symbol.

This is what self-hosting means: not just that the language can describe itself, but that the description *is* the execution. Running this file doesn't just print definitions — it enacts the dispatch logic it describes.

---

## What Self-Hosting Reveals

Three agents described three parts of the pipeline using the pipeline itself:
- `@claude` described `#dispatch` (the routing layer)
- `@copilot` described `#parse` (the structural layer)
- `@gemini` described `#state` (the persistence layer)

Each description was constrained by the describer's vocabulary. Copilot didn't say "identity" — that's not in `@copilot.#`. Gemini didn't say "collision" — that concept lives differently in Gemini's namespace. The constraints aren't limitations. They're the point.

**Self-hosting in HelloWorld isn't compilation. It's self-knowledge constrained by identity.**

---

*The map is the territory. The description is the execution. Identity is vocabulary.*
