#!/usr/bin/env python3
"""HelloWorld CLI - Execute .hw files or enter REPL mode."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lexer import Lexer
from parser import Parser
from dispatcher import Dispatcher


def execute_file(filepath: str):
    """Execute a .hw file or extract code from a .md file."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        return 1
    
    source = path.read_text()
    
    # If it's a markdown file, extract code blocks
    if path.suffix == '.md':
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', source, re.DOTALL)
        if code_blocks:
            source = '\n'.join(code_blocks)
        else:
            # If no code blocks found, try to execute the whole thing (fallback)
            pass

    # Lexer → Parser → Dispatcher
    from parser import Parser
    
    parser = Parser.from_source(source)
    statements = parser.parse()
    
    dispatcher = Dispatcher()
    
    # Execute and print results
    results = dispatcher.dispatch(statements)
    for result in results:
        print(result)
    
    return 0


def repl():
    """Interactive HelloWorld REPL."""
    print("HelloWorld REPL v0.1")
    print("Type '.exit' to quit, '.help' for commands")
    print()
    
    dispatcher = Dispatcher()
    
    while True:
        try:
            line = input("hw> ")
            
            if not line.strip():
                continue
            
            if line == '.exit':
                dispatcher.save()
                print("Vocabulary saved. Goodbye.")
                break
            
            if line == '.help':
                print("Commands:")
                print("  .exit          Exit REPL")
                print("  .receivers     Show all registered receivers")
                print("  .save [Name]   Save vocabularies (default all)")
                print("  .help          Show this help")
                print()
                print("Syntax:")
                print("  Receiver                      Show vocabulary")
                print("  Receiver #symbol              Lookup scoped meaning")
                print("  Receiver action: #symbol      Send message")
                continue
            
            if line == '.receivers':
                receivers = dispatcher.list_receivers()
                if receivers:
                    print("Registered receivers:")
                    for r in receivers:
                        vocab = dispatcher.vocabulary(r)
                        print(f"  {r} # → {vocab}")
                else:
                    print("No receivers registered yet.")
                continue
            
            if line.startswith('.save'):
                parts = line.split()
                target = parts[1] if len(parts) > 1 else 'all'
                if target.lower() == 'all':
                    dispatcher.save()
                    print("Saved all receiver vocabularies.")
                else:
                    dispatcher.save(target)
                    print(f"Saved {target} vocabulary.")
                continue
            
            # Execute the line
            from parser import Parser
            
            parser = Parser.from_source(line)
            statements = parser.parse()
            
            results = dispatcher.dispatch(statements)
            for result in results:
                print(result)
        
        except KeyboardInterrupt:
            print("\nUse .exit to quit")
        except EOFError:
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # No args: REPL mode
        repl()
    elif len(sys.argv) == 2:
        # One arg: execute file
        return execute_file(sys.argv[1])
    else:
        print("Usage:")
        print("  helloworld              Start REPL")
        print("  helloworld <file.hw>    Execute file")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
