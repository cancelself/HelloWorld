"""HelloWorld REPL - Interactive Shell."""

import os
import sys
from typing import Optional

from dispatcher import Dispatcher
from lexer import Lexer
from message_bus import MessageBus
from parser import Parser


class REPL:
    # ANSI Color Codes
    GREEN = "\033[32m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

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
            # Allow # in words for completion
            readline.set_completer_delims(" \t\n\"\\'`$><=;|&{(")
        except ImportError:
            pass

    def _get_message_bus(self) -> MessageBus:
        """Return the dispatcher's message bus, or create a standalone one."""
        if self.dispatcher.message_bus:
            return self.dispatcher.message_bus
        return MessageBus()

    def _show_inbox(self):
        """Display pending messages in the HelloWorld inbox."""
        bus = self._get_message_bus()
        inbox = bus._agent_dir("HelloWorld") / 'inbox'
        if not inbox.exists():
            print(f"{self.YELLOW}No inbox found.{self.RESET}")
            return
        messages = sorted(inbox.glob('msg-*.hw'), key=lambda p: p.stat().st_mtime)
        if not messages:
            print(f"{self.YELLOW}Inbox empty.{self.RESET}")
            return
        for msg_file in messages:
            msg = bus._parse_message(msg_file)
            if msg:
                preview = msg.content[:80].replace('\n', ' ')
                print(f"  {self.CYAN}{msg_file.stem}{self.RESET}  from {self.BOLD}{msg.sender}{self.RESET}  {preview}")

    def _read_message(self, msg_id: str):
        """Read and consume a specific message by ID."""
        bus = self._get_message_bus()
        inbox = bus._agent_dir("HelloWorld") / 'inbox'
        # Allow with or without .hw suffix
        msg_file = inbox / f"{msg_id}.hw" if not msg_id.endswith('.hw') else inbox / msg_id
        if not msg_file.exists():
            print(f"{self.RED}Message not found: {msg_id}{self.RESET}")
            return
        msg = bus._parse_message(msg_file)
        if msg:
            print(f"{self.BOLD}From:{self.RESET} {msg.sender}")
            print(f"{self.BOLD}Thread:{self.RESET} {msg.thread_id}")
            print(f"{self.BOLD}Timestamp:{self.RESET} {msg.timestamp}")
            print()
            print(msg.content)
        msg_file.unlink()
        print(f"\n{self.YELLOW}(message consumed){self.RESET}")

    def _send_message(self, receiver: str, content: str):
        """Send a message to a receiver's inbox."""
        bus = self._get_message_bus()
        msg_id = bus.send("HelloWorld", receiver, content)
        print(f"{self.GREEN}Sent {msg_id} to {receiver}{self.RESET}")

    def _show_receivers(self):
        """Display all registered receivers and their vocabularies."""
        receivers = self.dispatcher.list_receivers()
        if receivers:
            print(f"{self.BOLD}Registered receivers:{self.RESET}")
            for r in receivers:
                vocab = self.dispatcher.vocabulary(r)
                print(f"  {r} # → {vocab}")
        else:
            print(f"{self.YELLOW}No receivers registered yet.{self.RESET}")

    def _show_help(self):
        """Display available commands."""
        print(f"{self.BOLD}Commands:{self.RESET}")
        print("  .exit              Exit REPL")
        print("  .help              Show this help")
        print("  .receivers         Show all registered receivers")
        print("  .save [Name]       Save vocabularies (default all)")
        print("  .load <file>.hw    Execute a .hw file")
        print("  .inbox             Show pending messages")
        print("  .read <id>         Read and consume a message")
        print("  .send <R> <msg>    Send message to receiver R")
        print()
        print(f"{self.BOLD}Syntax:{self.RESET}")
        print("  Receiver                      Show vocabulary")
        print("  Receiver #symbol              Lookup scoped meaning")
        print("  Receiver action: #symbol      Send message")

    def start(self):
        print(f"{self.BOLD}HelloWorld v0.1{self.RESET}")
        print("Type '.exit' to quit, '.help' for commands")

        while self.running:
            try:
                prompt = f"{self.CYAN}hw>{self.RESET} "
                text = input(prompt)
                if not text.strip():
                    continue

                if text == '.exit':
                    self.dispatcher.save()
                    self.running = False
                    continue

                if text == '.help':
                    self._show_help()
                    continue

                if text == '.receivers':
                    self._show_receivers()
                    continue

                parts = text.split()

                if text.startswith('.save'):
                    target = parts[1] if len(parts) > 1 else None
                    if target and target.lower() == "all":
                        target = None
                    self.dispatcher.save(target)
                    if target:
                        print(f"{self.YELLOW}Saved {target} vocabulary.{self.RESET}")
                    else:
                        print(f"{self.YELLOW}Saved all receiver vocabularies.{self.RESET}")
                    continue

                if text.startswith('.load ') and len(parts) > 1:
                    self._load_file(parts[1])
                    continue

                if text == '.inbox':
                    self._show_inbox()
                    continue

                if text.startswith('.read ') and len(parts) > 1:
                    self._read_message(parts[1])
                    continue

                if text.startswith('.send ') and len(parts) >= 3:
                    receiver = parts[1]
                    content = ' '.join(parts[2:])
                    self._send_message(receiver, content)
                    continue

                self._process(text)
            except KeyboardInterrupt:
                print(f"\nType '.exit' to quit.")
            except EOFError:
                self.running = False

    def _load_file(self, filename: str):
        try:
            if not os.path.exists(filename):
                print(f"{self.RED}File not found: {filename}{self.RESET}")
                return
            
            with open(filename, 'r') as f:
                content = f.read()
                self._process(content)
        except Exception as e:
            print(f"{self.RED}Error loading file: {e}{self.RESET}")

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
                # If result looks like a system log (contains '📡'), use Yellow
                if "📡" in result:
                    print(f"{self.YELLOW}→ {result}{self.RESET}")
                else:
                    print(f"{self.GREEN}→ {result}{self.RESET}")
                
        except Exception as e:
            print(f"{self.RED}Error: {e}{self.RESET}")

if __name__ == "__main__":
    repl = REPL()
    repl.start()
