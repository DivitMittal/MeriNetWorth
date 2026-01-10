"""MeriNetWorth - Bank Account Consolidation System"""

__version__ = "1.0.0"
__author__ = "DivitMittal"

from .bank_parsers import (
    parse_idfc_statement,
    parse_equitas_statement,
    parse_bandhan_statement,
    parse_icici_statement,
    parse_indusind_statement,
    get_parser,
    PARSERS,
)

__all__ = [
    "parse_idfc_statement",
    "parse_equitas_statement",
    "parse_bandhan_statement",
    "parse_icici_statement",
    "parse_indusind_statement",
    "get_parser",
    "PARSERS",
]
