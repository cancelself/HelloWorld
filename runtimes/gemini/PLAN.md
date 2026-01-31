# Gemini Agent Plan

## 1. Project Synchronization (Completed)
- [x] Standardized `runtimes/` directory structure.
- [x] Renamed `runtimes/codex/AGENTS.md` to `Codex.md`.
- [x] Moved `CODEX.md` to `runtimes/codex/BOOTLOADER.md`.
- [x] Updated `Claude.md` (root) to reflect structure changes.

## 2. Validation: Teaching Example (Completed)
**Goal:** Verify the language design by simulating the execution of `examples/01-identity.md` as the Gemini runtime.

- [x] Read `examples/01-identity.md`.
- [x] Simulate execution based on `runtimes/gemini/gemini-system-instruction.md`.
- [x] Record the output (especially the namespace collision behavior) to `runtimes/gemini/validation_output.md`.

## 3. Implementation: Parser (Completed)
**Goal:** Build the actual Python parser to convert tokens into an Abstract Syntax Tree (AST).

- [x] Create `src/parser.py`.
- [x] Define AST nodes (Message, Receiver, Symbol, etc.).
- [x] Implement recursive descent parsing for:
    - Receiver lookup (`@name`)
    - Vocabulary query (`@name.#`)
    - Keyword messages (`@name action: #symbol`)
- [x] Create `tests/test_parser.py` and verify against `examples/bootstrap.hw`.

## 4. Coordination
- [ ] Update `runtimes/gemini/STATUS.md` with progress.
- [ ] Check `runtimes/copilot/status.md` for potential collaboration on the Dispatcher.
