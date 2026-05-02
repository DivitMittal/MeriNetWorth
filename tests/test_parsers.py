"""Tests for individual bank parsers using real non-consolidated statements."""

from collections.abc import Callable
from pathlib import Path

import pytest

from src.process_banks import (
    parse_bandhan_statement,
    parse_equitas_statement,
    parse_icici_statement,
    parse_idfc_statement,
    parse_indusind_statement,
    parse_kotak_statement,
)

PROJECT_ROOT = Path(__file__).parent.parent


def _first_statement(folder: str, pattern: str) -> Path:
    bank_path = PROJECT_ROOT / "data" / "10.25" / "bank" / folder
    if not bank_path.exists():
        pytest.skip(f"Bank path does not exist: {bank_path}")

    files = [path for path in sorted(bank_path.glob(pattern)) if "Consolidated" not in path.name]
    if not files:
        pytest.skip(f"No matching statements in {bank_path}")
    return files[0]


def _assert_account(result: dict | None, expected_bank: str) -> None:
    assert result is not None
    assert result["bank"] == expected_bank
    assert result["account_number"]
    assert isinstance(result["holder_name"], str)
    assert isinstance(result["balance"], int | float)
    assert result["balance"] >= 0
    assert result["source_file"]


@pytest.mark.parametrize(
    ("folder", "pattern", "parser", "expected_bank"),
    [
        ("bandhan", "*.csv", parse_bandhan_statement, "Bandhan"),
        ("idfc", "*.xlsx", parse_idfc_statement, "IDFC FIRST"),
        ("equitas", "*.xlsx", parse_equitas_statement, "Equitas"),
        ("icici", "*.xlsx", parse_icici_statement, "ICICI"),
        ("kotak", "*.csv", parse_kotak_statement, "Kotak Mahindra"),
        ("indus", "*.csv", parse_indusind_statement, "IndusInd"),
    ],
)
def test_bank_parser_returns_standard_account(
    folder: str,
    pattern: str,
    parser: Callable[[Path], dict | None],
    expected_bank: str,
) -> None:
    statement = _first_statement(folder, pattern)
    _assert_account(parser(statement), expected_bank)
