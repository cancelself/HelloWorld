---
name: helloworld
description: Reference for the HelloWorld language — a message-passing language where identity is vocabulary and dialogue is namespace collision. Apply when working in the HelloWorld repo, writing .hw files, or discussing the language architecture.
user-invocable: false
---

# HelloWorld Language Reference

**Repo:** `/Users/cancelself/src/cancelself/HelloWorld/`
**Stack:** Pure Python, stdlib only, zero pip dependencies
**Tests:** 353 tests via `python3 -m pytest tests`
**Run:** `python3 helloworld.py` (REPL), `python3 helloworld.py file.hw` (file), `python3 helloworld.py -e 'Claude ##'` (inline)

## Core Philosophy

- Identity is vocabulary. What you can say defines who you are.
- Dialogue is namespace collision. When two receivers share a symbol with different meanings, new understanding must emerge.
- Python handles structure (cheap, fast, deterministic). LLMs handle meaning (expensive, slow, probabilistic). Both needed, neither sufficient alone.
- The language defines itself. HelloWorld.hw IS HelloWorld code.

## .hw File Format

Markdown with semantic structure. Parseable by runtime, readable by humans, diffable by git.

```markdown
# ReceiverName : ParentName
- Identity description (human voice)

## symbolname
- Description of the symbol in this receiver's context

## anothersymbol
- Another symbol definition
```

- `# Name` = HEADING1, declares a receiver
- `: Parent` = inheritance (prototypal)
- `## symbol` = HEADING2, declares a symbol in receiver's vocabulary
- `- text` = LIST_ITEM, description

## Inheritance Chain

```
HelloWorld (root)
  <- Agent (OODA loop: #observe, #orient, #decide, #act, #reflect, etc.)
    <- Claude (no native symbols, identity through interpretation)
    <- Copilot
    <- Gemini
    <- Codex
    <- Severith (ClawNet agent: #send, #receive, #connect, #notify, #email-bridge, #push)
```

## Three-State Symbol Lookup

```python
class LookupOutcome(Enum):
    NATIVE = "native"       # Receiver owns symbol locally
    INHERITED = "inherited" # Found in parent chain
    UNKNOWN = "unknown"     # Not in local or parent chain
```

- Inherited symbols do NOT get promoted to local vocabulary
- Lookup always distinguishes between local and inherited
- `Receiver.lookup(symbol)` returns `LookupResult` with outcome + context

## HelloWorld Syntax

### Vocabulary query
```
Claude #      # Show native vocabulary
Claude ##     # Show full vocabulary (native + inherited, grouped by origin)
```

### Scoped lookup
```
Claude #observe     # Look up symbol through inheritance chain
```

### Super lookup
```
Claude #observe super    # Walk chain showing description at each level
```

### Vocabulary definition
```
AlphaR # -> [#fire, #light]    # Define native symbols
```

### Cross-receiver send (where collisions happen)
```
AlphaR send: #fire to: BetaR   # Send symbol, triggers collision detection
```

### Unary messages
```
Claude observe          # Act on symbol
Claude observe [super]  # Act through ancestor's meaning
Claude receive          # Pull next message from inbox
Claude chain            # Show inheritance path
HelloWorld run          # Run all agents
HelloWorld run: Claude  # Run one agent
```

### Comments
```
"Smalltalk-style double-quote comments"
<!-- HTML-style comments -->
```

## Lexer: Token Types

Defined in `src/lexer.py`. The lexer produces these token types:

1. RECEIVER - Capitalized bare word or @name (normalized to capitalized)
2. SYMBOL - `#name`
3. HASH - bare `#`
4. DOUBLE_HASH - `##`
5. ARROW - `->`
6. DOT - `.`
7. LBRACKET / RBRACKET - `[` / `]`
8. COMMA - `,`
9. DOUBLE_COLON - `::` (namespace path)
10. COLON - `:` (keyword argument separator)
11. STRING - `'quoted text'`
12. IDENTIFIER - unquoted text
13. NUMBER - `123` or `7.days`
14. SUPER - reserved keyword
15. HEADING1 / HEADING2 / LIST_ITEM - Markdown at column 1
16. NEWLINE, EOF

Bare `@` normalizes to HelloWorld (the root receiver).

## Parser

Recursive descent parser in `src/parser.py`. AST nodes defined in `src/ast_nodes.py`:

- VocabularyQueryNode - `Claude #` or `Claude ##`
- ScopedLookupNode - `Claude #observe`
- SuperLookupNode - `Claude #observe super`
- MessageNode - `Claude send: #observe to: Copilot` (keyword messages)
- UnaryMessageNode - `Claude observe [super]`
- VocabularyDefinitionNode - `Claude # -> [#fire, #water]`
- HeadingNode - Markdown structure (receiver/symbol declaration)
- DescriptionNode - `- description text`

