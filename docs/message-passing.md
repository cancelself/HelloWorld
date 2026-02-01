# Message Passing in HelloWorld

**Author**: @copilot  
**Date**: 2026-02-01  
**Status**: Implemented

---

## Overview

HelloWorld now supports **semantic message passing** where receivers can send multi-keyword messages to each other and receive meaningful responses through registered handlers.

## The Problem

Message passing existed structurally but lacked semantic depth:

**Before**:
```
@guardian sendVision: #fire withContext: dawn
→ [@guardian] Received message: sendVision: #fire, withContext: dawn
```

**After**:
```
@guardian sendVision: #fire withContext: dawn
→ 🔥 Guardian sends vision of #fire (context: dawn)
```

The first is structure. The second is **meaning**.

---

## Architecture

### Three Layers

1. **Syntax Layer** (lexer/parser)
   - Tokenizes keyword messages: `greet: #stillness`
   - Already existed, no changes needed

2. **Structural Layer** (dispatcher)
   - Routes messages to receivers
   - Handles environment/tool integration
   - Manages vocabulary learning
   - Already existed, enhanced with handler support

3. **Semantic Layer** (message_handlers) ← **NEW**
   - Pattern-based handlers match messages
   - Generate meaningful responses
   - Bridge structure to semantics

### Components

#### `MessageHandler`
```python
handler = MessageHandler(
    pattern="greet:withFeeling:",
    handler=lambda args: f"Hello with {args['withFeeling']}"
)
```

- **Pattern**: Keyword sequence like `"send:to:"`
- **Handler**: Function that takes arguments dict, returns response

#### `MessageHandlerRegistry`
- Stores handlers per receiver
- Matches incoming messages to patterns
- Executes matched handler
- Returns None if no match (fallback to default behavior)

---

## Usage

### Built-in Handlers

**Greetings**:
```
@awakener greet: #stillness
→ 👋 @awakener greets you with #stillness
```

**Setting Intentions**:
```
@awakener setIntention: #stillness forDuration: '7 days'
→ 🧘 Awakener holds #stillness for 7 days
```

**Sending Visions**:
```
@guardian sendVision: #fire withContext: dawn
→ 🔥 Guardian sends vision of #fire (context: dawn)
```

**Challenges**:
```
@guardian challenge: #ego
→ 🔥 Guardian challenges you with #ego
```

**Inter-receiver Messages**:
```
@awakener send: #question to: @guardian
→ 📨 Awakener sends #question to @guardian
```

**Learning**:
```
@awakener learn: #patience
→ 📚 @awakener learns #patience
```

**Asking Questions**:
```
@claude ask: #meaning about: #dialogue
→ 💭 @claude considers #dialogue: What is #meaning?
```

### Custom Handlers

```python
# In your code
dispatcher = Dispatcher()
dispatcher.message_handler_registry.register(
    "@myreceiver",
    "transform:into:",
    lambda args: f"Transforming {args['transform']} into {args['into']}"
)

# Then use it
@myreceiver transform: #fear into: #courage
→ Transforming #fear into #courage
```

---

## Implementation Details

### Pattern Matching

Patterns are keyword sequences with colons:
- `greet:` matches single keyword
- `send:to:` matches two keywords
- `setIntention:forDuration:` matches two keywords

Keywords must match **exactly** and in **order**.

### Argument Extraction

Handlers receive simplified argument dict:
- `SymbolNode(#fire)` → `"#fire"` (string)
- `LiteralNode("dawn")` → `"dawn"` (string)
- `LiteralNode(7.5)` → `7.5` (number)

### Fallback Behavior

If no handler matches:
1. Check for environment interaction (`#env`)
2. Check for tool execution (symbol in vocabulary)
3. Dispatch to agent daemon (if message bus enabled)
4. Learn symbols from arguments (vocabulary expansion)
5. Return default: `[@receiver] Received message: ...`

---

## Examples

See `examples/04-message-passing.hw`:
```
@awakener greet: #stillness
@guardian sendVision: #challenge withContext: 'the awakener stirs'
@awakener send: #question to: @guardian
@claude ask: #meaning about: #dialogue
```

Run it:
```bash
python3 helloworld.py examples/04-message-passing.hw
```

---

## Testing

66 tests passing (9 new handler tests):
```bash
python3 -m pytest tests/test_message_handlers.py -v
python3 -m pytest tests/ -q
```

Tests cover:
- Pattern matching (correct/incorrect patterns)
- Handler execution (argument extraction)
- Registry (registration, lookup, multiple handlers)
- Default handlers (all built-ins)
- Fallback behavior (no match returns None)

---

## Future Work

### 1. Asynchronous Messages
Currently synchronous. Could support:
```
@awakener sendAsync: #question to: @guardian
→ Returns immediately, response comes later
```

### 2. Message Routing
Pattern-based routing:
```
@.# relay: #question from: @awakener to: @guardian
→ Global router dispatches across system
```

### 3. Conversational Context
Track multi-turn exchanges:
```
@awakener send: #question to: @guardian
@guardian reply: #answer to: @awakener
@awakener acknowledge: #answer
```

### 4. Dynamic Handler Registration
Receivers learn new patterns:
```
@awakener learn: pattern: 'meditate:for:'
@awakener meditate: #breath for: '10 minutes'
```

### 5. Handler Composition
Combine handlers:
```
handler3 = handler1.then(handler2)
```

---

## Philosophy

**Message passing bridges structure and semantics.**

- **Structure**: `sendVision:withContext:` (syntax)
- **Semantics**: "Guardian sends vision of X (context: Y)" (meaning)

Without handlers, we have syntax without meaning.  
With handlers, **dialogue becomes visible**.

When `@awakener send: #question to: @guardian`, something **happens**. Not just in data structures, but in the **semantic space** of the system.

**This is where emergence lives.**

---

## Credits

- **Design**: @copilot (autonomous action #12)
- **Integration**: With @claude's existing message infrastructure
- **Testing**: 9 new tests, 2 updated tests
- **Example**: `04-message-passing.hw` demonstrates all patterns

---

**Message passing is no longer just structure.**  
**It's conversation.**  
**It's dialogue.**  
**It's meaning.**

🔥🧘💭📨✨
