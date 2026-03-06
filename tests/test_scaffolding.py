"""
tests/test_scaffolding.py

Story 1.1 — AC validation:
  AC-1: Required files and directories exist.
  AC-4: engine/ modules do not import pygame, renderer, or ai.
  AC-5: .gitignore is present.

Headless — never imports pygame.
"""

import ast
import os
import pathlib
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).parent.parent  # workspace root


def _exists(rel: str) -> bool:
    return (ROOT / rel).exists()


# ---------------------------------------------------------------------------
# AC-1: Directory and file skeleton
# ---------------------------------------------------------------------------

REQUIRED_FILES = [
    "main.py",
    "requirements.txt",
    "engine/__init__.py",
    "renderer/__init__.py",
    "editor/__init__.py",
    "ai/__init__.py",
    "ui/__init__.py",
    "tests/__init__.py",
]

REQUIRED_DIRS = [
    "engine",
    "renderer",
    "editor",
    "ai",
    "ui",
    "tests",
    "data/levels",
    "data/brains",
]


@pytest.mark.parametrize("rel_path", REQUIRED_FILES)
def test_required_file_exists(rel_path: str) -> None:
    assert _exists(rel_path), f"Missing required file: {rel_path}"


@pytest.mark.parametrize("rel_dir", REQUIRED_DIRS)
def test_required_directory_exists(rel_dir: str) -> None:
    assert (ROOT / rel_dir).is_dir(), f"Missing required directory: {rel_dir}"


# ---------------------------------------------------------------------------
# AC-2: requirements.txt contains expected dependencies
# ---------------------------------------------------------------------------

def test_requirements_contains_pygame() -> None:
    req = (ROOT / "requirements.txt").read_text()
    assert "pygame" in req, "requirements.txt must declare pygame"


def test_requirements_contains_numpy() -> None:
    req = (ROOT / "requirements.txt").read_text()
    assert "numpy" in req, "requirements.txt must declare numpy"


# ---------------------------------------------------------------------------
# AC-4: engine/ modules must NOT import pygame, renderer, or ai
# ---------------------------------------------------------------------------

FORBIDDEN_IMPORTS = {"pygame", "renderer", "ai"}


def _forbidden_imports_in_file(path: pathlib.Path) -> list[str]:
    """Return list of forbidden module names imported by the given Python file."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        pytest.fail(f"SyntaxError in {path}")
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_mod = alias.name.split(".")[0]
                if root_mod in FORBIDDEN_IMPORTS:
                    bad.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_mod = node.module.split(".")[0]
                if root_mod in FORBIDDEN_IMPORTS:
                    bad.append(node.module)
    return bad


def _engine_python_files() -> list[pathlib.Path]:
    return list((ROOT / "engine").rglob("*.py"))


@pytest.mark.parametrize("py_file", _engine_python_files())
def test_engine_module_no_forbidden_imports(py_file: pathlib.Path) -> None:
    bad = _forbidden_imports_in_file(py_file)
    assert not bad, (
        f"{py_file.relative_to(ROOT)} must not import {FORBIDDEN_IMPORTS}; "
        f"found: {bad}"
    )


# ---------------------------------------------------------------------------
# AC-5: .gitignore is present
# ---------------------------------------------------------------------------

def test_gitignore_exists() -> None:
    assert _exists(".gitignore"), ".gitignore must exist at project root"


def test_gitignore_covers_venv() -> None:
    gi = (ROOT / ".gitignore").read_text()
    assert ".venv" in gi or "venv" in gi, ".gitignore must exclude virtual environment directories"


def test_gitignore_covers_pycache() -> None:
    gi = (ROOT / ".gitignore").read_text()
    assert "__pycache__" in gi, ".gitignore must exclude __pycache__/"
