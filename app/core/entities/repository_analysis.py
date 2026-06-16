from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RepositoryAnalysis:
    id: int
    repository_id: int
    overall_score: float
    security_score: float
    performance_score: float
    maintainability_score: float
    architecture_score: float
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    project_type: str = "unknown"
    files_analyzed: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
