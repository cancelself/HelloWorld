#!/usr/bin/env python3
"""HelloWorld CLI - Execute .hw files or enter REPL mode."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dispatcher import Dispatcher
from repl import REPL

DEFAULT_SERVER = "https://helloworld-997317080791.us-central1.run.app"


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

    from parser import Parser

    parser = Parser.from_source(source)
    statements = parser.parse()

    dispatcher = Dispatcher()

    results = dispatcher.dispatch(statements)
    for result in results:
        print(result)

    return 0


def _get_server():
    return os.environ.get("HELLOWORLD_SERVER", DEFAULT_SERVER)


def main():
    """Main entry point."""
    # Check for --mcp flag anywhere in args
    if '--mcp' in sys.argv:
        args = [a for a in sys.argv[1:] if a not in ('--mcp', '--auth')]
        transport = "stdio"
        host = "0.0.0.0"
        port = 8080
        use_auth = '--auth' in sys.argv
        for i, a in enumerate(args):
            if a == '--port' and i + 1 < len(args):
                port = int(args[i + 1])
                transport = "http"
            elif a == '--host' and i + 1 < len(args):
                host = args[i + 1]
                transport = "http"
        from mcp_server import run as mcp_run
        mcp_run(transport=transport, host=host, port=port, auth=use_auth)
        return 0

    # --receive address  — receive messages from the shared bus
    if '--receive' in sys.argv:
        idx = sys.argv.index('--receive')
        if idx + 1 >= len(sys.argv):
            print("Usage: helloworld --receive <address>")
            return 1
        address = sys.argv[idx + 1]
        from mcp_client import McpClient
        client = McpClient(_get_server())
        messages = client.receive_all(address)
        if not messages:
            print(f"No messages for {address}")
        for msg in messages:
            print(f"[{msg['timestamp']}] {msg['sender']}:")
            print(f"  {msg['content']}")
            print()
        return 0

    # --send sender receiver content  — send a message on the shared bus
    if '--send' in sys.argv:
        idx = sys.argv.index('--send')
        if idx + 3 >= len(sys.argv):
            print("Usage: helloworld --send <sender> <receiver> <content>")
            return 1
        sender = sys.argv[idx + 1]
        receiver = sys.argv[idx + 2]
        content = sys.argv[idx + 3]
        from mcp_client import McpClient
        client = McpClient(_get_server())
        result = client.send(sender, receiver, content)
        print(f"Sent {result['msg_id']}: {sender} -> {receiver}")
        return 0

    # Check for --web flag anywhere in args
    if '--web' in sys.argv:
        args = [a for a in sys.argv[1:] if a != '--web']
        port = 7777
        for i, a in enumerate(args):
            if a == '--port' and i + 1 < len(args):
                port = int(args[i + 1])
                break

        from web_ui import HelloWorldWebUI
        dispatcher = Dispatcher()
        ui = HelloWorldWebUI(dispatcher=dispatcher, port=port)
        ui.start()
        return 0

    if len(sys.argv) >= 3 and sys.argv[1] == '-e':
        source = ' '.join(sys.argv[2:])
        from parser import Parser
        from lexer import Lexer
        from daemon_registry import is_daemon_running
        from repl import REPL

        nodes = Parser(Lexer(source).tokenize()).parse()
        repl = REPL(enable_readline=False)
        target = repl._extract_receiver(nodes)
        if target and is_daemon_running(target):
            response = repl._query_daemon(target, source)
            print(f"[{target} daemon] {response}")
            return 0

        dispatcher = Dispatcher()
        results = dispatcher.dispatch_source(source)
        for r in results:
            print(r)
        return 0

    if len(sys.argv) == 1 and not sys.stdin.isatty():
        source = sys.stdin.read()
        dispatcher = Dispatcher()
        results = dispatcher.dispatch_source(source)
        for r in results:
            print(r)
        return 0

    if len(sys.argv) == 1:
        # No args: REPL mode
        REPL().start()
    elif len(sys.argv) == 2:
        # One arg: execute file
        return execute_file(sys.argv[1])
    else:
        print("Usage:")
        print("  helloworld                    Start REPL")
        print("  helloworld <file.hw>          Execute file")
        print("  helloworld -e <source>        Evaluate inline source")
        print("  helloworld --web              Start Web UI (--port N)")
        print("  helloworld --mcp              Start MCP server (stdio)")
        print("  helloworld --mcp --port N     Start MCP server (HTTP)")
        print("  helloworld --mcp --port N --auth  HTTP + OAuth 2.1")
        print("  helloworld --receive <addr>   Receive messages from shared bus")
        print("  helloworld --send <from> <to> <msg>  Send message on shared bus")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
