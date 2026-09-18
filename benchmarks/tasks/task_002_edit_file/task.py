from pathlib import Path


TASK_DIR = Path(__file__).resolve().parent

TASK_ID = "task_002_edit_file"

WORKSPACE = (
    TASK_DIR.parents[2]
    / "workspace"
    / "benchmark_task_002"
)

PROMPT = """
Work on the benchmark_task_002 project in the workspace.

Fix the broken format_result implementation.

Inspect the existing implementation and tests before making changes.

Make the smallest necessary change to the existing file.
Preserve all unrelated functionality.

Run test_calculator.py after making the change.

Use the relative workspace path benchmark_task_002 as the working
directory when running tests.

Only report completion after the implementation is fixed and all
tests pass.
"""

VALIDATION_COMMAND = "pytest -q test_calculator.py"