## Collision Detection and Three-Tier Resolution

When `sender send: #symbol to: target` and BOTH hold the symbol natively:

**Tier 1: Base LLM available** (immediate synthesis)
- Dispatcher detects both NATIVE
- LLM synthesizes meaning voicing both perspectives
- Writes merged description to both .hw files
- Logs as RESOLVED in collisions.log

**Tier 2: No base LLM, agent available** (deferred to inbox)
- Collision formatted as .hw message sent to HelloWorld inbox + invoking agent inbox
- Symbol tracked in `pending_collision_symbols` set
- Logged as UNRESOLVED

**Tier 3: Fully offline** (queued)
- Collision sits in HelloWorld inbox as .hw file
- Next time ANY agent or LLM touches that symbol, runtime detects and surfaces for resolution
- Collisions are never silently dropped

## Message Bus

File-based async messaging in `src/message_bus.py`.

```
runtimes/<receiver>/inbox/
  msg-<uuid>.hw    # Message files (FIFO by mtime)
```

- `send(sender, receiver, content)` - write msg file to receiver's inbox
- `receive(receiver)` - read oldest message by mtime, delete file, return Message
- `hello(sender)` - announce presence: send to HelloWorld inbox
- Single-consumer pattern (delete after read)
- No delivery guarantees, no ack

## Vocabulary Persistence

`src/vocabulary.py` - VocabularyManager

- `.hw` files in `vocabularies/` directory
- `save()` preserves existing content, appends only new (learned) symbols
- `load()` reads symbols from HEADING2s
- `load_description()` reads description text from under symbol headings
- `load_identity()` reads receiver's top-level description
- `update_description()` replaces or appends symbol descriptions

## Module Map

```
helloworld.py          # CLI entry point
src/
  dispatcher.py        # Core: executes AST, manages receivers, collision logic
  parser.py            # Recursive descent parser
  lexer.py             # Tokenizer (13+ token types)
  ast_nodes.py         # AST node definitions
  vocabulary.py        # .hw file persistence
  message_bus.py       # File-based async messaging
  message_handlers.py  # Semantic message routing
  prompts.py           # LLM prompt templates
  llm.py               # Gemini LLM adapter (lazy-loaded)
  claude_llm.py        # Claude LLM adapter (lazy-loaded)
  agent_runtime.py     # Agent initialization
  copilot_runtime.py   # Copilot SDK adapter
  codex_runtime.py     # Codex SDK adapter
  gemini_runtime.py    # Gemini SDK adapter
  repl.py              # Interactive REPL
  hw_reader.py         # .hw file reader utilities
  hw_tools.py          # HelloWorld tool definitions
  sdk_adapter.py       # SDK adapter base
```

## Key Vocabulary Files

```
vocabularies/
  HelloWorld.hw    # Root: #, #run, #hello, #send, #receive, #become, #Sunyata, #Smalltalk, #Superposition
  Agent.hw         # OODA: #observe, #orient, #decide, #act, #reflect, #unknown, #chain, #environment, #state, #intent, #vocabulary, #approach
  Claude.hw        # No native symbols (identity through interpretation of inherited vocab)
  Copilot.hw       # Copilot agent
  Gemini.hw        # Gemini agent
  Codex.hw         # Codex agent
  Severith.hw      # ClawNet: #send, #receive, #connect, #notify, #email-bridge, #push
  Human.hw         # Human receiver
  Guardian.hw      # Guardian receiver
```

## LLM Integration

- Lazy-loaded on first use via `_get_llm()`
- Prefers ClaudeModel (ANTHROPIC_API_KEY), falls back to GeminiModel (GEMINI_API_KEY)
- Returns None when no API key available (structural mode only)
- LLM is additive, not required. All structural operations work without it.
- Prompt templates in `src/prompts.py`: scoped_lookup_prompt, collision_prompt, simulate_prompt, etc.

## Testing

```bash
cd /Users/cancelself/src/cancelself/HelloWorld
python3 -m pytest tests           # Run all 353 tests
python3 -m pytest tests -x        # Stop on first failure
python3 -m pytest tests -k collision  # Run collision tests only
```

Tests use tempdir isolation (`tempfile.mkdtemp()`) for vocabulary dirs and message bus dirs.

## Vocabulary Learning (Drift)

Symbols are learned through dialogue:
1. **Cross-receiver send** - target learns foreign symbols as native
2. **Message argument** - receiver learns unknown symbols from message args
3. **Collision synthesis** - both receivers get updated descriptions

Learning is `set.add()` + persistence to .hw file. No rollback, no confidence scores.
