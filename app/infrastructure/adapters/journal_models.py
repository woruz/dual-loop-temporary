import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.infrastructure.adapters.database import Base, engine


class GoalModel(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    goal_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")


class JournalModel(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False, index=True)
    study_hours = Column(Float, nullable=False, default=0.0)
    today_work = Column(Text, nullable=False, default="")
    learning_notes = Column(Text, nullable=False, default="")
    challenges = Column(Text, nullable=False, default="")
    tomorrow_plan = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class JournalAnalysisModel(Base):
    __tablename__ = "journal_analyses"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id"), unique=True, nullable=False, index=True)
    productivity_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    goal_alignment_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


async def create_journal_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            GoalModel.__table__,
            JournalModel.__table__,
            JournalAnalysisModel.__table__,
        ])
