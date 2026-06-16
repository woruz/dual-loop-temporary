import datetime
import json

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, text

from app.infrastructure.adapters.database import Base, engine


class RepositoryModel(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class RepositoryAnalysisModel(Base):
    __tablename__ = "repository_analyses"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(
        Integer, ForeignKey("repositories.id"), unique=True, nullable=False, index=True
    )
    overall_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=False)
    maintainability_score = Column(Float, nullable=False)
    architecture_score = Column(Float, nullable=False)
    strengths = Column(Text, nullable=False, default="[]")
    weaknesses = Column(Text, nullable=False, default="[]")
    recommendations = Column(Text, nullable=False, default="[]")
    project_type = Column(String(50), nullable=False, default="unknown")
    files_analyzed = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


async def migrate_repository_analysis_columns(conn) -> None:
    await conn.execute(
        text(
            "ALTER TABLE repository_analyses "
            "ADD COLUMN IF NOT EXISTS project_type VARCHAR(50) NOT NULL DEFAULT 'unknown'"
        )
    )
    await conn.execute(
        text(
            "ALTER TABLE repository_analyses "
            "ADD COLUMN IF NOT EXISTS files_analyzed TEXT NOT NULL DEFAULT '[]'"
        )
    )


async def create_repository_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[RepositoryModel.__table__, RepositoryAnalysisModel.__table__],
        )
        await migrate_repository_analysis_columns(conn)
