"""Integration test for the REPL pipeline."""

import sys
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from repl import REPL

def test_repl_pipeline():
    repl = REPL()
    
    # We want to capture the output of processing a command
    # The REPL._process method prints to stdout
    
    command = "@guardian"
    
    f = StringIO()
    with redirect_stdout(f):
        repl._process(command)
    
    output = f.getvalue()
    assert "→" in output
    assert "#fire" in output

def test_repl_message_evolution():
    repl = REPL()
    
    # 1. Check @guardian doesn't know #stillness
    f1 = StringIO()
    with redirect_stdout(f1):
        repl._process("@guardian.#stillness")
    out1 = f1.getvalue()
    # Depending on dispatcher logic, it might say "collision" or similar
    # My current dispatcher says "... reaches for ... boundary collision" if not known
    assert "reaches for" in out1

    # 2. Teach @guardian #stillness via message
    repl._process("@guardian sendVision: #stillness")
    
    # 3. Verify @guardian now knows #stillness
    f2 = StringIO()
    with redirect_stdout(f2):
        repl._process("@guardian.#")
    out2 = f2.getvalue()
    assert "#stillness" in out2

if __name__ == "__main__":
    test_repl_pipeline()
    test_repl_message_evolution()
    print("✓ REPL integration tests passed")
