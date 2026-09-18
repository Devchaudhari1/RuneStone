from pathlib import Path

from sandbox.docker_sandbox import DockerSandbox


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent / "workspace"

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120


def _safe_directory(path: str) -> Path:
    """
    Resolve a working directory and ensure it remains
    inside the Rune Stone workspace.
    """

    requested = (WORKSPACE_ROOT / path).resolve()

    try:
        requested.relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        raise ValueError(
            "Working directory is outside the Rune Stone workspace."
        )

    return requested


def run_command(
    command: str,
    working_directory: str = ".",
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Run a command inside the Rune Stone Docker sandbox.
    """

    try:
        cwd = _safe_directory(working_directory)
    except ValueError as e:
        return f"Error: {e}"

    if not cwd.exists():
        return (
            f"Error: working directory does not exist: "
            f"{working_directory}"
        )

    if not cwd.is_dir():
        return (
            f"Error: not a directory: "
            f"{working_directory}"
        )

    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        return "Error: timeout must be an integer."

    if timeout <= 0:
        return "Error: timeout must be greater than zero."

    timeout = min(timeout, MAX_TIMEOUT)

    # Parse using Windows-compatible shlex behavior.
    import shlex

    try:
        parts = shlex.split(command, posix=True)
    except ValueError as e:
        return f"Error: invalid command syntax: {e}"

    if not parts:
        return "Error: command cannot be empty."

    # Explicit command allowlist.
    allowed_commands = {
        "python",
        "pytest",
        "pip",
        "git",
        "ruff",
        "mypy",
        "black",
    }

    executable = Path(parts[0]).name.lower()

    if executable not in allowed_commands:
        return (
            f"Error: command '{executable}' "
            "is not allowed."
        )

    sandbox = DockerSandbox()

    # DockerSandbox always starts in /workspace.
    # Convert the host working directory into
    # a workspace-relative path.
    relative_directory = cwd.relative_to(
        WORKSPACE_ROOT
    )

    # DockerSandbox currently starts at /workspace.
    # Execute commands from the requested subdirectory
    # by prepending a shell-free Python cwd change.
    #
    # For now, use Docker's `-w` directly through a
    # specialized method in the next step.
    return sandbox.run(
        parts,
        working_directory=str(relative_directory),
        timeout=timeout,
    )
