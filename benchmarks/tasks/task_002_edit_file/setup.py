from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[3]

SOURCE = (
    PROJECT_ROOT
    / "benchmarks"
    / "tasks"
    / "task_002_edit_file"
    / "project"
)

TARGET = (
    PROJECT_ROOT
    / "workspace"
    / "benchmark_task_002"
)


def setup():
    if TARGET.exists():
        shutil.rmtree(TARGET)

    shutil.copytree(SOURCE, TARGET)

    print(
        f"Benchmark workspace prepared at: {TARGET}"
    )


if __name__ == "__main__":
    setup()