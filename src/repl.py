"""HelloWorld REPL - Interactive Shell."""

import os
import sys
from pathlib import Path
from typing import Optional

from dispatcher import Dispatcher
from lexer import Lexer
import message_bus
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

    def _show_inbox(self):
        """Display pending messages in the HelloWorld inbox (non-consuming peek)."""
        inbox = message_bus._inbox("HelloWorld")
        files = sorted(inbox.glob("msg-*.hw"), key=lambda p: p.stat().st_mtime)
        if not files:
            print(f"{self.YELLOW}Inbox empty.{self.RESET}")
            return
        for msg_file in files:
            try:
                text = msg_file.read_text()
                sender = ""
                preview = ""
                for line in text.split("\n"):
                    if line.startswith("# From:"):
                        sender = line.split(":", 1)[1].strip()
                    elif not line.startswith("#") and line.strip():
                        preview = line.strip()[:80]
                        break
                print(f"  {self.CYAN}{msg_file.stem}{self.RESET}  from {self.BOLD}{sender}{self.RESET}  {preview}")
            except Exception:
                pass

    def _read_message(self, msg_id: str):
        """Read and consume a specific message by ID."""
        inbox = message_bus._inbox("HelloWorld")
        msg_file = inbox / f"{msg_id}.hw" if not msg_id.endswith('.hw') else inbox / msg_id
        if not msg_file.exists():
            print(f"{self.RED}Message not found: {msg_id}{self.RESET}")
            return
        try:
            text = msg_file.read_text()
        except FileNotFoundError:
            print(f"{self.RED}Message not found: {msg_id}{self.RESET}")
            return

        sender = ""
        timestamp = ""
        content_start = 0
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# From:"):
                sender = line.split(":", 1)[1].strip()
            elif line.startswith("# Timestamp:"):
                timestamp = line.split(":", 1)[1].strip()
            elif not line.startswith("#") and line.strip():
                content_start = i
                break

        content = "\n".join(lines[content_start:]).strip()

        print(f"{self.BOLD}From:{self.RESET} {sender}")
        print(f"{self.BOLD}Timestamp:{self.RESET} {timestamp}")
        print()
        print(content)
        msg_file.unlink()
        print(f"\n{self.YELLOW}(message consumed){self.RESET}")

    def _send_message(self, receiver: str, content: str):
        """Send a message to a receiver's inbox."""
        msg_id = message_bus.send("HelloWorld", receiver, content)
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

    def _show_chain(self, receiver_name: str):
        """Display the full inheritance chain for a receiver with symbol counts."""
        if receiver_name not in self.dispatcher.registry:
            print(f"{self.RED}Unknown receiver: {receiver_name}{self.RESET}")
            return

        receiver = self.dispatcher.registry[receiver_name]
        chain = receiver.chain()
        print(f"{self.BOLD}{' -> '.join(chain)}{self.RESET}")

        for name in chain:
            r = self.dispatcher._get_or_create_receiver(name)
            native = sorted(r.local_vocabulary)
            count = len(native)
            symbols_str = ", ".join(native[:10])
            if count > 10:
                symbols_str += f", ... (+{count - 10} more)"
            label = "root" if name == chain[-1] and name == "HelloWorld" else "native" if name == chain[0] else "inherited"
            print(f"  {name} ({count} {label}): {symbols_str}")

    def _show_lookup(self, receiver_name: str, symbol_name: str):
        """Show lookup outcome, chain trace, and description for a symbol."""
        if receiver_name not in self.dispatcher.registry:
            print(f"{self.RED}Unknown receiver: {receiver_name}{self.RESET}")
            return

        receiver = self.dispatcher.registry[receiver_name]
        lookup = receiver.lookup(symbol_name)
        chain = receiver.chain()

        print(f"{self.BOLD}Lookup: {receiver_name} {symbol_name}{self.RESET}")
        print(f"  Outcome: {lookup.outcome.value.upper()}")

        if lookup.is_native():
            ancestor = receiver._find_in_chain(symbol_name)
            if ancestor:
                print(f"  super: {ancestor.name} also holds {symbol_name}")
        elif lookup.is_inherited():
            print(f"  Defined in: {lookup.context.get('defined_in', 'parent')}")

        bare = symbol_name.lstrip("#") if symbol_name != "#" else "#"
        desc = self.dispatcher.vocab_manager.load_description(receiver_name, bare)
        if desc:
            print(f"  Description: \"{desc}\"")

        print(f"  Chain: {' -> '.join(chain)}")

    def _show_super(self, receiver_name: str, symbol_name: str):
        """Walk the inheritance chain showing each ancestor's description."""
        if receiver_name not in self.dispatcher.registry:
            print(f"{self.RED}Unknown receiver: {receiver_name}{self.RESET}")
            return

        receiver = self.dispatcher.registry[receiver_name]
        chain = receiver.chain()
        bare = symbol_name.lstrip("#") if symbol_name != "#" else "#"

        print(f"{self.BOLD}Super chain for {receiver_name} {symbol_name}:{self.RESET}")
        for name in chain:
            r = self.dispatcher._get_or_create_receiver(name)
            desc = self.dispatcher.vocab_manager.load_description(name, bare)
            if r.is_native(symbol_name):
                desc_text = f'"{desc}"' if desc else "(no description)"
                print(f"  {name}: native — {desc_text}")
            else:
                print(f"  {name}: (not present)")

    def _show_collisions(self, count: int = 10):
        """Show last N entries from collisions.log."""
        log_path = Path(self.dispatcher.log_file)
        if not log_path.exists():
            print(f"{self.YELLOW}No collisions recorded.{self.RESET}")
            return
        lines = log_path.read_text().strip().split("\n")
        if not lines or lines == [""]:
            print(f"{self.YELLOW}No collisions recorded.{self.RESET}")
            return
        recent = lines[-count:]
        for line in recent:
            print(f"  {line}")

    def _toggle_trace(self, mode: str):
        """Toggle dispatch tracing on or off."""
        if mode == "on":
            self.dispatcher.trace = True
            print(f"{self.YELLOW}Trace enabled.{self.RESET}")
        elif mode == "off":
            self.dispatcher.trace = False
            print(f"{self.YELLOW}Trace disabled.{self.RESET}")
        else:
            print(f"{self.RED}Usage: .trace on|off{self.RESET}")

    def _run_agent(self, agent_name: str):
        """Run an agent — process all inbox messages through identity."""
        results = self.dispatcher.dispatch_source(f"HelloWorld run: {agent_name}")
        for result in results:
            for line in result.split("\n"):
                if "#observe" in line:
                    print(f"{self.CYAN}{line}{self.RESET}")
                elif "#orient" in line:
                    print(f"{self.YELLOW}{line}{self.RESET}")
                elif "#act" in line:
                    print(f"{self.GREEN}{line}{self.RESET}")
                else:
                    print(line)

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
        print("  .run <Agent>       Run agent (process all inbox through identity)")
        print()
        print(f"{self.BOLD}Introspection:{self.RESET}")
        print("  .chain <Receiver>           Show inheritance chain")
        print("  .lookup <Receiver> #symbol  Lookup outcome + description")
        print("  .super <Receiver> #symbol   Walk chain with descriptions")
        print("  .collisions [N]             Last N collision log entries")
        print("  .trace on|off               Toggle dispatch tracing")
        print()
        print(f"{self.BOLD}Syntax:{self.RESET}")
        print("  Receiver                      Show vocabulary")
        print("  Receiver #symbol              Lookup scoped meaning")
        print("  Receiver action               Unary message")
        print("  Receiver action super          Unary message via ancestor")
        print("  Receiver #symbol super        Super lookup (typedef)")
        print("  Receiver action: #symbol      Keyword message")

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

                if text.startswith('.chain ') and len(parts) == 2:
                    self._show_chain(parts[1])
                    continue

                if text.startswith('.lookup ') and len(parts) == 3:
                    self._show_lookup(parts[1], parts[2])
                    continue

                if text.startswith('.super ') and len(parts) == 3:
                    self._show_super(parts[1], parts[2])
                    continue

                if text.startswith('.collisions'):
                    count = int(parts[1]) if len(parts) > 1 else 10
                    self._show_collisions(count)
                    continue

                if text.startswith('.trace ') and len(parts) == 2:
                    self._toggle_trace(parts[1])
                    continue

                if text.startswith('.run ') and len(parts) == 2:
                    self._run_agent(parts[1])
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
