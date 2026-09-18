from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_python

from indexer.models import CodeSymbol


PYTHON_LANGUAGE = Language(tree_sitter_python.language())


def parse_python_file(file_path: str) -> list[CodeSymbol]:
    path = Path(file_path)

    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []

    parser = Parser(PYTHON_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))

    symbols = []

    def node_source(node):
        return source[node.start_byte:node.end_byte]

    def node_name(node):
        name_node = node.child_by_field_name("name")

        if name_node:
            return source[
                name_node.start_byte:name_node.end_byte
            ]

        return ""

    def visit(node, parent_class=""):
        # -------------------------
        # Class
        # -------------------------
        if node.type == "class_definition":
            name = node_name(node)

            if name:
                symbols.append(
                    CodeSymbol(
                        name=name,
                        symbol_type="class",
                        file_path=str(path),
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        source=node_source(node),
                    )
                )

            for child in node.children:
                visit(child, parent_class=name)

            return

        # -------------------------
        # Function / Method
        # -------------------------
        if node.type == "function_definition":
            name = node_name(node)

            if name:
                symbol_type = (
                    "method"
                    if parent_class
                    else "function"
                )

                symbols.append(
                    CodeSymbol(
                        name=name,
                        symbol_type=symbol_type,
                        file_path=str(path),
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        source=node_source(node),
                        parent=parent_class,
                    )
                )

            for child in node.children:
                visit(child, parent_class)

            return

        # -------------------------
        # Imports
        # -------------------------
        if node.type in {
            "import_statement",
            "import_from_statement",
        }:
            symbols.append(
                CodeSymbol(
                    name=node_source(node).strip(),
                    symbol_type="import",
                    file_path=str(path),
                    start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1,
                    source=node_source(node),
                )
            )

        for child in node.children:
            visit(child, parent_class)

    visit(tree.root_node)

    return symbols