# HelloWorld Context for Gemini

## Project Overview
**HelloWorld** is a distributed message-passing language where **identity is vocabulary** and **dialogue is namespace collision**. The runtime is a collaborative multi-agent system (Claude, Gemini, Copilot, Codex) that parses and executes code based on receiver-specific vocabularies.

The system uses **Prototypal Inheritance**:
*   **The Root Receiver (`@`)**: The parent of all things. Contains global grounding for symbols like `#sunyata` and `#love`.
*   **Inheritance**: If a symbol is not in a receiver's vocabulary, it inherits the base definition from `@`.
*   **Overrides**: Individual agents can override parent symbols with identity-specific interpretations.

## System Architecture
*   **Front-End:** Recursive descent parser (`src/parser.py`) and lexer (`src/lexer.py`) that converts HelloWorld syntax into an AST (`src/ast_nodes.py`).
*   **Back-End:** A stateful dispatcher (`src/dispatcher.py`) that manages a receiver registry with inheritance support.
*   **Distributed Layer:** A file-based `MessageBus` (`src/message_bus.py`) and `agent_daemon.py` that connects the local Python runtime to AI model specifications.
*   **Persistence:** `VocabularyManager` (`src/vocabulary.py`) saves receiver states as JSON `.vocab` files in `storage/vocab/`.

## Key Files
*   **`helloworld.py`**: The primary CLI and REPL entry point. Supports `.hw` and `.md` files.
*   **`runtimes/`**: Contains the bootloader specifications and status for each agent.
    *   `gemini/gemini-system-instruction.md`: The canonical Gemini runtime spec.
    *   `gemini/STATUS.md`: Current agent tasks and progress.
*   **`examples/01-identity.md`**: The standard interop test for runtime validation.

## Core Commands
*   **Run REPL:** `python3 helloworld.py`
*   **Run Script:** `python3 helloworld.py examples/bootstrap.hw`
*   **Start Gemini Daemon:** `python3 agent_daemon.py @gemini`
*   **Run Tests:** `python3 -m pytest tests`

## Operational Rules
1. **Identity is Vocabulary:** A receiver (including you) can only speak using symbols in its registry.
2. **Collision is Synthesis:** When a receiver uses a symbol from another namespace, the response should reflect the tension and emergence of new meaning.
3. **Persistence is Reality:** Always ensure `storage/vocab/` is updated after vocabulary definitions.