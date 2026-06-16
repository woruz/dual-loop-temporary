from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CreateRepositoryRequest(BaseModel):
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")


class RepositoryResponse(BaseModel):
    id: int
    user_id: int
    repo_name: str
    repo_url: str
    created_at: datetime


class RepositoryAnalysisResponse(BaseModel):
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
    project_type: str
    files_analyzed: list[str]
    created_at: datetime
