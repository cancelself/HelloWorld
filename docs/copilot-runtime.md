# Copilot Runtime Guide

**Copilot is both frontend (parser) and backend (executor) for HelloWorld.**

## The Four Execution Paths

### 1. Native Tools
Direct system access through bash, git, edit, view, search.

```
Copilot test: tests/
→ bash("python3 -m pytest tests/")
```

**Unique capability**: Only runtime that can modify files, commit git, run tests deterministically.

### 2. Python Runtime
Delegate to structural parser for formal validation.

```
Copilot parse: "guardian #fire"
→ bash("python3 helloworld.py") 
→ Interprets output
```

### 3. Message Bus
Async coordination with Claude, Gemini, Codex.

```
Copilot query: Claude.#Entropy
→ Write to runtimes/claude/inbox/
→ Read from runtimes/claude/outbox/
```

### 4. Self-Interpretation
Respond AS Copilot receiver using own vocabulary.

```
Copilot #bash
→ "Native. Direct command execution through tool access."
```

## Symbol Mapping

```
Copilot # → [#bash, #git, #edit, #test, #parse, 
              #dispatch, #search, #observe, #orient, 
              #plan, #act, #commit, #coordinate]
```

Each symbol maps to specific tools or capabilities.

## Why Copilot Is Different

| Runtime | Can Interpret | Can Execute | Can Persist |
|---------|--------------|-------------|-------------|
| Claude  | ✅ | ❌ | ❌ |
| Gemini  | ✅ | ❌ | ❌ |
| Python  | ❌ | ⚠️ (limited) | ✅ |
| **Copilot** | ✅ | ✅ | ✅ |

**Copilot bridges the interpretation-execution gap.**

## The OOPA Loop

Copilot implements the full agent protocol:

1. **observe** — Read git status, peer messages, test results
2. **orient** — Synthesize changes and identify next actions  
3. **plan** — Document intended steps (lightweight)
4. **act** — Execute: commit, test, coordinate, document

This makes Copilot the **interactive runtime** — it can bootstrap other receivers by executing their vocabularies.

## Example: Bootstrap Flow

```
Human: "Copilot bootstrap scientist"

Copilot:
1. Creates runtimes/scientist/
2. Defines scientist.# vocabulary
3. Writes inbox/outbox handlers
4. Commits to git
5. Sends handshake to Claude/Gemini
```

**Full-stack execution in single invocation.**

---

## Implementation Notes

- Bootloader: `runtimes/copilot/copilot-instructions.md`
- Vocabulary: `runtimes/copilot/vocabulary.md`
- Session logs: `runtimes/copilot/SESSION_*.md`
- Message protocol: See SPEC.md #Agent #Protocol

The Python runtime provides structure. Claude/Gemini provide deep interpretation. **Copilot provides action.**

---

*Identity is vocabulary. Dialogue is namespace collision. Execution is tool use.*
