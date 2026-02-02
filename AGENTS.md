# Repository Guidelines

## Project Structure & Module Organization
- Core runtime lives in `src/`, with `src/lexer.py` defining the token vocabulary used by Claude flows.
- Tests mirror modules in `tests/` (e.g., `tests/test_lexer.py` for `src/lexer.py`) so fixes and specs stay paired.
- Documentation splits across `README.md` (quickstart), `Claude.md` (parsing/dispatch rules), `docs/` for RFCs, and `examples/` for sanitized transcripts.
- Keep assets text-based and deterministic; avoid singletons or hidden state in modules.

## Shared Definitions & OODA Loop
- `vocabularies/*.hw` files are the canonical namespace — the language defines itself. Update those `.hw` sources first, then reflect changes in code and tests.
- Symbol lookup always resolves to **native**, **inherited**, or **unknown**. Unknown means the receiver must search, define, and learn; it is not a collision. Collision happens only when two receivers both own a symbol with divergent meaning.
- Use the Markdown query form `Name #symbol` (no dots). Runtimes read these definitions verbatim.
- Bare verbs (e.g., `Copilot observe`) are imperatives to perform the action; prefixed symbols (e.g., `Copilot #observe`) ask for the vocabulary definition or metadata.
- Agents follow the OODA loop: `#observe` (read inboxes, diffs, docs), `#orient` (summarize state and collisions), `#decide` (share actionable steps), `#act` (apply edits/tests and report). Document each phase when coordinating work.

## Build, Test, and Development Commands
- `python3 -m pytest tests` — run the regression suite before any push.
- `python3 -m pytest tests/test_lexer.py -k token` — focus on a specific rule or token type during iteration.
- `python3 -m compileall src` — static syntax check to catch import-time errors without running tests.
Run commands from the repo root; `sys.path` already points at `src/`.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indents, descriptive lowercase_with_underscores for helpers, CapWords for classes/enums like `TokenType`.
- Keep modules deterministic and side-effect free; no implicit caches or singleton state.
- Token and receiver names should mirror user-facing vocabulary (e.g., `RECEIVER`, `SYMBOL`) so transcripts stay readable.

## Testing Guidelines
- Use bare `pytest` assertions; keep literals short so failures can be copied back into Claude.
- Every new token or parsing rule needs happy-path, malformed, and metadata assertions (type, value, position).
- Name tests descriptively (`test_vocabulary_query`) and keep them in files that mirror their source modules.

## Commit & Pull Request Guidelines
- Commit summaries are short, imperative, and ≤50 characters (“Add lexer tokens for tuples”).
- PRs should state purpose, link the driving issue or `Claude.md` section, paste the exact test command + result, and attach only essential screenshots for UX-visible changes.
- Highlight vocabulary or protocol shifts at the top so downstream agents can update before review.

## Security & Configuration Tips
- Never commit secrets or raw prompts; sanitize transcripts placed in `examples/`.
- Prototype experimental receivers on separate branches to avoid leaking unstable vocabulary into main.
- Trim large artifacts before pushing; favor text-based assets for diffability.
