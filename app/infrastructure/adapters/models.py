import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class AuthMethod(enum.Enum):
    email_password = "email_password"
    github_oauth = "github_oauth"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    github_id = Column(String(255), unique=True, nullable=True, index=True)
    github_username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    auth_methods = relationship("UserAuthMethod", back_populates="user", cascade="all, delete-orphan")

class UserAuthMethod(Base):
    __tablename__ = "user_auth_methods"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    auth_method = Column(Enum(AuthMethod), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="auth_methods")
    __table_args__ = (UniqueConstraint("user_id", "auth_method", name="unique_user_method"),)
