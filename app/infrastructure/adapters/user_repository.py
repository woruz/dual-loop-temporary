"""
LOCATION: app/infrastructure/adapters/user_repository.py
 
WHY HERE: This is the CONCRETE implementation of UserRepositoryPort.
It knows about SQLAlchemy and Postgres — the use-cases don't.
 
Pattern: maps between DB model (UserModel) ↔ domain entity (User).
This translation layer is called an "anti-corruption layer."
"""

from datetime import datetime 
from typing import  Optional
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select 
import os 
import base64

from app.core.entities.user import User,GithubProfile
from app.core.ports.auth_ports import UserRepositoryPort
from app.infrastructure.adapters.database import Usermodel


# ─── Token Encryption ─────────────────────────────────────────────────────────
# We encrypt GitHub access tokens at rest. Never store raw OAuth tokens in DB.
def _get_fernet()->Fernet:
       """
    Derive a Fernet key from SECRET_KEY.
    Fernet requires exactly 32 url-safe base64 bytes.
    """
       secret = os.getenv("SECRET_KEY", "fallback-insecure-key-change-me")
       #Pad/Trim to 32 then base64 encode 
       key_bytes = secret.encode()[:32].ljust(32,"b0")
       fernet_key = base64.urlsafe_b64encode(key_bytes)
       return Fernet(fernet_key)
 
def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()
 
 
def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()

##Mapping Helpers_________________________________________________________________________
def _model_to_entity(model:User)-> User:
      """Convert DB row → domain entity. Decrypts the access token."""
      return User(
             id=model.id,
        github_id=model.github_id,
        username=model.github_username,
        email=model.email,
        github_url=model.github_url,
        access_token=decrypt_token(model.access_token),
        created_at=model.created_at,
        updated_at=model.updated_at,
           
      )


###Repository_______________________________________________________________________

class SQLAlchemyUserRepository(UserRepositoryPort):
    """
    Postgres implementation of UserRepositoryPort using async SQLAlchemy.
    Injected into use-cases via dependencies.py.
    """
    def __init__(self,db:AsyncSession):
        self.db = db
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)

        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
    async def get_by_github_id(self, github_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.github_id == github_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
 
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
 
    async def create(self, profile: GithubProfile, access_token: str) -> User:
        model = User(
            github_id=profile.github_id,
            username=profile.login,
            email=profile.email,
            name=profile.name,
            avatar_url=profile.avatar_url,
            bio=profile.bio,
            github_url=profile.html_url,
            access_token=encrypt_token(access_token),  # encrypt before storing
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(model)
        await self.db.flush()  # Get the auto-generated ID without committing
        await self.db.refresh(model)
        return _model_to_entity(model)
 
    async def update(self, user: User) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"User {user.id} not found for update")
 
        model.name = user.name
        model.email = user.email
        model.avatar_url = user.avatar_url
        model.bio = user.bio
        model.is_active = user.is_active
        model.updated_at = datetime.utcnow()
 
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)
 
    async def update_access_token(self, user_id: int, new_token: str) -> None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.access_token = encrypt_token(new_token)
            model.updated_at = datetime.utcnow()
            await self.db.flush()