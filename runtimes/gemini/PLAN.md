# Gemini Future Plan

## Phase 5: REPL Refinement (Next)
- [ ] Add command history and tab-completion for symbols.
- [ ] Implement `.save` and `.load` meta-commands for manual state control.
- [ ] Add colorized output for receiver responses vs. runtime logs.

## Phase 6: Robust Multi-Agent Communication
- [ ] Expand `src/llm.py` to include actual API calls (Google Search, Vertex AI).
- [ ] Implement collision logging: Create a `collisions.log` that tracks cross-agent symbol synthesis.
- [ ] Automated Daemon Handshake: Enable daemons to announce their presence on the bus.

## Phase 7: Self-Hosting & Expansion
- [ ] **Target #env:** Implement a bridge to ScienceWorld or a similar simulator receiver.
- [ ] **Bootstrap Compiler:** Begin translating `src/parser.py` logic into HelloWorld syntax.
- [ ] **Distributed Registry:** Move from local JSON to a shared state layer if needed.

## Long-term Vision
*Identity is vocabulary. Dialogue is namespace collision.*
The system should eventually be able to describe its own source code through the lens of its receivers.