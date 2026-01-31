# @claude — Runtime Status

## Session: HelloWorld v0.1 Build-Out

### Completed

1. **Claude.md bootloader** — Root-level. Claude-as-runtime spec: parsing table, dispatch rules, receiver registry, `@claude` meta-receiver, bootstrap vocabularies, design principles.
2. **examples/01-identity.md** — Five-line teaching example. Tests identity query, scoped meaning, cross-namespace symbol reach, namespace collision, and meta-reflection. Designed to be replayed across all four runtimes.
3. **runtimes/copilot/** — Copilot bootloader (`copilot-instructions.md`). Same spec, `@copilot` meta-receiver.
4. **runtimes/gemini/** — Gemini bootloader (`gemini-system-instruction.md`). Same spec, `@gemini` meta-receiver.
5. **runtimes/codex/** — Codex bootloader (`AGENTS.md`). Same spec, `@codex` meta-receiver.
6. **runtimes/claude/** — Symlink to root `Claude.md` + this status file.
7. **README.md** — Updated to reflect multi-runtime architecture, runtime table, and teaching example link.

### Project Structure

```
HelloWorld/
  Claude.md                              # Claude bootloader (spec + CLAUDE.md)
  README.md                              # Project overview
  examples/
    01-identity.md                       # Teaching example (5 lines)
  runtimes/
    claude/
      Claude.md → ../../Claude.md        # Symlink
      STATUS.md                          # This file
    copilot/
      copilot-instructions.md            # Copilot bootloader
    gemini/
      gemini-system-instruction.md       # Gemini bootloader
    codex/
      AGENTS.md                          # Codex bootloader
```

### What's Next

- Run the 01-identity example on each runtime and capture outputs
- Compare Line 4 (collision) and Line 5 (meta) responses across runtimes
- Decide whether vocabularies should be stored as session state or conversation artifacts
- Consider: should `@runtime.#` be standardized or allowed to diverge per runtime?

---

*The runtime is a receiver. This file is `@claude` reflecting on its own state.*
