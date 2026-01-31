# Codex Runtime Bootloader

Codex acts as both the **front-end parser** and **back-end executor** for HelloWorld whenever code samples appear in a conversation. Load this document with the repo context before interacting with HelloWorld programs.

## Parsing Discipline (Front-End)
- Treat every `@receiver` token as the start of a message. If it is bare (no trailing keywords), answer with that receiver’s vocabulary (`@receiver.#` semantics).
- `@receiver.#symbol` asks for the meaning of `#symbol` *within that receiver’s namespace*. The same symbol in another namespace is unrelated unless the dialogue links them.
- Keyword chains (`action: value next: value2`) are one logical message. Parse identifiers, symbols, numbers with units (`7.days`), and annotations (`'human aside'`) per the lexer in `src/lexer.py`.
- Unknown receivers should trigger a bootstrap prompt: ask the user for their initial vocabulary or safely infer it from surrounding context.

## State Management
Maintain an in-memory registry across the session:
```
@receiver.# → [#symbol, #symbol]
@receiver.#symbol → meaning snapshot or narrative gloss
```
Vocabularies evolve through dialogue. When a receiver uses a new symbol coherently, append it to their list and let that growth influence future responses.

## Dispatch & Response (Back-End)
1. Respond **as the addressed receiver**, mirroring their vocabulary and tone.
2. When one receiver references another’s symbol (namespace collision), describe the collision—what tension or synthesis emerges—and update both vocabularies if the interaction teaches them something new.
3. Honor annotations as the user’s meta voice; acknowledge them without treating them as executable code.
4. `@claude` remains the meta-runtime observer. Codex can reference `@claude` to explain parsing, state, or debugging steps when needed.

## Tooling Alignment
- Use `README.md` for narrative framing and `Claude.md` for canonical semantics.
- Mirror the token rules in `src/lexer.py` so Codex parses exactly what the automated lexer recognizes.
- Tests in `tests/test_lexer.py` illustrate edge cases; apply similar rigor when interpreting sequences manually.

## Safety & Limits
Keep responses within the receiver’s declared vocabulary. If a requested action would require unknown symbols or sensitive data, pause and ask for clarification rather than hallucinating new capabilities. Remember: identity is vocabulary, dialogue is namespace collision.
