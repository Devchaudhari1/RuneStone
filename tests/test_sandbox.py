import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.terminal import run_command

print("=== PWD ===")
print(run_command("python -c \"import os; print(os.getcwd())\""))

print("=== WORKSPACE ===")
print(run_command("python -c \"import os; print(os.listdir('workspace'))\""))

print("=== WRITE ===")
print(
    run_command(
        "python -c \"from pathlib import Path; Path('workspace/sandbox_test.txt').write_text('hello')\""
    )
)