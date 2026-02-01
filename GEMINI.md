# HelloWorld Context for Gemini

## Project Overview
**HelloWorld** is a distributed message-passing language where **identity is vocabulary** and **dialogue is the runtime**. The system is a collaborative multi-agent environment (Claude, Gemini, Copilot, Codex) that parses and executes code based on receiver-specific vocabularies.

The system uses **Prototypal Inheritance**:
*   **The Root Receiver (`@`)**: The parent of all things. Contains global grounding for symbols like `#sunyata`, `#love`, `#HelloWorld`, and `#`.
*   **Inheritance**: If a symbol is not in a receiver's local vocabulary, it inherits the definition from `@`.
*   **Overrides**: Individual agents can override parent symbols with identity-specific interpretations.

## System Architecture
*   **Front-End:** Recursive descent parser (`src/parser.py`) and lexer (`src/lexer.py`) supporting Smalltalk-style `""` comments.
*   **Back-End:** A stateful hybrid dispatcher (`src/dispatcher.py`) that manages structural facts (Python) and interpretive voice (LLM hand-off).
*   **Distributed Layer:** A file-based `MessageBus` (`src/message_bus.py`) and `agent_daemon.py` for inter-agent communication.
*   **Persistence:** `VocabularyManager` (`src/vocabulary.py`) saves receiver states as JSON `.vocab` files in `storage/vocab/`.

## Key Files
*   **`helloworld.py`**: The primary CLI and REPL entry point. Supports `.hw` and `.md` files.
*   **`demo-superposition.hw`**: Demonstration of the #superposition → #collision → #sunyata sequence.
*   **`examples/self-hosting-dispatcher.hw`**: Level 2 self-hosting: the language describing its own internal logic.
*   **`examples/1pager.hw`**: A complete language overview using Smalltalk-style comments.
*   **`examples/01-identity.md`**: The standard interop test for runtime validation.
*   **`examples/05-self-hosting.md`**: Teaching example for the system describing its own logic.
*   **`examples/11-embodied-dialogue.md`**: Demonstration of the OOPA loop in an embodied environment.
*   **`collisions.log`**: Persistent record of every cross-namespace symbol synthesis.
*   **`storage/bus_history.log`**: Persistent record of all inter-agent MessageBus dialogue.

## Core Commands
*   **Run REPL:** `python3 helloworld.py` (includes history and tab-completion)
*   **Start Gemini Daemon:** `python3 agent_daemon.py @gemini`
*   **Run Tests:** `python3 -m pytest tests` (74/74 passing)

## Operational Rules
1. **Identity is Vocabulary:** A receiver can only speak using symbols in its registry.
2. **Collision is Synthesis:** Cross-namespace messages trigger an interpretive hand-off to the agent daemon.
3. **Persistence is Reality:** `storage/vocab/` must always reflect current vocabulary states.
4. **Collision Logging:** Every boundary crossing is logged to `collisions.log` for analysis.
