import asyncio
import logging
from pathlib import Path

from app.core.entities.extraction_result import ExtractionResult
from app.core.ports.repository_ports import FileExtractionPort
from app.infrastructure.adapters.extraction_strategies import (
    EXTRACTION_STRATEGIES,
    IGNORED_DIRS,
    MAX_FILES,
    MAX_LINES_PER_FILE,
)
from app.infrastructure.adapters.project_detection_service import ProjectDetectionService

logger = logging.getLogger(__name__)


class FileExtractionService(FileExtractionPort):
    def __init__(self, detector: ProjectDetectionService | None = None):
        self.detector = detector or ProjectDetectionService()

    async def extract(self, repo_path: str) -> ExtractionResult:
        return await asyncio.to_thread(self._extract_sync, repo_path)

    async def extract_context(self, repo_path: str) -> str:
        """Backward-compatible helper returning only the context string."""
        result = await self.extract(repo_path)
        return result.context

    def _extract_sync(self, repo_path: str) -> ExtractionResult:
        root = Path(repo_path)
        if not root.is_dir():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        project_type = self.detector._detect_sync(repo_path)
        strategy = EXTRACTION_STRATEGIES.get(project_type, EXTRACTION_STRATEGIES["unknown"])

        candidates = self._collect_candidates(root, strategy)
        selected = self._select_files(candidates)
        contents = self._read_files(root, selected)

        if not contents:
            logger.warning(
                "[RepositoryAnalysis] No strategy files found for project_type=%s",
                project_type,
            )
            return ExtractionResult(
                project_type=project_type,
                files_analyzed=[],
                context="No target files found in repository.",
            )

        sections = [
            f"=== FILE: {relative_path} ===\n{content}"
            for relative_path, content in sorted(contents.items())
        ]
        context = "\n\n".join(sections)

        logger.info("[RepositoryAnalysis] Project Type: %s", project_type)
        logger.info("[RepositoryAnalysis] Files Extracted: %d", len(contents))
        for relative_path in sorted(contents.keys()):
            logger.info("[RepositoryAnalysis]   - %s", relative_path)
        logger.info("[RepositoryAnalysis] Context Length: %d", len(context))

        return ExtractionResult(
            project_type=project_type,
            files_analyzed=sorted(contents.keys()),
            context=context,
        )

    def _collect_candidates(self, root: Path, strategy) -> list[Path]:
        candidates: list[Path] = []

        for name in strategy.root_files:
            direct = root / name
            if direct.is_file() and self._is_allowed_path(direct, root):
                candidates.append(direct)

        for directory in strategy.directories:
            dir_path = root / directory
            if not dir_path.is_dir():
                continue
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                if not self._is_allowed_path(file_path, root):
                    continue
                if file_path.suffix not in strategy.extensions:
                    continue
                candidates.append(file_path)

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if not self._is_allowed_path(file_path, root):
                continue
            if file_path.name in strategy.root_files:
                continue
            if file_path.suffix not in strategy.extensions:
                continue
            if any(part in strategy.directories for part in file_path.relative_to(root).parts[:-1]):
                continue
            candidates.append(file_path)

        unique: dict[str, Path] = {}
        for path in candidates:
            unique[path.relative_to(root).as_posix()] = path
        return list(unique.values())

    def _select_files(self, candidates: list[Path]) -> list[Path]:
        def priority(path: Path) -> tuple[int, str]:
            name = path.name.lower()
            if name == "package.json":
                return (0, path.as_posix())
            if name in {"main.py", "app.py", "manage.py", "server.js", "index.js"}:
                return (1, path.as_posix())
            if name.startswith("next.config"):
                return (2, path.as_posix())
            if name in {"requirements.txt", "pyproject.toml", "settings.py"}:
                return (3, path.as_posix())
            if "test" in path.as_posix().lower():
                return (9, path.as_posix())
            return (5, path.as_posix())

        return sorted(candidates, key=priority)[:MAX_FILES]

    def _read_files(self, root: Path, selected: list[Path]) -> dict[str, str]:
        contents: dict[str, str] = {}
        for file_path in selected:
            relative_path = file_path.relative_to(root).as_posix()
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError as exc:
                logger.warning("Skipping unreadable file %s: %s", relative_path, exc)
                continue

            if len(lines) > MAX_LINES_PER_FILE:
                lines = lines[:MAX_LINES_PER_FILE] + ["... [truncated]"]

            contents[relative_path] = "\n".join(lines)
        return contents

    def _is_allowed_path(self, file_path: Path, root: Path) -> bool:
        relative_parts = file_path.relative_to(root).parts
        return not any(part in IGNORED_DIRS or part.startswith(".") for part in relative_parts[:-1])
