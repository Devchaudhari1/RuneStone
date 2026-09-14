from pathlib import Path


def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    file_path = Path(path)

    if not file_path.exists():
        return f"Error: file does not exist: {path}"

    if not file_path.is_file():
        return f"Error: not a file: {path}"

    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: file is not valid UTF-8 text: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def list_directory(path: str = ".") -> str:
    """List files and directories inside a directory."""
    directory = Path(path)

    if not directory.exists():
        return f"Error: directory does not exist: {path}"

    if not directory.is_dir():
        return f"Error: not a directory: {path}"

    try:
        entries = []

        for entry in sorted(directory.iterdir()):
            if entry.is_dir():
                entries.append(f"[DIR]  {entry.name}")
            else:
                entries.append(f"[FILE] {entry.name}")

        if not entries:
            return "(empty directory)"

        return "\n".join(entries)

    except Exception as e:
        return f"Error listing directory: {e}"


def search_files(path: str, query: str) -> str:
    """Search text files recursively for a string."""
    root = Path(path)

    if not root.exists():
        return f"Error: directory does not exist: {path}"

    if not root.is_dir():
        return f"Error: not a directory: {path}"

    results = []

    try:
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip common generated/dependency directories.
            if any(
                part in {
                    ".git",
                    "__pycache__",
                    "node_modules",
                    ".venv",
                    "venv",
                }
                for part in file_path.parts
            ):
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError, OSError):
                continue

            for line_number, line in enumerate(text.splitlines(), start=1):
                if query.lower() in line.lower():
                    results.append(
                        f"{file_path}:{line_number}: {line.strip()}"
                    )

                    if len(results) >= 100:
                        return "\n".join(results)

        if not results:
            return "No matches found."

        return "\n".join(results)

    except Exception as e:
        return f"Error searching files: {e}"


def write_file(path: str, content: str) -> str:
    """Write text content to a file."""
    file_path = Path(path)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return f"Successfully wrote {len(content)} characters to {path}"

    except Exception as e:
        return f"Error writing file: {e}"