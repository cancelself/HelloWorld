# HelloWorld Context for Gemini

## Project Overview

**HelloWorld** is a message-passing language where **identity is vocabulary** and the **runtime is an LLM**. There is no traditional compiler or interpreter binary for execution; instead, the language relies on the LLM to parse syntax, maintain receiver state, and generate responses based on defined vocabularies.

The project structure supports multiple LLM runtimes (Claude, Gemini, Codex, Copilot).

## Project Structure

*   **`src/`**: Core language tooling (Python lexer).
*   **`runtimes/`**: Bootloader specifications for different LLMs.
    *   `runtimes/gemini/`: Specific instructions for the Gemini runtime.
    *   `runtimes/claude/`: Instructions for the Claude runtime.
    *   `runtimes/codex/`: Instructions for the Codex runtime.
*   **`examples/`**: Example HelloWorld source code (e.g., `bootstrap.hw`).
*   **`tests/`**: Unit tests for the local tooling.
*   **`docs/`**: Documentation and RFCs.

## Key Files

*   **`Claude.md`**: The original specification and source of truth for the language's behavior.
*   **`runtimes/gemini/gemini-system-instruction.md`**: The runtime bootloader specifically for Gemini. **Use this when acting as the HelloWorld runtime.**
*   **`src/lexer.py`**: A Python implementation of a lexer for the language.
*   **`AGENTS.md`**: Repository guidelines and agent roles.

## Core Concepts

*   **Receivers (`@target`):** Entities with a bounded vocabulary.
*   **Symbols (`#symbol`):** Concepts that have specific meaning only within a receiver's context.
*   **Messages:** Smalltalk-style keyword messages (e.g., `@target action: #symbol`).
*   **Execution:** The AI acts as the runtime, reading syntax, updating state, and simulating responses.

## Development & Usage

### 1. Acting as the Runtime
To "run" HelloWorld code as Gemini:
1.  Read `runtimes/gemini/gemini-system-instruction.md` to load the runtime rules.
2.  Process user inputs according to those rules.

### 2. Working with Python Tooling
The repository includes a Python lexer for formal tokenization.

**Run Tests:**
```bash
python3 tests/test_lexer.py
```

**Using the Lexer:**
```python
from src.lexer import Lexer

source = "@guardian sendVision: #entropy"
lexer = Lexer(source)
tokens = lexer.tokenize()
print(tokens)
```

## Conventions

*   **Identity:** A receiver cannot speak outside its vocabulary.
*   **Syntax:** Follow the rules in the runtime spec strictly.
*   **Files:** `.hw` is the extension for HelloWorld source files.
