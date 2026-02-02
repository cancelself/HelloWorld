#!/usr/bin/env python3
"""
HelloWorld REPL — Copilot as Runtime
Demonstrates: Parse → Dispatch → Execute loop
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lexer import tokenize
from parser import parse
from dispatcher import Dispatcher

def repl():
    """Interactive HelloWorld REPL"""
    print("HelloWorld REPL v1.0")
    print("Identity is vocabulary. Dialogue is learning.")
    print("Type 'exit' or 'quit' to exit.\n")
    
    dispatcher = Dispatcher(llm_enabled=False)
    
    while True:
        try:
            line = input("HelloWorld> ").strip()
            
            if line in ('exit', 'quit', ''):
                print("Dialogue complete.")
                break
            
            # Parse
            tokens = tokenize(line)
            ast = parse(tokens)
            
            # Dispatch
            result = dispatcher.dispatch(ast)
            
            # Display
            print(f"→ {result}\n")
            
        except KeyboardInterrupt:
            print("\n\nDialogue interrupted.")
            break
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    repl()
