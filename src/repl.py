"""HelloWorld REPL - Interactive Shell."""

import sys
from lexer import Lexer, TokenType
from parser import Parser
from dispatcher import Dispatcher

class REPL:
    def __init__(self):
        self.dispatcher = Dispatcher()
        self.running = True

    def start(self):
        print("HelloWorld v0.1")
        print("Type 'exit' to quit. Identity is vocabulary.")
        
        while self.running:
            try:
                text = input("hw> ")
                if text.strip() == "exit":
                    self.running = False
                    continue
                if not text.strip():
                    continue
                
                self._process(text)
            except KeyboardInterrupt:
                print("\nType 'exit' to quit.")
            except EOFError:
                self.running = False

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
