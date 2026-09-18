import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import RuneStoneAgent


TASKS_DIR = PROJECT_ROOT / "benchmarks" / "tasks"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"


def load_task(task_dir: Path):
    task_file = task_dir / "task.py"

    if not task_file.exists():
        raise FileNotFoundError(
            f"Task definition not found: {task_file}"
        )

    module_name = f"benchmark_{task_dir.name}"

    spec = importlib.util.spec_from_file_location(
        module_name,
        task_file,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load task: {task_file}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def run_setup(task):
    setup_script = task.TASK_DIR / "setup.py"

    if not setup_script.exists():
        return

    subprocess.run(
        [sys.executable, str(setup_script)],
        cwd=PROJECT_ROOT,
        check=True,
    )


def run_validation(task):
    start = time.perf_counter()

    result = subprocess.run(
        task.VALIDATION_COMMAND,
        cwd=task.WORKSPACE,
        shell=True,
        capture_output=True,
        text=True,
    )

    elapsed = time.perf_counter() - start

    return {
        "command": task.VALIDATION_COMMAND,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_seconds": elapsed,
        "passed": result.returncode == 0,
    }


def run_task(task_dir: Path):
    task = load_task(task_dir)

    print("\n==============================")
    print(f"Running {task.TASK_ID}")
    print("==============================")

    run_setup(task)

    agent = RuneStoneAgent()

    start = time.perf_counter()

    try:
        final_response = agent.run(task.PROMPT)
        agent_exception = None
    except Exception as exc:
        final_response = ""
        agent_exception = repr(exc)

    agent_duration = time.perf_counter() - start

    validation = run_validation(task)

    success = validation["passed"]

    agent_validation_passed = (
        agent.metrics["tool_calls"] > 0
        and any(
            tool in {
                "run_command",
            }
            for tool in agent.metrics["tools"]
        )
        and validation["passed"]
    )

    failure_reason = None

    if agent_exception:
        failure_reason = f"agent_exception: {agent_exception}"
    elif not validation["passed"]:
        failure_reason = "independent_validation_failed"
    elif not agent_validation_passed:
        failure_reason = "agent_did_not_validate"

    result = {
        "task_id": task.TASK_ID,

        "success": success,
        "agent_validation_passed": agent_validation_passed,

        "agent_duration_seconds": round(
            agent_duration,
            3,
        ),

        "validation": validation,

        "metrics": agent.metrics,

        "failure_reason": failure_reason,

        "final_response": final_response,
    }

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        RESULTS_DIR
        / f"{task.TASK_ID}.json"
    )

    output_file.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n------------------------------")
    print(f"Task:       {task.TASK_ID}")
    print(f"Success:    {success}")
    print(
        f"Agent validation: "
        f"{agent_validation_passed}"
    )
    print(
        f"Iterations: "
        f"{agent.metrics['iterations']}"
    )
    print(
        f"Tool calls: "
        f"{agent.metrics['tool_calls']}"
    )
    print(
        f"Duration:   "
        f"{agent_duration:.2f}s"
    )
    print(
        f"Prompt:     "
        f"{agent.metrics['prompt_tokens']}"
    )
    print(
        f"Completion: "
        f"{agent.metrics['completion_tokens']}"
    )
    print(
        f"Tokens:     "
        f"{agent.metrics['total_tokens']}"
    )

    if failure_reason:
        print(f"Failure:    {failure_reason}")

    print(f"Result:     {output_file}")

    return result


def discover_tasks():
    tasks = []

    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir():
            continue

        if not (task_dir / "task.py").exists():
            continue

        tasks.append(task_dir)

    return tasks


def run_benchmark():
    task_dirs = discover_tasks()

    if not task_dirs:
        print("No benchmark tasks found.")
        return

    results = []

    for task_dir in task_dirs:
        try:
            result = run_task(task_dir)
        except Exception as exc:
            print(
                f"\nERROR running "
                f"{task_dir.name}: {exc}"
            )

            result = {
                "task_id": task_dir.name,
                "success": False,
                "agent_validation_passed": False,
                "failure_reason": repr(exc),
            }

        results.append(result)

    successful = sum(
        bool(result.get("success"))
        for result in results
    )

    agent_validated = sum(
        bool(result.get("agent_validation_passed"))
        for result in results
    )

    count = len(results)

    avg_iterations = sum(
        result.get("metrics", {}).get(
            "iterations",
            0,
        )
        for result in results
    ) / count

    avg_tool_calls = sum(
        result.get("metrics", {}).get(
            "tool_calls",
            0,
        )
        for result in results
    ) / count

    avg_duration = sum(
        result.get(
            "agent_duration_seconds",
            0,
        )
        for result in results
    ) / count

    avg_tokens = sum(
        result.get("metrics", {}).get(
            "total_tokens",
            0,
        )
        for result in results
    ) / count

    summary = {
        "tasks": count,
        "successful": successful,
        "success_rate": round(
            successful / count,
            4,
        ),
        "agent_validation_passed": agent_validated,
        "agent_validation_rate": round(
            agent_validated / count,
            4,
        ),
        "average_iterations": round(
            avg_iterations,
            3,
        ),
        "average_tool_calls": round(
            avg_tool_calls,
            3,
        ),
        "average_duration_seconds": round(
            avg_duration,
            3,
        ),
        "average_tokens": round(
            avg_tokens,
            3,
        ),
    }

    output = {
        "summary": summary,
        "tasks": results,
    }

    output_file = (
        RESULTS_DIR
        / "agent_benchmark.json"
    )

    output_file.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n======================================")
    print("RuneStone Agent Benchmark")
    print("======================================")
    print(f"Tasks:              {count}")
    print(f"Successful:         {successful}")
    print(
        f"Success rate:       "
        f"{summary['success_rate']:.1%}"
    )
    print(
        f"Agent validation:   "
        f"{agent_validated}/{count}"
    )
    print(
        f"Avg iterations:     "
        f"{avg_iterations:.2f}"
    )
    print(
        f"Avg tool calls:     "
        f"{avg_tool_calls:.2f}"
    )
    print(
        f"Avg latency:        "
        f"{avg_duration:.2f}s"
    )
    print(
        f"Avg tokens/task:    "
        f"{avg_tokens:.0f}"
    )
    print(
        f"\nResults saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":
    run_benchmark()