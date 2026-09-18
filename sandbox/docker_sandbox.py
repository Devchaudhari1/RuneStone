import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"

IMAGE_NAME = "runestone-sandbox:latest"

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120
MAX_OUTPUT = 12_000


class DockerSandbox:
    """
    Execute commands inside an isolated Docker container.
    """

    def __init__(
        self,
        image: str = IMAGE_NAME,
        workspace: Path = WORKSPACE_ROOT,
    ):
        self.image = image
        self.workspace = workspace.resolve()

        if not self.workspace.exists():
            raise ValueError(
                f"Workspace does not exist: {self.workspace}"
            )

        if not self.workspace.is_dir():
            raise ValueError(
                f"Workspace is not a directory: {self.workspace}"
            )

    def run(
        self,
        command: list[str],
        working_directory: str = ".",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """
        Run a command inside the Docker sandbox.
        """

        if not command:
            return "Error: command cannot be empty."

        try:
            timeout = int(timeout)
        except (TypeError, ValueError):
            return "Error: timeout must be an integer."

        if timeout <= 0:
            return "Error: timeout must be greater than zero."

        timeout = min(timeout, MAX_TIMEOUT)

        working_directory = working_directory.replace("\\", "/").strip("/")

        if ".." in Path(working_directory).parts:
            return "Error: working directory cannot escape the workspace."

        if working_directory in ("", "."):
            container_working_directory = "/workspace"
        else:
            container_working_directory = f"/workspace/{working_directory}"

        print(f"[Sandbox Working Directory] {working_directory}")
        print(f"[Container Working Directory] {container_working_directory}")

        docker_command = [
            "docker",
            "run",
            "--rm",

            # No network access.
            "--network",
            "none",

            # Read-only container filesystem.
            "--read-only",

            # Drop Linux capabilities.
            "--cap-drop",
            "ALL",

            # Resource limits.
            "--memory",
            "512m",

            "--cpus",
            "1",

            "--pids-limit",
            "128",

            # Temporary writable filesystem.
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",

            "-e",
            "PYTEST_ADDOPTS=-p no:cacheprovider",

            # Only expose Rune Stone workspace.
            "-v",
            f"{self.workspace}:/workspace",

            "-w",
            f"/workspace/{working_directory}" if working_directory != "." else "/workspace",

            self.image,
            *command,
        ]

        try:
            print("\n[Docker Command]")
            print(" ".join(docker_command))
            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        except subprocess.TimeoutExpired:
            return (
                f"Error: sandbox command timed out "
                f"after {timeout} seconds."
            )

        except FileNotFoundError:
            return (
                "Error: Docker executable was not found. "
                "Make sure Docker Desktop is running."
            )

        except Exception as e:
            return f"Error starting sandbox: {e}"

        output_parts = []

        if result.stdout:
            output_parts.append(
                f"STDOUT:\n{result.stdout}"
            )

        if result.stderr:
            output_parts.append(
                f"STDERR:\n{result.stderr}"
            )

        output_parts.append(
            f"EXIT CODE: {result.returncode}"
        )

        output = "\n\n".join(output_parts)

        if len(output) > MAX_OUTPUT:
            output = (
                output[:MAX_OUTPUT]
                + "\n\n[Output truncated]"
            )

        return output