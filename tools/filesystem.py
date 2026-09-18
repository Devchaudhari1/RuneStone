from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent / "workspace"


def _safe_path(path: str) -> Path:
    requested = (WORKSPACE_ROOT / path).resolve()

    try:
        requested.relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        raise ValueError("Path is outside the Rune Stone workspace.")

    return requested


def read_file(path: str) -> str:
    """Read a text file inside the Rune Stone workspace."""
    try:
        file_path = _safe_path(path)
    except ValueError as e:
        return f"Error: {e}"

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
    """List files and directories inside the Rune Stone workspace."""
    try:
        directory = _safe_path(path)
    except ValueError as e:
        return f"Error: {e}"

    if not directory.exists():
        return f"Error: directory does not exist: {path}"

    if not directory.is_dir():
        return f"Error: not a directory: {path}"

    try:
        entries = []

        for item in sorted(directory.iterdir()):
            if item.is_dir():
                entries.append(f"[DIR]  {item.name}")
            else:
                entries.append(f"[FILE] {item.name}")

        return "\n".join(entries) if entries else "(empty directory)"

    except Exception as e:
        return f"Error listing directory: {e}"


def search_files(path: str, query: str) -> str:
    """Search text files recursively inside the Rune Stone workspace."""
    try:
        root = _safe_path(path)
    except ValueError as e:
        return f"Error: {e}"

    if not root.exists():
        return f"Error: path does not exist: {path}"

    matches = []

    ignored = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
    }

    try:
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            if any(part in ignored for part in file_path.parts):
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(text.splitlines(), start=1):
                if query.lower() in line.lower():
                    relative = file_path.relative_to(WORKSPACE_ROOT)
                    matches.append(
                        f"{relative}:{line_number}: {line.strip()}"
                    )

                    if len(matches) >= 100:
                        return "\n".join(matches)

        return "\n".join(matches) if matches else "No matches found."

    except Exception as e:
        return f"Error searching files: {e}"


def write_file(path: str, content: str) -> str:
    """Write a text file inside the Rune Stone workspace."""
    try:
        file_path = _safe_path(path)
    except ValueError as e:
        return f"Error: {e}"

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return (
            f"Successfully wrote "
            f"{len(content)} characters to {path}"
        )

    except Exception as e:
        return f"Error writing file: {e}"

def edit_file(
    path: str,
    old_text: str,
    new_text: str,
    start_line: int | None = None,
    start_column: int | None = None,
    end_line: int | None = None,
    end_column: int | None = None,
) -> str:
    """
    Make a precise edit to a workspace file.

    Without a source range:
        old_text must occur exactly once.

    With a source range:
        the text at that exact range must match old_text.

    Line numbers are 1-based.
    Columns are 0-based.
    End position is exclusive.
    """

    file_path = _safe_path(path)

    if not file_path.exists():
        return f"Error: file does not exist: {path}"

    if not file_path.is_file():
        return f"Error: path is not a file: {path}"

    if old_text == new_text:
        return "Error: old_text and new_text are identical; no edit needed."

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: file is not valid UTF-8 text: {path}"

    range_values = (
        start_line,
        start_column,
        end_line,
        end_column,
    )

    range_supplied = any(value is not None for value in range_values)

    # ---------------------------------------------------------
    # MODE 1: exact text replacement
    # ---------------------------------------------------------

    if not range_supplied:
        occurrences = content.count(old_text)

        if occurrences == 0:
            return "Error: old_text was not found in the file."

        if occurrences > 1:
            matches = []

            search_start = 0

            while True:
                index = content.find(old_text, search_start)

                if index == -1:
                    break

                line = content.count("\n", 0, index) + 1

                last_newline = content.rfind("\n", 0, index)

                if last_newline == -1:
                    column = index
                else:
                    column = index - last_newline - 1

                matches.append(f"{line}:{column}")

                search_start = index + 1

            return (
                f"Error: old_text occurs {occurrences} times.\n"
                f"Matches: {', '.join(matches)}\n"
                "Provide start_line, start_column, end_line, "
                "and end_column to select the intended occurrence."
            )

        new_content = content.replace(old_text, new_text, 1)

        try:
            file_path.write_text(new_content, encoding="utf-8")
        except OSError as e:
            return f"Error writing file: {e}"

        return f"Successfully edited {path}."

    # ---------------------------------------------------------
    # MODE 2: positional replacement
    # ---------------------------------------------------------

    if any(value is None for value in range_values):
        return (
            "Error: start_line, start_column, end_line, and "
            "end_column must all be provided together."
        )

    assert (
        start_line is not None
        and start_column is not None
        and end_line is not None
        and end_column is not None
    )

    if start_line < 1 or end_line < 1:
        return "Error: line numbers are 1-based and must be >= 1."

    if start_column < 0 or end_column < 0:
        return "Error: columns must be >= 0."

    if (start_line, start_column) > (end_line, end_column):
        return "Error: start position must not be after end position."

    lines = content.splitlines(keepends=True)

    if start_line > len(lines):
        return f"Error: start_line {start_line} is outside the file."

    if end_line > len(lines):
        return f"Error: end_line {end_line} is outside the file."

    start_offset = (
        sum(len(line) for line in lines[:start_line - 1])
        + start_column
    )

    end_offset = (
        sum(len(line) for line in lines[:end_line - 1])
        + end_column
    )

    if start_offset > len(content):
        return "Error: start position is outside the file."

    if end_offset > len(content):
        return "Error: end position is outside the file."

    selected_text = content[start_offset:end_offset]

    if selected_text != old_text:
        return (
            "Error: text at the specified range does not match old_text.\n"
            f"Expected: {old_text!r}\n"
            f"Found:    {selected_text!r}"
        )

    new_content = (
        content[:start_offset]
        + new_text
        + content[end_offset:]
    )

    try:
        file_path.write_text(new_content, encoding="utf-8")
    except OSError as e:
        return f"Error writing file: {e}"

    return (
        f"Successfully edited {path} "
        f"at {start_line}:{start_column}-"
        f"{end_line}:{end_column}."
    )