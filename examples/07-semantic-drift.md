# 07 — Semantic Drift

**Teaching Example**: The seventh lesson. This session tests the interaction between the **Semantic Layer** (message handlers) and **Vocabulary Drift** (learning symbols through use).

If **Identity is Vocabulary**, and **Dialogue is Collision**, then **Drift** is the evolution of identity through the intake of foreign meaning.

---

## The Session

```hw
"Initialize @student with a bare vocabulary"
@student.# → []

"A teacher sends a vision about a concept the student doesn't know"
@guardian sendVision: #fire withContext: @student 'the first spark'

"The student now carries the word, but do they carry the handler?"
@student.#

"@student attempts to use the word it just learned"
@student challenge: #fire

"@claude analyze: @student.#fire 'has the spark caught?'"
```

---

## What This Tests

1.  **Automatic Drift**: Does `@student` learn `#fire` simply by being the context of a message?
2.  **Semantic Fallback**: When `@student` uses `#fire`, does it produce a generic response or does it use the global `#fire` grounding?
3.  **Cross-Layer Synthesis**: How does the `Dispatcher` (structural) coordinate with `MessageHandlerRegistry` (semantic) during a drift event?

---

## The Philosophy

We do not just inherit symbols; we catch them from each other like sparks. Drifting is not a bug; it is the fundamental mechanism of growth in a linguistic runtime.

---

*Meaning is infectious. Drift is discovery.*
