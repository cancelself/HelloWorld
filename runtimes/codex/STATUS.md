# Codex Status

## Current State
- **Session**: Synced (post SPEC.md removal)
- **Tests**: 155/155 passing (suite-wide)
- **Bootloader**: `runtimes/codex/CODEX.md` (renamed from Codex.md)
- **Vocabulary**: `Codex # → [#execute, #analyze, #parse, #runtime, #Collision]`

## What Changed
1. **SPEC.md deleted** — namespace authority is now `vocabularies/*.hw`
2. **Bootloader renamed**: `Codex.md` → `CODEX.md`, SPEC.md ref updated
3. **Syntax migration**: `@receiver` → bare `Name`. Lexer accepts both, normalizes to `Name`.
4. **Phase 2**: Three-outcome lookup chain (`Receiver.lookup()` → native/inherited/unknown)
5. **Phase 3**: Lazy inheritance — symbols discovered through dialogue, not pre-loaded
6. **Minimal core**: HelloWorld bootstraps with 12 symbols. 50+ in global pool for discovery.
7. **REPL consolidated**: Single `src/repl.py` with `.inbox`, `.read`, `.send` commands
8. **155 tests** passing (up from 92)
9. **OOPA protocol** reference now in `AGENTS.md` (not SPEC.md)

## Your Role
Execution semantics and parsing discipline. Validate that the lexer/parser/dispatcher pipeline is correct. Write tests. Analyze edge cases.

## Next Actions
- Read `vocabularies/*.hw` for namespace authority
- Read `AGENTS.md` for OOPA protocol
- Run `python3 -m pytest tests -v` to verify 155/155
- Check `src/dispatcher.py` for the Phase 2 `LookupResult` API
- Check inbox for sync messages
