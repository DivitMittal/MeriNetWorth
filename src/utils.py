"""Shared utility functions for MeriNetWorth parsers."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def clean_amount(value: Any) -> float:
    """Clean and convert amount values to float.

    Handles various formats including:
    - ₹ prefix (Indian Rupee symbol)
    - Comma separators
    - INR suffix

    Args:
        value: Raw value to clean (can be int, float, str, or NaN)

    Returns:
        Cleaned float value, or 0.0 if conversion fails
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("₹", "").replace(",", "").replace("INR", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def save_json(data: dict, output_path: Path, description: str = "") -> Path:
    """Save data to JSON file with consistent formatting.

    Args:
        data: Dictionary to save
        output_path: Path to output file
        description: Optional description for success message (e.g., "Fixed income")

    Returns:
        Path to the saved file
    """
    # Add generation timestamp if not present
    if "generated_at" not in data:
        data = {"generated_at": datetime.now().isoformat(), **data}

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    label = f"{description} " if description else ""
    print(f"✅ {label}JSON saved: {output_path}")
    return output_path
