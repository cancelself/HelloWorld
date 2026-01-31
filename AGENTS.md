# Repository Guidelines

## Project Structure & Module Organization
Core language primitives live in `src/`, with `src/lexer.py` exposing the tokenization rules that Claude uses as its runtime vocabulary. `README.md` carries the quickstart narrative, while `Claude.md` documents parsing, dispatch, and vocabulary constraints. Example transcripts belong in `examples/`; contributor notes or RFC drafts go in `docs/`. Tests sit in `tests/`, mirroring file names (e.g., `tests/test_lexer.py` for `src/lexer.py`). Keep assets text-based so transcripts stay diffable.

## Build, Test, and Development Commands
- `python3 -m pytest tests` — run the full regression suite; preferred before any push.
- `python3 -m pytest tests/test_lexer.py -k token` — scope to a focused scenario when iterating on a rule.
- `python3 -m compileall src` — optional static syntax check to catch stray syntax errors.
Run commands from the repository root; `sys.path` already points at `src/`, so no packaging step is required.

## Coding Style & Naming Conventions
Follow idiomatic Python (PEP 8) with 4-space indents, lowercase_with_underscores for helpers, and CapWords for classes and Enums (`TokenType`). Keep modules deterministic: no singletons, no hidden state, and only standard-library dependencies. Favor descriptive token names that mirror HelloWorld vocabulary (`RECEIVER`, `SYMBOL`). New helpers should live beside the runtime modules and carry docstrings that explain their impact on dialogue flow.

## Testing Guidelines
Tests use bare `pytest` assertions. Name files `test_<module>.py` and write case names that describe the language rule they guard (`test_vocabulary_query`). Each new token, receiver behavior, or parsing rule must have: a happy-path sample, a malformed sample, and assertions on token metadata (type, value, position) when relevant. Prefer short literals so failures can be pasted straight into Claude for debugging.

## Commit & Pull Request Guidelines
Recent history uses short, imperative summaries (“Initial HelloWorld implementation with lexer and tests”). Continue that voice: ≤50 characters in the subject, optional wrapped body for rationale. PRs should state purpose, link the driving issue or spec section (`Claude.md` reference), paste the exact test command + result, and attach only the screenshots needed for UX-visible changes. Highlight vocabulary or protocol shifts up top so downstream agents can sync before review.

## Security & Configuration Tips
Never commit secrets or raw conversations that include private prompts. Sanitize language samples and trim large artifacts before pushing. Prototype new receivers on temporary branches so experimental vocabularies do not enter the mainline accidentally.
