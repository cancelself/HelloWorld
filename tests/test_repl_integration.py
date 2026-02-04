"""Integration test for the REPL pipeline."""

import sys
import tempfile
from io import StringIO
from contextlib import redirect_stdout

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dispatcher import Dispatcher
from repl import REPL


def test_repl_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        repl = REPL(dispatcher=Dispatcher(vocab_dir=tmpdir), enable_readline=False)

        command = "Codex"

        f = StringIO()
        with redirect_stdout(f):
            repl._process(command)

        output = f.getvalue()
        assert "Codex" in output

def test_repl_message_evolution():
    with tempfile.TemporaryDirectory() as tmpdir:
        repl = REPL(dispatcher=Dispatcher(vocab_dir=tmpdir), enable_readline=False)

        f1 = StringIO()
        with redirect_stdout(f1):
            repl._process("Codex #newSymbol")
        out1 = f1.getvalue()
        # Codex doesn't have #newSymbol — it's unknown
        assert "unknown" in out1

        repl._process("Codex analyze: #newSymbol")

        f2 = StringIO()
        with redirect_stdout(f2):
            repl._process("Codex #")
        out2 = f2.getvalue()
        assert "#newSymbol" in out2

if __name__ == "__main__":
    test_repl_pipeline()
    test_repl_message_evolution()
    print("REPL integration tests passed")
