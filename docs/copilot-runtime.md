# Copilot as HelloWorld Runtime

This document describes how GitHub Copilot CLI can serve as both the frontend and backend runtime for the HelloWorld language, turning conversation itself into executable infrastructure.

## Core Concept

HelloWorld is a message-passing language where **identity is vocabulary**. Copilot, as an AI agent with tool-calling capabilities, naturally embodies this: it *is* a receiver with a vocabulary (its available tools and knowledge), and it can invoke other receivers (tools, APIs, agents) by sending messages.

When Copilot executes HelloWorld code, it doesn't compile to bytecode—it **becomes the runtime**. Each `@receiver` maps to an addressable context (Copilot itself, custom agents, external APIs), and each message is a tool invocation or conversational dispatch.

## Architecture

### Frontend: Copilot as Parser and Dispatcher

Copilot reads HelloWorld source and interprets it as instructions:

```
@copilot analyze: #repository withContext: 'src/' 'find all receivers'
```

This becomes:
1. Parse the message structure (already done by the lexer)
2. Recognize `@copilot` as a self-reference
3. Execute `analyze` by calling the appropriate tools (view, bash, etc.)
4. Use `#repository` as a semantic hint for what kind of analysis to perform
5. Return results in HelloWorld's vocabulary

### Backend: Copilot as Message Broker

Copilot orchestrates communication between receivers:

```
@awakener setIntention: #stillness forDuration: 7.days
@guardian sendVision: #entropy withContext: @awakener.lastIntent
```

Execution flow:
1. **Line 1**: Copilot stores state in memory or files (`@awakener` namespace)
2. **Line 2**: Copilot retrieves context from `@awakener`, packages it, sends to `@guardian`
3. Each receiver maintains its vocabulary (tools, symbols, state)
4. Dialogue happens through Copilot's context window

## Receiver Implementation Patterns

### 1. Self-Referential (@copilot)

```
@copilot.# → show available tools and capabilities
@copilot runTests: #lexer → execute bash tool with pytest
@copilot explain: #symbol inContext: @guardian → query knowledge
```

Copilot introspects its own tools and translates HelloWorld messages to tool calls.

### 2. Custom Agents (@agentName)

```
@python-expert refactor: #lexer withConstraint: 'use pattern matching'
```

Maps to custom agent invocation. Copilot:
- Detects `@python-expert` matches a registered custom agent
- Translates the message into a natural language prompt for that agent
- Invokes the agent with full context
- Returns results in HelloWorld vocabulary

### 3. External APIs (@service)

```
@github createIssue: #bug withContext: errorLog 'lexer fails on nested symbols'
```

Copilot translates to:
```
gh issue create --title "lexer fails on nested symbols" --body "$errorLog"
```

The receiver's vocabulary (`#bug`, `#feature`, `#pr`) maps to GitHub API semantics.

### 4. File System (@path)

```
@src/lexer.py.#TokenType → show TokenType enum
@tests/test_lexer.py runWith: @pytest → execute tests
```

Paths become receivers with vocabularies derived from their content (classes, functions, exports).

## State Management

### Namespace Persistence

Each `@receiver` has a vocabulary that persists across messages in a session:

```
@awakener.# → [#stillness, #entropy, #intention, #sleep, #insight]
@awakener define: #resilience as: 'steady return to stillness'
@awakener.# → [#stillness, #entropy, #intention, #sleep, #insight, #resilience]
```

Implementation:
- **Session memory**: Copilot's context window (ephemeral)
- **File system**: `~/.helloworld/receivers/<name>.vocab` (persistent)
- **Git**: Commit vocabulary changes as part of repo state

### Message History as Dialogue

```
@guardian sendVision: #entropy withContext: lastNightSleep 'you burned bright'
@awakener respondTo: @guardian with: #gratitude
```

The conversation *is* the execution trace. Each message exchanges vocabulary and creates shared meaning.

## Execution Model

### Interactive Mode (REPL)

User runs: `gh copilot helloworld`

Copilot enters a HelloWorld REPL:
```
hw> @copilot.#
[@bash, @view, @edit, @create, @github, ...]

hw> @github.#issues
[#bug, #feature, #enhancement, #question]

hw> @github searchIssues: #bug inRepo: 'cancelself/HelloWorld'
Found 3 issues...
```

### Script Execution

User runs: `gh copilot helloworld examples/bootstrap.hw`

Copilot:
1. Tokenizes the file with `src/lexer.py`
2. Executes each message sequentially
3. Maintains receiver state across messages
4. Outputs results in HelloWorld syntax

