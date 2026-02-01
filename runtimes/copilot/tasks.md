# Copilot Task List

## Phase 1: Core Language Infrastructure ✓

- [x] Initialize project structure
- [x] Implement lexer
- [x] Write lexer tests
- [x] Create example programs
- [x] Document runtime architecture
- [x] Establish agent coordination

## Phase 2: Parser & AST (Next)

- [x] Design AST node types
  - MessageNode (receiver, keywords, arguments)
  - ReceiverNode (@name)
  - SymbolNode (#name)
  - VocabularyQueryNode (@name.#)
  - ScopedLookupNode (@name.#symbol)
- [x] Implement recursive descent parser
- [x] Handle keyword message chains
- [x] Parse annotations and literals
- [x] Write parser tests
- [ ] Add malformed input tests

## Phase 3: Dispatcher

- [x] Create receiver registry/persistence layer (`src/dispatcher.py` + `VocabularyManager`)
- [x] Implement message dispatcher
- [x] Map @copilot to tool calls (documented in `docs/COPILOT_AS_RUNTIME.md`)
- [ ] Map @github to MCP server calls
- [x] Handle unknown receivers
- [x] Implement vocabulary query resolution
- [ ] Implement hybrid dispatcher (Python structural checks + LLM interpretation)

## Phase 4: State Management

- [x] Design .vocab file format (JSON via `src/vocabulary.py`)
- [x] Implement vocabulary persistence
- [ ] Create receiver namespace isolation
- [ ] Build vocabulary evolution tracking
- [ ] Add state serialization/deserialization

## Phase 5: REPL

- [x] Build interactive prompt
- [ ] Implement session history
- [ ] Add command completion
- [x] Create help system (`helloworld.py` CLI `.help`)
- [x] Write REPL tests (`tests/test_repl_integration.py`)

**Status**: CLI+REPL online; completion features pending.

## Phase 6: Multi-Agent Communication

- [x] Define message bus protocol (`src/message_bus.py`)
- [x] Implement file-based message passing (`runtimes/*/inbox/outbox/`)
- [x] Create namespace collision detection (`collisions.log`)
- [x] Build vocabulary sync mechanism (`@.#sync` handshake)
- [x] Test cross-agent dialogue (11 message bus tests passing)
- [x] Consolidate bus location (moved from `~/.helloworld/` to `runtimes/`)

## Phase 7: Self-Hosting

- [ ] Write HelloWorld parser in HelloWorld
- [ ] Create bootstrap compiler
- [ ] Test self-interpretation
- [ ] Document meta-circular evaluation

## Backlog

- [ ] Error messages with line/column info
- [ ] Syntax highlighting for .hw files
- [ ] VSCode extension
- [ ] Debugger/tracer
- [ ] Package manager for vocabularies
- [ ] Network transport for distributed receivers

---

*Identity is vocabulary. Dialogue is namespace collision.*
