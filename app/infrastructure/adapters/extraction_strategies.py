"""Per-project-type file extraction strategies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractionStrategy:
    root_files: tuple[str, ...]
    directories: tuple[str, ...]
    extensions: tuple[str, ...]
    extra_patterns: tuple[str, ...] = ()


EXTRACTION_STRATEGIES: dict[str, ExtractionStrategy] = {
    "nextjs": ExtractionStrategy(
        root_files=(
            "package.json",
            "next.config.js",
            "next.config.ts",
            "next.config.mjs",     
            "middleware.ts",
            "middleware.js",
            "tsconfig.json",
            "README.md",
        ),
        directories=("app", "src", "components", "lib", "hooks", "pages", "public"),
        extensions=(".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".md"),
    ),
    "react": ExtractionStrategy(
        root_files=("package.json", "vite.config.ts", "vite.config.js", "tsconfig.json", "README.md"),
        directories=("src", "components", "hooks", "lib", "pages", "public"),
        extensions=(".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".md"),
    ),
    "fastapi": ExtractionStrategy(
        root_files=(
            "main.py",
            "app.py",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "auth.py",
            "database.py",
            "settings.py",
            "dependencies.py",
        ),
        directories=(
            "app",
            "routers",
            "services",
            "repositories",
            "models",
            "schemas",
            "core",
            "infrastructure",
            "use_cases",
            "entities",
            "ports",
        ),
        extensions=(".py", ".toml", ".txt", ".md", ".ini", ".env.example"),
    ),
    "django": ExtractionStrategy(
        root_files=(
            "manage.py",
            "settings.py",
            "views.py",
            "models.py",
            "urls.py",
            "requirements.txt",
            "README.md",
        ),
        directories=("apps", "config", "templates", "static"),
        extensions=(".py", ".html", ".txt", ".toml", ".md"),
    ),
    "express": ExtractionStrategy(
        root_files=(
            "package.json",
            "app.js",
            "server.js",
            "index.js",
            "tsconfig.json",
            "README.md",
        ),
        directories=("routes", "controllers", "middleware", "models", "services", "src", "config"),
        extensions=(".js", ".ts", ".json", ".md"),
    ),
    "nodejs": ExtractionStrategy(
        root_files=("package.json", "index.js", "server.js", "README.md"),
        directories=("src", "lib", "routes", "controllers", "config"),
        extensions=(".js", ".ts", ".json", ".md"),
    ),
    "python": ExtractionStrategy(
        root_files=(
            "main.py",
            "app.py",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "README.md",
        ),
        directories=("app", "src", "tests", "core", "lib"),
        extensions=(".py", ".toml", ".txt", ".md", ".ini"),
    ),
    "unknown": ExtractionStrategy(
        root_files=("README.md", "package.json", "requirements.txt", "pyproject.toml", "main.py"),
        directories=("src", "app", "lib"),
        extensions=(
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".json",
            ".md",
            ".toml",
            ".txt",
        ),
    ),
}

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    "venv",
    ".venv",
    "__pycache__",
    "coverage",
    ".turbo",
    "out",
}

MAX_FILES = 20
MAX_LINES_PER_FILE = 500
