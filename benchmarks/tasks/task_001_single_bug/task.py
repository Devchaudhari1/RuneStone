from pathlib import Path


TASK_DIR = Path(__file__).resolve().parent

TASK_ID = "task_001_single_bug"

WORKSPACE = (
    TASK_DIR.parents[2]
    / "workspace"
    / "benchmark_task"
)

PROMPT = """
Work on the benchmark_task project in the workspace.

Fix the broken addition implementation.

Inspect the relevant code and tests.
Make the necessary change.

Run the test file test_calculator.py after making the change.

Use the relative workspace path benchmark_task as the working directory
when running tests.

Only report completion after the implementation is fixed
and the tests pass.
"""

VALIDATION_COMMAND = "pytest -q test_calculator.py"