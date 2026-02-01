"""HelloWorld REPL - Interactive Shell."""

import os
import sys
from typing import Optional

from dispatcher import Dispatcher
from lexer import Lexer
from parser import Parser


class REPL:
    def __init__(self, dispatcher: Optional[Dispatcher] = None, enable_readline: bool = True):
        self.dispatcher = dispatcher or Dispatcher()
        self.running = True
        self.enable_readline = enable_readline and os.environ.get("HELLOWORLD_DISABLE_READLINE") != "1"
        if self.enable_readline:
            self._setup_readline()

    def _setup_readline(self):
        try:
            import readline
            import atexit

            # Set up history
            histfile = os.path.expanduser("~/.helloworld_history")
            try:
                readline.read_history_file(histfile)
                readline.set_history_length(1000)
            except FileNotFoundError:
                pass
            def _write_history():
                try:
                    readline.write_history_file(histfile)
                except (PermissionError, OSError):
                    pass
            atexit.register(_write_history)

            # Set up completion
            def completer(text, state):
                receivers = self.dispatcher.list_receivers()
                # Get all symbols from all receivers
                all_symbols = set()
                for r in receivers:
                    all_symbols.update(self.dispatcher.vocabulary(r))
                
                options = receivers + sorted(list(all_symbols))
                matches = [o for o in options if o.startswith(text)]
                if state < len(matches):
                    return matches[state]
                else:
                    return None

            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")
            # Allow @ and # in words for completion
            readline.set_completer_delims(" \t\n\"\\'`@$><=;|&{(")
        except ImportError:
            pass

    def start(self):
        print("HelloWorld v0.1")
        print("Type 'exit' to quit, 'save [@receiver]' to persist vocabularies, 'load <file>.hw' to run a script.")
        
        while self.running:
            try:
                text = input("hw> ")
                if not text.strip():
                    continue
                
                parts = text.split()
                command = parts[0]
                if command == "exit":
                    self.dispatcher.save()
                    self.running = False
                    continue
                
                if command == "save":
                    target = parts[1] if len(parts) > 1 else None
                    if target and target.lower() == "all":
                        target = None
                    if target and not target.startswith("@"):
                        target = f"@{target}"
                    self.dispatcher.save(target)
                    if target:
                        print(f"Saved {target} vocabulary.")
                    else:
                        print("Saved all receiver vocabularies.")
                    continue
                
                if command == "load" and len(parts) > 1:
                    self._load_file(parts[1])
                    continue

                self._process(text)
            except KeyboardInterrupt:
                print("\nType 'exit' to quit.")
            except EOFError:
                self.running = False

    def _load_file(self, filename: str):
        try:
            if not os.path.exists(filename):
                print(f"File not found: {filename}")
                return
            
            with open(filename, 'r') as f:
                content = f.read()
                self._process(content)
        except Exception as e:
            print(f"Error loading file: {e}")

    def _process(self, source: str):
        try:
            # 1. Lex
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            
            # 2. Parse
            parser = Parser(tokens)
            nodes = parser.parse()
            
            # 3. Dispatch
            results = self.dispatcher.dispatch(nodes)
            
            # 4. Print results
            for result in results:
                print(f"→ {result}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    repl = REPL()
    repl.start()
