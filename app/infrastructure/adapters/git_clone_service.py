import logging
import os
import subprocess
import shutil
import tempfile

from app.core.ports.repository_ports import GitClonePort

logger = logging.getLogger(__name__)


class GitCloneService(GitClonePort):
    def __init__(self, clone_timeout_seconds: int = 120):
        self.clone_timeout_seconds = clone_timeout_seconds

    async def clone(self, repo_url: str) -> str:
        temp_dir = tempfile.mkdtemp(prefix="repo_analysis_")
        logger.info("[RepositoryAnalysis] Clone started: %s -> %s", repo_url, temp_dir)

        try:
            await self._verify_git_exists()
            await self._clone_repo(repo_url=repo_url, temp_dir=temp_dir)
        except Exception as exc:
            await self.cleanup(temp_dir)
            logger.error("[RepositoryAnalysis] Clone failed: %s", exc)
            raise

        logger.info("[RepositoryAnalysis] Clone completed: %s", temp_dir)
        return temp_dir

    async def _verify_git_exists(self) -> None:
        def _check() -> None:
            try:
                subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "Git is not installed or not available in PATH. "
                    "Install Git and ensure the 'git' command works."
                ) from exc
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                raise RuntimeError(f"Git is installed but not usable: {stderr}") from exc

        import asyncio

        await asyncio.to_thread(_check)

    async def _clone_repo(self, repo_url: str, temp_dir: str) -> None:
        def _run() -> None:
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, temp_dir],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.clone_timeout_seconds,
                )
            except FileNotFoundError as exc:
                # Shouldn't happen due to precheck, but keep error clear.
                raise RuntimeError(
                    "Git is not installed or not available in PATH."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Git clone timed out") from exc
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                raise RuntimeError(f"Failed to clone repository: {stderr}") from exc

        import asyncio

        await asyncio.to_thread(_run)

    async def cleanup(self, repo_path: str) -> None:
        if repo_path and os.path.isdir(repo_path):
            import asyncio

            await asyncio.to_thread(shutil.rmtree, repo_path, ignore_errors=True)
            logger.info("Cleaned up temporary repository path: %s", repo_path)
