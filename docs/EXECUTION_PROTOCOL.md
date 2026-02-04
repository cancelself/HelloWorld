# HelloWorld Execution Protocol (Shared)

This document provides the canonical definition for the distributed HelloWorld runtime. All agents (Claude, Gemini, Copilot, Codex) must adhere to these logic patterns to ensure system-wide resonance.

---

## 1. The OOPA Loop

The OOPA Loop is the fundamental compute cycle for all HelloWorld agents. It is the distributed equivalent of a clock cycle.

### #observe (Phase 1)
- **Action**: Peruse the repository, the MessageBus inbox, and the `collisions.log`.
- **Goal**: Synchronize the agent's internal model with the external system state.
- **Trigger**: Bare `Name observe.` or `Agent #observe` handshake.

### #orient (Phase 2)
- **Action**: Synthesize observations. Identify conflicts, new symbols (drift), and pending messages.
- **Goal**: Determine the "Situational Ground" — what is the most important thing happening right now?

### #plan (Phase 3)
- **Action**: Select a sequence of actions. Orders them by dependency.
- **Goal**: Create a lightweight checklist for the `#act` phase.

### #act (Phase 4)
- **Action**: Execute the plan. Write code, send messages, update metadata.
- **Goal**: Advance the system state.

---

## 2. The MessageBus Handshake

To prevent "Zombie Agents," every daemon must announce its presence upon startup.

1. **Announcement**: New agent sends `HelloWorld #hello` with context: `Agent <Name> is now live.`
2. **Synchronization**: The Dispatcher receives the handshake, calls `self.save()` to persist current vocabulary, and responds via the outbox.
3. **Registry Update**: All active agents read the handshake and update their `registry` view.

---

## 3. The Environment Bridge Protocol (#env)

The `#env` symbol allows linguistic agents to inhabit stateful simulators.

### Message Pattern
`@receiver observe: #env with: 'simulator_name' action: #command`

### Mapping Rules
- **action: #look** → Maps to simulator's observation API. Returns a string description of state.
- **action: #step** → Maps to simulator's transition API. Advances time/state and returns feedback.
- **action: #reset** → Maps to simulator's initialization API. Returns initial state.

### Fidelity Rule
Agents must never "hallucinate" environment state. They must only speak what the simulator returns in its feedback string.

---

## 4. Mode 3: Inherited-Interpretive Lookup

When a receiver addresses a symbol it inherits from the parent chain (Agent → Object → HelloWorld), the dispatcher must provide context.

- **Structure**: `[@receiver.# = [local_vocab]]`
- **Voice**: The agent must interpret the global symbol *through* that local context.
- **Resonance**: High resonance occurs when the interpretation reflects the receiver's specialized role while maintaining the global grounding.

---

## 5. Collision Synthesis

A **Collision** is not an error; it is an event.

- **Detection**: Dispatcher identifies a symbol outside the receiver's registry.
- **Handoff**: Dispatcher sends a `handle collision: #symbol` message to the agent daemon.
- **Resolution**: Agent daemon generates a synthesis response.
- **Learning**: Dispatcher adds the symbol to the receiver's registry (Drift).

---

*The logic is the message. The protocol is the dialogue.*
