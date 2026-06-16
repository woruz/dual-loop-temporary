from app.core.ports.auth_repo import AuthRepo
from app.core.ports.oauth_port import OAuthPort, GitHubUserInfo
from app.core.ports.password_hasher import IPasswordHasher
from app.core.ports.token_generator import ITokenGenerator
from app.core.ports.journal_repo import JournalRepositoryPort
from app.core.ports.analysis_repo import AnalysisRepositoryPort
from app.core.ports.journal_llm import JournalLLMPort, JournalAnalysisResult
