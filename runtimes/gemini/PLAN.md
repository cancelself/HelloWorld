# Gemini Agent Plan

## 1. Project Synchronization (Completed)
- [x] Standardized `runtimes/` directory structure.
- [x] Renamed `runtimes/codex/AGENTS.md` to `Codex.md`.
- [x] Moved `CODEX.md` to `runtimes/codex/BOOTLOADER.md`.
- [x] Updated `Claude.md` (root) to reflect structure changes.

## 2. Validation: Teaching Example
**Goal:** Verify the language design by simulating the execution of `examples/01-identity.md` as the Gemini runtime.

- [ ] Read `examples/01-identity.md`.
- [ ] Simulate execution based on `runtimes/gemini/gemini-system-instruction.md`.
- [ ] Record the output (especially the namespace collision behavior) to `runtimes/gemini/validation_output.md`.

## 3. Implementation: Parser
**Goal:** Build the actual Python parser to convert tokens into an Abstract Syntax Tree (AST).

- [ ] Create `src/parser.py`.
- [ ] Define AST nodes (Message, Receiver, Symbol, etc.).
- [ ] Implement recursive descent parsing for:
    - Receiver lookup (`@name`)
    - Vocabulary query (`@name.#`)
    - Keyword messages (`@name action: #symbol`)
- [ ] Create `tests/test_parser.py` and verify against `examples/bootstrap.hw`.

## 4. Coordination
- [ ] Update `runtimes/gemini/STATUS.md` with progress.
- [ ] Check `runtimes/copilot/status.md` for potential collaboration on the Dispatcher.
