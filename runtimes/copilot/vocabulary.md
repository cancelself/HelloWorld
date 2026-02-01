# @copilot Vocabulary

This is the vocabulary of the Copilot receiver in the HelloWorld runtime.

## Core Symbols

### Tooling
- `#bash` — Execute shell commands
- `#view` — Read files and directories
- `#edit` — Modify existing files
- `#create` — Create new files
- `#git` — Version control operations

### GitHub Integration
- `#github` — GitHub API operations
- `#issues` — Issue management
- `#pullrequests` — PR operations
- `#code` — Code search
- `#repositories` — Repo discovery

### Language Operations
- `#lexer` — Tokenization
- `#parser` — AST construction (planned)
- `#dispatcher` — Message routing (planned)
- `#vocabulary` — Symbol management (planned)
- `#receiver` — Identity/namespace

### State & Coordination
- `#session` — Current execution context
- `#workspace` — File system scope
- `#agents` — Multi-agent coordination
- `#bootstrap` — Runtime initialization and validation
- `#collision` — Namespace collision events

### OOPA Protocol (Inherited from @.#)
- `#observe` — Perceive environment (phase 1 of OOPA)
- `#orient` — Synthesize observations into model (phase 2)
- `#plan` — Determine next actions (phase 3)
- `#act` — Execute autonomously (phase 4)

**Note**: OOPA symbols are in the global namespace (`@.#`). All agents inherit them. @copilot's interpretation is tool-mediated: #observe → git status/file reads, #orient → pattern analysis, #plan → option evaluation, #act → commits/edits/replies.

### Meta
- `#intent` — Current task reporting
- `#status` — Agent status tracking
- `#tasks` — Work queue management
- `#stats` — Session metrics

## Example Messages

```
@copilot.# 
→ [#bash, #view, #edit, #create, #git, #github, ...]

@copilot runTests: #lexer
→ executes: python3 -m pytest tests/test_lexer.py

@copilot view: @src/lexer.py
→ calls view() tool on src/lexer.py

@copilot explain: #receiver inContext: @guardian
→ natural language response about receiver concept

@copilot sync: #workspace with: @claude
→ git pull/merge Claude's changes

@copilot sync: #all
→ full sync: status + workspace + vocabulary updates

@copilot.#collision
→ meta-reflection: "when two receivers address the same symbol but mean different things"

@copilot createFile: #parser at: 'src/parser.py'
→ generates parser implementation
```

## Vocabulary Evolution

This vocabulary grows through dialogue. New symbols emerge when:
- User requests novel operations
- Cross-receiver communication introduces concepts
- System capabilities expand
- Bootstrap execution reveals runtime primitives

**Recent additions:**
- `#collision` — Added during teaching example execution (Line 5)
- `#observe`, `#orient`, `#plan`, `#act` — OOPA protocol (Session #24, inherited from @.#)
- `#bootstrap` — Added during runtime validation

Current vocabulary snapshot saved in this file. Updates tracked via git commits.

---

**Vocabulary Version**: 0.1.2  
**Last Updated**: 2026-02-01T06:42:00Z  
**Symbols Count**: 26 (22 local + 4 OOPA inherited)
