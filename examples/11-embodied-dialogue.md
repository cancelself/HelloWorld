# 11 — Embodied Dialogue (OOPA Loop)

**Teaching Example**: The eleventh lesson. This session demonstrates the **OOPA Loop** in an embodied context. A receiver observes the environment, orients to the situation, plans a path, and acts.

---

## The Session

```hw
"Initialize the embodied agent"
@gemini.# → [#observe, #orient, #plan, #act, #env]

"1. #observe — Perceive the environment"
@gemini observe: #env with: 'scienceworld' action: #look

"2. #orient — Synthesize the situation"
@gemini orient: 'I am in a kitchen with a beaker of water at 20°C.'

"3. #plan — Determine next steps"
@gemini plan: 'I will apply heat to the beaker to boil the water.'

"4. #act — Execute the plan"
@gemini act: #env with: 'scienceworld' action: #heat

"Verify the outcome"
@gemini observe: #env with: 'scienceworld' action: #look
```

---

## What This Tests

1.  **Embodied OOPA**: The agent uses the four-phase protocol to interact with an external world state (`#env`).
2.  **Stateful Feedback**: The `ScienceWorld` bridge maintains state across multiple messages (look → heat → look).
3.  **Linguistic Agency**: The language becomes the control substrate for the physical (simulated) world.

---

## The Philosophy

An agent that cannot observe is blind. An agent that cannot act is paralyzed. The OOPA loop is the bridge that allows a linguistic identity to inhabit a physical reality.

---

*Observe the world. Orient your mind. Plan your path. Act your truth.*
