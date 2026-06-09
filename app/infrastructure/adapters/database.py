"""
LOCATION: app/infrastructure/adapters/database.py
 
WHY HERE: Infrastructure holds all the "dirty" external concerns — DB, HTTP clients,
file systems. This file is the SQLAlchemy setup + the User DB model.
 
The DB model is SEPARATE from the domain entity (app/core/entities/user.py).
They look similar but serve different masters:
  - Domain entity: represents business logic
  - DB model: represents how data is stored in Postgres
"""

from datetime import datetime 
from sqlalchemy import (Column,Integer,String,Boolean,Datetime,Text,BigInteger)
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os 

 
# ─── Async Engine Setup ───────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL","")


# asyncpg driver for async Postgres. Convert postgres:// → postgresql+asyncpg://
if DATABASE_URL.startswith("postfresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://",1)
elif DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echos = os.getenv("DEBUG","False").lower() == "true", ##SQL Logging in dev only 
    pool_size = 10, 
    max_overflow = 20,
    pool_pre_ping = True, ##Check connection health before using from pool 
    pool_recycle = 3600,

)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False

)


##Base & Model ______________________________________________
class Base(DeclarativeBase):
    pass

class Usermodel(Base):
    __tablename__  = "users"
    

    id = Column(Integer,primary_key=True,index=True)
    github_id = Column(BigInteger,unique=True,nullable=False,index=True)
    username = Column(String(255),unique=True,nullable=False,index=True)
    email = Column(String(255),unique=True,nullable=False,index=True)
    github_url = Column(Text,nullable=False,default="")


##Store the github access token(see encrypted and decrpyted)
access_token = Column(Text,nullable=False)
is_active = Column(Boolean,defaullt=True,nullable=False)
created_at = Column(Boolean,default=datetime.utcnow,nullable=False)
updated_at = Column(Boolean,default=datetime.utcnow,nullable=False)


##DB Session Dependency _______________________________________________
async def get_db()-> AsyncSession:
    """
    FastAPI dependency. Yields a DB session, always closes it after the request.
    Usage in router: db: AsyncSession = Depends(get_db)
    """
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
     """Call this on app startup to create tables if they don't exist."""
     async with engine.begin() as conn:
         await conn.run_sync(Base.metadata.create_all)