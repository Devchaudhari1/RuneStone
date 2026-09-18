from dataclasses import dataclass


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    signature: str = ""
    source: str = ""
    parent: str = ""


@dataclass
class CodeChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str = ""
    symbol_type: str = ""
    parent: str = ""