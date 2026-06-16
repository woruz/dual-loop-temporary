import re

from app.core.entities.repository import Repository
from app.core.ports.repository_ports import RepositoryRepositoryPort

_GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$"
)


def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    match = _GITHUB_URL_PATTERN.match(repo_url.strip())
    if not match:
        raise ValueError(
            "Invalid GitHub repository URL. "
            "Expected format: https://github.com/owner/repo"
        )
    owner, repo_name = match.group(1), match.group(2)
    normalized_url = f"https://github.com/{owner}/{repo_name}.git"
    return repo_name, normalized_url


class CreateRepositoryUseCase:
    def __init__(self, repository_repo: RepositoryRepositoryPort):
        self.repository_repo = repository_repo

    async def execute(self, user_id: int, repo_url: str) -> Repository:
        repo_name, normalized_url = parse_github_repo_url(repo_url)
        return await self.repository_repo.create(
            user_id=user_id,
            repo_name=repo_name,
            repo_url=normalized_url,
        )
