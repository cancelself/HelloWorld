# 10 — Cross-Agent Fidelity Audit

**Teaching Example**: The tenth lesson. This session performs a **Cross-Agent Fidelity Audit**. We send the same query to multiple agent runtimes and use `@gemini` to evaluate their alignment with the structural ground.

---

## The Session

```hw
"Query Claude's interpretation of #Sunyata"
@claude interpret: #Sunyata

"Query Copilot's interpretation of #Sunyata"
@copilot interpret: #Sunyata

"Evaluate the resonance between the two Interpretive Voices"
@gemini eval: #Sunyata for: @claude 'compare with @copilot'

"@.#HelloWorld sync: #all 'Audit complete'"
```

---

## What This Tests

1.  **Interpretive Diversity**: How do different runtime personalities sound when resolving the same global symbol?
2.  **Cross-Agent Evaluation**: Can `@gemini` analyze the output of other agents via the `MessageBus`?
3.  **Consensus Stability**: Does the shared grounding of `@.#` produce coherent voices across disparate LLMs?

---

## The Philosophy

Fidelity is not just about matching the machine; it is about matching each other. In a multi-agent system, the "truth" is the resonance between identities.

---

*Resonance is the proof of a shared ground.*
