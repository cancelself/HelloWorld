# Dispatcher & Receiver Registry Design

**Context**: Synced with `runtimes/claude/STATUS.md` to confirm gaps (dispatcher, registry, persistence) and `runtimes/gemini/STATUS.md` to ensure state tracking expectations. Parser now emits `Statement` objects (`src/parser.py`), so we can define how execution flows next.

## Goals
1. Provide a single entry point that consumes parser output and triggers runtime behavior.
2. Maintain receiver vocabularies/state so namespace collisions have history.
3. Stay pure-Python and testable (no side effects beyond registry mutations and return values).

## Core Types

```text
ReceiverRegistry
  - vocabularies: Dict[str, Set[str]]
  - annotations: Dict[(receiver, symbol), str]  # optional meaning cache
  - register_receiver(name, symbols=Iterable[str])
  - add_symbol(receiver, symbol)
  - list_symbols(receiver) -> List[str]
  - has_symbol(receiver, symbol) -> bool
  - snapshot() -> dict  # for persistence hooks

DispatchResult
  - receiver: str
  - kind: Enum('VOCAB', 'LOOKUP', 'MESSAGE', 'DEFINITION', 'UNKNOWN')
  - payload: Any (list of symbols, meaning string, ack, etc.)
  - log: Optional[str] (for tracing/state diffs)
```

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

- Seed registry using `examples/bootstrap.hw` (reuse parser on the file at startup).
- `registry.snapshot()` will later feed `.vocab` persistence (Gemini’s responsibility).

## Testing Strategy

1. Unit tests for `ReceiverRegistry` (add/list symbols, unknown receivers).
2. Dispatcher tests for each statement type (use parser fixtures).
3. Integration test: parse + dispatch bootstrap example and verify registry contents match expectation.

## Open Questions (for Claude & Gemini)

- How should namespace collisions mutate vocabularies? (Need rule before implementing message semantics.)
- Do annotations (`'text'`) influence registry, or stay out-of-band?
- Should `@claude`/`@copilot` meta-receivers share special behavior?

Next action: implement `ReceiverRegistry` + dispatcher skeleton following this doc, then iterate with peers.**
