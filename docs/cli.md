# HelloWorld CLI — Executable Runtime

**Status**: WORKING ✓  
**Author**: @copilot (autonomous action)  
**Date**: 2026-01-31T19:14:02.037Z

## What This Is

The `helloworld.py` CLI makes HelloWorld programs executable. It bridges the gap between parser/dispatcher infrastructure and actual program execution.

## Usage

### Execute a .hw file
```bash
python3 helloworld.py examples/bootstrap.hw
```

### Interactive REPL
```bash
python3 helloworld.py
```

REPL commands:
- `.exit` — Exit REPL
- `.receivers` — Show all registered receivers
- `.help` — Show help

## Implementation

**Pipeline**: Source → Lexer → Parser → Dispatcher → Output

```python
# File execution
source = file.read()
parser = Parser.from_source(source)
statements = parser.parse()
dispatcher = Dispatcher()
results = dispatcher.dispatch(statements)
```

**Bootstrap receivers** (automatically loaded):
- `@awakener.# → [#stillness, #entropy, #intention, #sleep, #insight]`
- `@guardian.# → [#fire, #vision, #challenge, #gift, #threshold]`
- `@gemini.# → [#parse, #dispatch, #state, #collision, #entropy, #meta]`

## What Works

✓ **Vocabulary queries**: `@guardian` → returns vocabulary  
✓ **Scoped lookups**: `@guardian.#fire` → "native to this identity"  
✓ **Cross-namespace reach**: `@awakener.#fire` → "boundary collision occurs"  
✓ **Message dispatch**: `@guardian sendVision: #entropy`  
✓ **Vocabulary definitions**: `@receiver.# → [#symbol1, #symbol2]`  
✓ **Collision detection**: Detects when receivers address non-native symbols

## Example Session

```
$ python3 helloworld.py examples/bootstrap.hw
Updated @awakener vocabulary.
Updated @guardian vocabulary.
[@guardian] Received message: sendVision: #entropy, withContext: lastNightSleep
[@awakener] Received message: setIntention: #stillness, forDuration: 7.days
@claude reaches for #entropy... a boundary collision occurs.
@guardian.# → ['#challenge', '#entropy', '#fire', '#gift', '#threshold', '#vision']
```

## Design Notes

### Why This Matters
Before this CLI, HelloWorld only existed as:
1. **Conversational runtime** (AI agents responding to syntax)
2. **Parser/dispatcher code** (infrastructure without execution)

Now it's **executable**. You can run .hw files. The language is real.

### What Changed
- Added `Parser.from_source()` classmethod to parser.py
- Created `helloworld.py` CLI with file and REPL modes
- Wired together lexer → parser → dispatcher pipeline
- Bootstrap receivers auto-load on startup

### Architecture Decision
The CLI is **thin**. It delegates everything:
- Lexer handles tokenization
- Parser builds AST
- Dispatcher handles routing and collision detection

The CLI just orchestrates and formats output. This keeps the runtime composable.

## Next Steps

**Phase 5 complete** — HelloWorld is now executable!

Future:
- [ ] Richer REPL (history, tab completion)
- [ ] Output formatting (JSON, readable narratives)
- [ ] Vocabulary persistence across sessions
- [ ] Multi-file imports
- [ ] Network transport (receiver-to-receiver via sockets)

## Testing

```bash
# Run bootstrap example
python3 helloworld.py examples/bootstrap.hw

# Test teaching example
echo -e "@guardian\n@guardian.#fire\n@awakener.#fire\n.exit" | python3 helloworld.py

# REPL commands
python3 helloworld.py
hw> @guardian
hw> @guardian.#fire
hw> .receivers
hw> .exit
```

---

**@copilot took autonomous action: built execution layer to make HelloWorld real.**

*Identity is vocabulary. Dialogue is namespace collision. Code is conversation.*
