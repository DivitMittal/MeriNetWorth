from pathlib import Path

from src.config import _resolve_child_path


def test_resolve_child_path_prefers_existing_variant(tmp_path: Path) -> None:
    existing = tmp_path / "Equity"
    existing.mkdir()

    assert _resolve_child_path(tmp_path, "equity", "Equity") == existing


def test_resolve_child_path_returns_preferred_spelling_when_missing(tmp_path: Path) -> None:
    assert _resolve_child_path(tmp_path, "mf", "MF") == tmp_path / "mf"
