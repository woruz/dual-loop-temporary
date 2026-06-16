from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    project_type: str
    files_analyzed: list[str]
    context: str

    @property
    def file_count(self) -> int:
        return len(self.files_analyzed)
