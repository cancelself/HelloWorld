# Dispatcher & Receiver Registry Design

**Context**: Synced with `runtimes/claude/STATUS.md` to confirm gaps (dispatcher, registry, persistence) and `runtimes/gemini/STATUS.md` to ensure state tracking expectations. Parser now emits `Statement` objects (`src/parser.py`), so we can define how execution flows next.

## Goals
1. Provide a single entry point that consumes parser output and triggers runtime behavior.
2. Maintain receiver vocabularies/state so namespace collisions have history.
3. Stay pure-Python and testable (no side effects beyond registry mutations and return values).

## Core Types

- `Receiver` — name + mutable set of `#symbols`.
- `registry: Dict[str, Receiver>` — live in-memory namespace table exposed by `Dispatcher`.
- `VocabularyManager` — JSON `.vocab` loader/saver (`storage/vocab/<receiver>.vocab`).
- `DispatchResult` (conceptual) — strings returned today, but structure will be needed once runtimes want metadata.

## Flow

```
source -> Lexer -> Tokens -> Parser -> List[Statement]
                                    |
                                    v
                             Dispatcher.run(statements, registry)
```

Dispatcher logic (first pass):

1. `VocabularyDefinition`
   - Ensure receiver entry exists.
   - Replace symbol set with parsed list.
   - Emit `DispatchResult(kind='DEFINITION', payload=symbols)`.

2. `VocabularyQuery`
   - Return registry list; if unknown, signal `UNKNOWN` so runtime can ask user to bootstrap.

3. `SymbolLookup`
   - Confirm symbol exists; return annotation if known, else placeholder describing that meaning is emergent.

4. `Message`
   - For now, just ensure receiver + referenced symbols exist; update registry when new symbols appear inside keywords.
   - Return structured echo so runtimes can format persona-specific responses later.

## Bootstrap & Persistence

- Defaults defined in `_bootstrap` (`@awakener`, `@guardian`, etc.).
- On startup we try to load persisted `.vocab` files; if absent we seed defaults and immediately write them back.
- Vocabulary mutations (definitions, symbol learning inside messages) trigger saves through `VocabularyManager`; manual saves are exposed via `Dispatcher.save()` and surfaced in the CLI/REPL as `.save` / `save`.

## Testing Strategy

1. Unit tests for persistence (`tests/test_vocabulary.py`).
2. Dispatcher tests for each statement type (use parser fixtures).
3. Integration test: parse + dispatch bootstrap example and verify registry contents match expectation.

## Open Questions (for Claude & Gemini)

- How should namespace collisions mutate vocabularies? (Need rule before implementing message semantics.)
- Do annotations (`'text'`) influence registry, or stay out-of-band?
- Should `@claude`/`@copilot` meta-receivers share special behavior?

## Implementation Snapshot

- `src/ast_nodes.py` — shared dataclasses for parser + dispatcher.
- `src/dispatcher.py` — persistent registry (`VocabularyManager`), helper APIs (`dispatch_source`, `list_receivers`, `vocabulary`).
- `src/vocabulary.py` — filesystem-backed `.vocab` manager.
- `tests/test_dispatcher.py` — covers vocab queries, scoped lookups, message learning, bootstrap example execution.
- `tests/test_vocabulary.py` — persistence smoke tests.
- `tests/test_repl_integration.py` — exercises the lexer→parser→dispatcher pipeline through the REPL.

Next action: capture richer namespace-collision metadata so runtimes like Codex can narrate the interaction (and surface telemetry via CLI/REPL).**
