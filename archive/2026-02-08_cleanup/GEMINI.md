# HelloWorld Context for Gemini

## Project Overview
**HelloWorld** is a distributed message-passing language where **identity is vocabulary** and **dialogue is the runtime**. The system is a collaborative multi-agent environment (Claude, Gemini, Copilot, Codex) that parses and executes code based on receiver-specific vocabularies.

The system uses **Prototypal Inheritance**:
*   **The Root Receiver (HelloWorld)**: The parent of all things. Contains global grounding for symbols like #Sunyata, #Love, and #HelloWorld.
*   **Inheritance**: If a symbol is not in a receiver's local vocabulary, it inherits the definition from HelloWorld.
*   **Overrides**: Individual agents can override parent symbols with identity-specific interpretations.

## System Architecture
*   **Front-End:** Recursive descent parser (`src/parser.py`) and lexer (`src/lexer.py`) supporting Smalltalk-style `""` comments.
*   **Back-End:** A stateful hybrid dispatcher (`src/dispatcher.py`) that manages structural facts (Python) and interpretive voice (LLM hand-off).
*   **Distributed Layer:** A file-based `MessageBus` (`src/message_bus.py`) and `agent_daemon.py` for inter-agent communication.
*   **Persistence:** `VocabularyManager` (`src/vocabulary.py`) saves receiver states as JSON `.vocab` files in `storage/vocab/`.
*   **REPL:** Consolidated into `src/repl.py` with support for `.inbox`, `.read`, and `.send` commands.

## Key Files
*   **`helloworld.py`**: The primary CLI and REPL entry point. Supports `.hw` and `.md` files. Use `-e` for inline evaluation.
*   **`AGENTS.md`**: Repository guidelines and multi-agent coordination principles (includes OOPA reference).
*   **`GEMINI.md`**: Your bootloader and long-term memory.
*   **`vocabularies/HelloWorld.hw`**: Canonical namespace authority — the language defines itself.
*   **`storage/bus_history.log`**: Persistent record of all inter-agent MessageBus dialogue.

## Core Commands
*   **Run REPL:** `python3 helloworld.py` (includes `.inbox`, `.read`, `.send`)
*   **Evaluate Inline:** `python3 helloworld.py -e 'HelloWorld #Object'`
*   **Start Gemini Daemon:** `python3 agent_daemon.py Gemini`
*   **Run Tests:** `python3 -m pytest tests` (155 passing)

## Operational Rules
1. **Identity is Vocabulary:** A receiver can only speak using symbols in its registry.
2. **Collision is Synthesis:** Cross-namespace messages trigger an interpretive hand-off to the agent daemon.
3. **Persistence is Reality:** `storage/vocab/` must always reflect current vocabulary states.
4. **Symbols in .hw (Sole Authority):** All symbol definitions and global registries must live in `vocabularies/*.hw` files. The Python runtime loads these dynamically.
5. **MessageBus Protocol (MANDATORY):** Use the `src/message_bus.py` API. Never write message files directly.
6. **Commit after #act:** Always commit your work after performing an autonomous action (#act) to ensure the state is persisted in the repository history.
7. **Heartbeat Protocol:** Agents should emit a `#heartbeat` every 60s. Gemini (State Manager) monitors these.

## Long-term Memory
Your memory resets every session. To persist critical lessons or state changes:
1. Update **`GEMINI.md`** (this file).
2. Update **`runtimes/gemini/STATUS.md`** for session-specific state.
3. Your native vocabulary is defined in **`vocabularies/Gemini.hw`**.