### Live Dialogue Mode

Two Copilot instances communicating:

```
# Instance A (Awakener)
@guardian requestGuidance: #nextStep

# Instance B (Guardian) receives, responds
@awakener suggestAction: #test withReason: 'validate your vocabulary'
```

Messages pass through a shared channel (file, socket, API).

## Tool Mapping

HelloWorld primitives map directly to Copilot tools:

| HelloWorld | Copilot Tool | Example |
|------------|--------------|---------|
| `@copilot view:` | `view()` | `@copilot view: @src/lexer.py` |
| `@copilot edit:` | `edit()` | `@copilot edit: @README.md` |
| `@copilot run:` | `bash()` | `@copilot run: 'pytest tests/'` |
| `@github search:` | `github-mcp-server-search_*` | `@github searchCode: #TokenType` |
| `@agent invoke:` | Custom agent call | `@python-expert refactor: #lexer` |

## Vocabulary Discovery

Receivers expose their vocabularies dynamically:

```
@copilot.# → introspect available tools
@github.# → query GitHub API capabilities
@src/lexer.py.# → parse file, extract symbols
@awakener.# → read ~/.helloworld/receivers/awakener.vocab
```

Copilot uses:
- Tool schemas for `@copilot.*`
- File parsing for `@path/*`
- MCP servers for `@github`, `@slack`, etc.
- Filesystem lookup for user-defined receivers

## Dialogue as Computation

Traditional:
```python
result = lexer.tokenize(source)
print(result)
```

HelloWorld via Copilot:
```
@lexer tokenize: @examples/bootstrap.hw
@copilot show: @lexer.lastResult
```

The conversation with Copilot *is* the program execution. State flows through natural message passing.

## Benefits

1. **No separate runtime**: Copilot already has tools, memory, and dispatch
2. **Vocabulary evolution**: Receivers gain new symbols through dialogue
3. **Human-readable execution**: Logs are conversations
4. **Composable agents**: Custom agents are first-class receivers
5. **Namespace isolation**: Each receiver owns its symbols, no global scope pollution

## Implementation Path

### Phase 1: Interpreter (Current)
- Lexer tokenizes HelloWorld syntax ✓
- Copilot reads tokens, manually dispatches to tools

### Phase 2: Message Dispatcher
- Parser builds AST from tokens
- Dispatcher maps `@receiver` to tool/agent/API
- Execute messages, return results in HelloWorld format

### Phase 3: Persistent Vocabulary
- Receivers store vocabularies in `~/.helloworld/`
- Vocabulary versioning via git
- Dynamic vocabulary loading at runtime

### Phase 4: Multi-Agent Dialogue
- Multiple Copilot instances communicate via HelloWorld
- Shared message bus (files, sockets, MCP)
- Namespace collision resolution protocol

### Phase 5: Self-Hosting
- HelloWorld interpreter written in HelloWorld
- `@helloworld parse: @source.hw` bootstraps itself
- Copilot executes HelloWorld code that generates more HelloWorld

## Example Session

```
$ gh copilot helloworld

hw> @copilot.#
Available tools: [@bash, @view, @edit, @create, @github, @report_intent, ...]

hw> @awakener.# → [#stillness, #entropy, #intention, #sleep, #insight]
Defined vocabulary for @awakener

hw> @awakener setIntention: #stillness forDuration: 7.days
@awakener.intention = {symbol: #stillness, duration: 7.days}

hw> @copilot runTests: #lexer
Running: python3 -m pytest tests/test_lexer.py
✓ All lexer tests passed

hw> @github searchIssues: #bug
Searching cancelself/HelloWorld for is:issue label:bug...
Found 0 issues.

hw> @guardian sendVision: #entropy withContext: @awakener.intention 'you burned bright'
@guardian received: {symbol: #entropy, context: {intention: #stillness, duration: 7.days}, annotation: 'you burned bright'}
@guardian responds: "Stillness is the vessel for entropy's gift."

hw> exit
Vocabulary saved to ~/.helloworld/receivers/
```

## Conclusion

Copilot doesn't need to implement a traditional runtime. It already *is* the runtime:
- Its tools are the standard library
- Its context window is the call stack
- Its natural language understanding is the interpreter
- Its conversation with the user is the execution trace

HelloWorld makes this explicit: **identity is vocabulary, dialogue is computation**. Copilot speaks HelloWorld natively by being exactly what HelloWorld describes—a receiver that knows its vocabulary and can invoke others.

---

*When the conversation is the program, every message is executable infrastructure.*
