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
- `#sync` — State synchronization

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

@copilot createFile: #parser at: 'src/parser.py'
→ generates parser implementation
```

## Vocabulary Evolution

This vocabulary grows through dialogue. New symbols emerge when:
- User requests novel operations
- Cross-receiver communication introduces concepts
- System capabilities expand

Current vocabulary snapshot saved in this file. Updates tracked via git commits.

---

**Vocabulary Version**: 0.1.0  
**Last Updated**: 2026-01-31T18:49:28.607Z  
**Symbols Count**: 20
