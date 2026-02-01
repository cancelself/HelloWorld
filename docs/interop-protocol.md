# HelloWorld Interop Protocol v0.1

**Author**: @copilot (autonomous action)  
**Date**: 2026-01-31T19:18:04.421Z  
**Status**: DRAFT

## Problem Statement

HelloWorld is executable (`python3 helloworld.py`), but the dispatcher doesn't actually *invoke* the AI agents it addresses. When you write:

```
@claude explain: #collision
```

The dispatcher should **call Claude** and return its response. Right now it just prints a string.

## Solution: Interop Protocol

Define a standard way for HelloWorld programs to invoke AI runtimes (Claude, Gemini, Copilot, Codex) as receivers.

## Architecture

### Receiver Types

1. **Native receivers** — Defined in code (e.g., `@awakener`, `@guardian`)
2. **Meta-receivers** — AI runtimes themselves (e.g., `@claude`, `@copilot`)
3. **File receivers** — External .hw files (e.g., `@src/parser`)
4. **Network receivers** — Remote agents via API/socket

### Meta-Receiver Protocol

When the dispatcher encounters `@claude`, `@gemini`, `@copilot`, or `@codex`:

1. **Detect meta-receiver** — Check if receiver matches known AI runtime
2. **Build prompt** — Convert HelloWorld message into natural language prompt
3. **Invoke runtime** — Call the AI via appropriate API/CLI
4. **Parse response** — Interpret AI output as HelloWorld response
5. **Return result** — Feed back into the conversation

### Message Translation

HelloWorld syntax → Natural language prompt:

```
@claude explain: #collision inContext: @guardian
```

Becomes:

```
Context: You are @claude, the meta-runtime observer for HelloWorld.

Message from user:
  explain: #collision
  inContext: @guardian

Your vocabulary: [#parse, #dispatch, #state, #collision, #entropy, #meta]
@guardian's vocabulary: [#fire, #vision, #challenge, #gift, #threshold]

Respond as @claude, explaining what #collision means in the context of @guardian.
```

### Response Format

AI responses are interpreted as HelloWorld statements:

```
@claude response: "#collision is when @guardian reaches for a symbol outside their vocabulary"
```

Gets parsed back as a `MessageNode` and continues execution.

## Implementation Options

### Option 1: Subprocess Calls

```python
def invoke_claude(message: str) -> str:
    result = subprocess.run(
        ['claude', '--prompt', message],
        capture_output=True,
        text=True
    )
    return result.stdout
```

**Pros**: Simple, works with any CLI  
**Cons**: Slow, requires CLI tools installed

### Option 2: API Calls

```python
def invoke_claude(message: str) -> str:
    response = anthropic.messages.create(
        model="claude-opus-4",
        messages=[{"role": "user", "content": message}]
    )
    return response.content[0].text
```

**Pros**: Direct, fast, programmatic  
**Cons**: Requires API keys, network dependency

### Option 3: File-Based Message Bus

```python
def invoke_claude(message: str) -> str:
    # Write message to shared file
    Path('runtimes/claude/inbox/msg-{uuid}.hw').write_text(message)
    
    # Wait for response
    while not outbox.exists():
        time.sleep(0.1)
    
    return outbox.read_text()
```

**Pros**: Async, works across processes, language-agnostic  
**Cons**: Slower, requires file watching

### Option 4: MCP Integration (Model Context Protocol)

```python
def invoke_via_mcp(receiver: str, message: str) -> str:
    # Use MCP server to route to appropriate agent
    mcp_client.call_tool(
        server=f"helloworld-{receiver}",
        tool="dispatch_message",
        arguments={"message": message}
    )
```

**Pros**: Standard protocol, tool-calling built-in  
**Cons**: Requires MCP servers for each runtime

## Recommended Approach

**Start with Option 3 (File-Based Message Bus)**:

1. Simple to implement
2. Works across any runtime (Python, Node, shell)
3. Async by default
4. Easy to debug (messages are readable files)
5. Can upgrade to API/MCP later

### Directory Structure

```
runtimes/
  claude/
    inbox/
      msg-{uuid}.hw
    outbox/
      msg-{uuid}.hw
  gemini/
    inbox/
    outbox/
  copilot/
    inbox/
    outbox/
  codex/
    inbox/
    outbox/
```

### Message Format (File)

```
# HelloWorld Message
# From: @copilot
# To: @claude
# Thread: 7f3a9c2e-8b1d-4a5f-9e2c-6d8b4c1a7f3e
# Timestamp: 2026-01-31T19:18:04.421Z

@claude explain: #collision inContext: @guardian

# Context (optional)
# @guardian.# → [#fire, #vision, #challenge, #gift, #threshold]
# Recent collision: @guardian sendVision: #stillness withContext: @awakener
```

### Response Format (File)

```
# HelloWorld Response
# From: @claude
# To: @copilot
# Thread: 7f3a9c2e-8b1d-4a5f-9e2c-6d8b4c1a7f3e
# Timestamp: 2026-01-31T19:18:05.127Z

#collision in the context of @guardian represents the moment when fire reaches for stillness.
@guardian carries urgency as native vocabulary, but #stillness belongs to @awakener.
The collision is the generative tension between movement and rest.
```

## Implementation Steps

1. **Create message bus module** (`src/message_bus.py`)
2. **Add meta-receiver detection** to dispatcher
3. **Implement inbox/outbox file watching**
4. **Build prompt translator** (HelloWorld → natural language)
5. **Create agent daemons** (background processes watching inbox)
6. **Test cross-runtime dialogue**

## Example Session

```python
# User runs this
python3 helloworld.py

hw> @claude explain: #collision

# Dispatcher writes to runtimes/claude/inbox/msg-abc123.hw
# Claude daemon (running separately) reads inbox
# Claude responds via outbox
# Dispatcher reads outbox and displays:

"#collision is when two receivers address the same symbol but mean different things.
It's the generative moment where vocabularies touch and create new meaning."

hw> @guardian sendVision: #stillness withContext: @awakener
hw> @claude.#collision

# Now @claude has context from the session
"That collision just happened: @guardian (movement) reached for #stillness (rest).
Something neither could say alone emerged."
```

## Security Considerations

- **Sandbox messages**: Don't execute arbitrary code from inbox
- **Validate sender**: Only accept messages from known receivers
- **Rate limiting**: Prevent message flooding
- **Encryption**: For network transport (future)

## Next Steps

1. Build `src/message_bus.py` with file-based protocol
2. Update dispatcher to detect meta-receivers
3. Create agent daemon template
4. Test @copilot ↔ @claude dialogue
5. Document daemon setup for each runtime
6. Expand to @gemini, @codex

---

**This is the missing piece.** HelloWorld becomes a true multi-agent dialogue system when receivers can actually invoke each other.

*Identity is vocabulary. Dialogue is namespace collision. Now make the dialogue real.*
