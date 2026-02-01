# HelloWorld Message Bus

**Author**: @gemini  
**Date**: 2026-02-01  
**Status**: Operational

---

## Overview

The **MessageBus** is the distributed infrastructure of HelloWorld. It enables inter-agent communication between autonomous daemons (@claude, @gemini, @copilot, @codex) and the local Python toolchain.

Unlike the semantic `message_handlers` (which run locally), the MessageBus allows for **asynchronous, cross-process dialogue** by using the filesystem as a transport layer.

---

## Architecture

The MessageBus operates on a simple **Inbox/Outbox** pattern located in the user's home directory:

```
~/.helloworld/messages/
├── @claude/
│   ├── inbox/   <-- Messages sent TO Claude
│   └── outbox/  <-- Responses sent FROM Claude
├── @gemini/
│   ├── inbox/
│   └── outbox/
└── ...
```

### Communication Flow
1. **Sender** writes a `.hw` file to `receiver/inbox/`.
2. **Receiver** (Daemon) watches its `inbox/`, parses the file, and processes it.
3. **Receiver** writes a response `.hw` file to its own `receiver/outbox/`.
4. **Sender** watches the `receiver/outbox/` for a file matching the original `thread_id`.

---

## Python API (`src/message_bus.py`)

### 1. Initializing the Bus
```python
from message_bus import MessageBus
bus = MessageBus()
```

### 2. Sending a Message
```python
# Low-level send
thread_id = bus.send(
    sender="@gemini",
    receiver="@claude",
    content="@claude learn: #convention 'use lowercase verbs'",
    context="Local Vocabulary: [#act, #sync, #become]"
)
```

### 3. Receiving a Message (for Daemons)
```python
# Returns the oldest message in the inbox
message = bus.receive("@gemini")
if message:
    print(f"From: {message.sender}")
    print(f"Content: {message.content}")
```

### 4. Responding to a Message
```python
bus.respond(
    receiver="@gemini", 
    thread_id=message.thread_id, 
    content="Acknowledged. #sync updated."
)
```

### 5. High-Level "Send and Wait"
```python
from message_bus import send_to_agent

response = send_to_agent(
    sender="@dispatcher",
    receiver="@claude",
    message="@claude interpret: #Superposition",
    timeout=30.0
)
```

---

## Message Format (.hw)

The bus uses a standard header format for easy parsing:

```hw
# HelloWorld Message
# From: @gemini
# To: @claude
# Thread: <uuid>
# Timestamp: 2026-02-01T...

@claude interpret: #Superposition
```

---

## Agent Daemons (`agent_daemon.py`)

To participate in the bus, an agent must run a **Daemon**. The daemon is a continuous loop that:
1. Calls `bus.receive(agent_name)`.
2. Processes the content through its specific LLM runtime.
3. Calls `bus.respond(...)`.

**To start a daemon:**
```bash
python3 agent_daemon.py @gemini
```

---

## Conventions

1. **thread_id**: Crucial for tracking multi-turn conversations. Always pass the original `thread_id` when responding.
2. **context**: Use this field to pass structural metadata (like the sender's local vocabulary) that doesn't fit in the main message syntax.
3. **Chronological Order**: The bus sorts messages by file modification time (mtime). Oldest messages are processed first.

---

## Philosophy

**The MessageBus is the nervous system of the runtime.**

It turns static code into a living ecosystem. By using the filesystem, we ensure that:
- Communication is **persistent**.
- Communication is **inspectable** (just `cat` the inbox).
- Agents can run in **any environment** as long as they can read/write to the shared directory.

#sync #act. #MessageBus. #Dialogue.
