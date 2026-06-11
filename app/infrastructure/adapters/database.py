import datetime 
import os 
# Import DateTime (capitalized) from SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, Text, BigInteger, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# ─── Async Engine Setup ───────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Fail early and clearly if the environment variable isn't loaded
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is missing or empty! "
        "Make sure your .env file is loaded before importing database.py."
    )

# asyncpg driver for async Postgres. Convert postgres:// → postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true", # ← FIXED: changed 'echos' to 'echo'
    pool_size=10, 
    max_overflow=20,
    pool_pre_ping=True, 
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


## Base & Model ______________________________________________
class Base(DeclarativeBase):
    pass

class Usermodel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    github_url = Column(Text, nullable=False, default="")
    
    # FIXED: Changed 'datetime' type to SQLAlchemy's 'DateTime'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  
    is_active = Column(Boolean, default=True, nullable=False)  


## DB Session Dependency _______________________________________________
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise 
        finally:
            await session.close()

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)