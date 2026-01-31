# Copilot Task List

## Phase 1: Core Language Infrastructure ✓

- [x] Initialize project structure
- [x] Implement lexer
- [x] Write lexer tests
- [x] Create example programs
- [x] Document runtime architecture
- [x] Establish agent coordination

## Phase 2: Parser & AST (Next)

- [ ] Design AST node types
  - MessageNode (receiver, keywords, arguments)
  - ReceiverNode (@name)
  - SymbolNode (#name)
  - VocabularyQueryNode (@name.#)
  - ScopedLookupNode (@name.#symbol)
- [ ] Implement recursive descent parser
- [ ] Handle keyword message chains
- [ ] Parse annotations and literals
- [ ] Write parser tests
- [ ] Add malformed input tests

## Phase 3: Dispatcher

- [ ] Create receiver registry
- [ ] Implement message dispatcher
- [ ] Map @copilot to tool calls
- [ ] Map @github to MCP server calls
- [ ] Handle unknown receivers
- [ ] Implement vocabulary query resolution

## Phase 4: State Management

- [ ] Design .vocab file format
- [ ] Implement vocabulary persistence
- [ ] Create receiver namespace isolation
- [ ] Build vocabulary evolution tracking
- [ ] Add state serialization/deserialization

## Phase 5: REPL

- [ ] Build interactive prompt
- [ ] Implement session history
- [ ] Add command completion
- [ ] Create help system (@copilot.#)
- [ ] Write REPL tests

## Phase 6: Multi-Agent Communication

- [ ] Define message bus protocol
- [ ] Implement file-based message passing
- [ ] Create namespace collision detection
- [ ] Build vocabulary sync mechanism
- [ ] Test cross-agent dialogue

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
