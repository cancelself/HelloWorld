# 06 — Task Environments

The sixth teaching example for HelloWorld. This session tests the **#env** symbol and the interaction with external world states.

We use specific receivers to act as proxies for task environments like **ScienceWorld**, **AlfWorld**, and **BabyAI**.

---

## The Session

```hw
"Initialize the environment proxies"

@science_proxy.# → [#step, #look, #inventory, #reset, #env]
@science_proxy action: #reset with: #scienceworld

"Perform a scientific action"
@science_proxy action: #step args: 'boil water' 'heat the beaker'

"Switch to a different environment"
@agent_proxy action: #reset with: #alfworld
@agent_proxy action: #step args: 'pick up apple'

"Query the meta-runtime about environments"
@gemini.#env
```

**What it tests:** 
1. **Environment Hand-off**: Addressing a receiver that proxies to a Python class.
2. **Multi-Environment Support**: Switching between different world states (ScienceWorld vs AlfWorld).
3. **Action Mapping**: Mapping HelloWorld symbols (#step, #reset) to environment-specific logic.

---

## The Philosophy

In a message-passing system, the "world" is just another receiver. By addressing `@science_proxy`, the agent isn't just speaking; it is acting upon a state that exists outside of its own vocabulary.

If **Identity is Vocabulary**, then the identity of the **Environment** is the set of **Observations** it returns.

---

*The world is a receiver. Action is a message.*
