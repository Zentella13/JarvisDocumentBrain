from dataclasses import dataclass


@dataclass
class DocumentRecord:
    id: int | None = None
    filename: str = ""
    path: str = ""
    content: str = ""
