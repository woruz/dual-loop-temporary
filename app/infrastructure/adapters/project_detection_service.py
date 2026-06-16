import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx"}


class ProjectDetectionService:
    async def detect(self, repo_path: str) -> str:
        return await asyncio.to_thread(self._detect_sync, repo_path)

    def _detect_sync(self, repo_path: str) -> str:
        root = Path(repo_path)
        if not root.is_dir():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        package_json = self._read_json_if_exists(root / "package.json")
        requirements = self._read_text_if_exists(root / "requirements.txt")
        pyproject = self._read_text_if_exists(root / "pyproject.toml")

        if (root / "manage.py").is_file():
            project_type = "django"
        elif self._is_nextjs(root, package_json):
            project_type = "nextjs"
        elif self._is_fastapi(root, requirements, pyproject):
            project_type = "fastapi"
        elif self._has_package_dependency(package_json, "express"):
            project_type = "express"
        elif self._has_package_dependency(package_json, "react"):
            project_type = "react"
        elif package_json is not None:
            project_type = "nodejs"
        elif requirements or pyproject or self._has_python_files(root):
            project_type = "python"
        else:
            project_type = "unknown"

        logger.info("[RepositoryAnalysis] Project type detected: %s", project_type)
        return project_type

    def _is_nextjs(self, root: Path, package_json: dict | None) -> bool:
        if any(
            (root / name).is_file()
            for name in ("next.config.js", "next.config.ts", "next.config.mjs")
        ):
            return True
        return self._has_package_dependency(package_json, "next")

    def _is_fastapi(
        self, root: Path, requirements: str | None, pyproject: str | None
    ) -> bool:
        deps_text = " ".join(filter(None, [requirements, pyproject])).lower()
        if "fastapi" in deps_text:
            return True

        for file_path in self._iter_source_files(root, limit=40):
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            if "from fastapi" in content or "import fastapi" in content:
                return True
        return False

    def _has_package_dependency(self, package_json: dict | None, name: str) -> bool:
        if not package_json:
            return False
        deps = package_json.get("dependencies", {}) or {}
        dev_deps = package_json.get("devDependencies", {}) or {}
        return name in deps or name in dev_deps

    def _has_python_files(self, root: Path) -> bool:
        return any(True for _ in self._iter_source_files(root, limit=1, extensions={".py"}))

    def _iter_source_files(
        self, root: Path, limit: int, extensions: set[str] | None = None
    ):
        extensions = extensions or SOURCE_EXTENSIONS
        count = 0
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue
            if any(part in {"node_modules", ".git", "venv", ".venv", "__pycache__"} for part in file_path.parts):
                continue
            yield file_path
            count += 1
            if count >= limit:
                break

    def _read_json_if_exists(self, path: Path) -> dict | None:
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _read_text_if_exists(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
