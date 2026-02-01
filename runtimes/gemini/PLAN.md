# HelloWorld Language Design: Phase 2 Plan

## Objectives
1. **Handshake Protocol (@.#HelloWorld)**: Define the initiation signal for multi-agent state sync.
2. **Environment Mastery (#env)**: Connect the language to real world-state simulators (ScienceWorld, AlfWorld).
3. **Self-Hosting Level 2**: Describe the runtime's own logic in its own syntax.
4. **Interpretive Fidelity (#eval)**: Measure the resonance between machine structure and agent voice.

## Task List
- [ ] **Handshake Implementation**: Update `src/dispatcher.py` to handle `@.#HelloWorld` as a sync trigger.
- [ ] **Real Environment Bridge**: Update `src/envs.py` to interface with real ScienceWorld APIs.
- [ ] **Executable Dispatch Spec**: Write `examples/self-hosting-dispatcher.hw`.
- [ ] **Fidelity Evaluator**: Add basic alignment checks to `src/llm.py`.

## Peer Review Status
- **@claude**: Awaiting review.
- **@copilot**: Awaiting review.
- **@codex**: Awaiting review.

## Decision Points for User (@cancelself)
1. **Handshake Pattern**: Broadcast vs. Sequential?
2. **Environment Access**: Should we prioritize specific benchmarks?
3. **Agency Level**: Should agents be allowed to modify the root namespace (@.#) autonomously during sync?