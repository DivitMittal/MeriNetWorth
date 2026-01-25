"""Parsers for real estate and other assets."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import (
    OTHER_ASSETS_FILE_PATH,
    OUTPUT_PATH,
    REAL_ESTATE_FILE_PATH,
)
from .utils import clean_amount, save_json


def parse_asset_file(file_path: Path, asset_type: str) -> Optional[dict]:
    """Parse an asset CSV file with Name, Current Value columns.

    Args:
        file_path: Path to the asset CSV file
        asset_type: Type of asset (e.g., 'real_estate', 'other')

    Returns:
        Dict with asset info or None on error
    """
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        assets = []
        total_value = 0.0

        for _, row in df.iterrows():
            name = row.get("Name", "")
            if pd.isna(name) or str(name).strip() == "":
                continue

            value = clean_amount(row.get("Current Value", 0))

            asset = {
                "name": str(name).strip(),
                "value": value,
            }
            assets.append(asset)
            total_value += value

        return {
            "source_file": file_path.name,
            "asset_type": asset_type,
            "assets": assets,
            "total_value": total_value,
            "asset_count": len(assets),
        }

    except Exception as e:
        print(f"Error parsing {asset_type} file {file_path.name}: {e}")
        return None


def process_real_estate() -> dict:
    """Process real estate assets from CSV file.

    Returns:
        Dict containing real estate data
    """
    if not REAL_ESTATE_FILE_PATH.exists():
        print(f"Real estate file not found: {REAL_ESTATE_FILE_PATH}")
        return {
            "generated_at": datetime.now().isoformat(),
            "assets": [],
            "total_value": 0.0,
        }

    print("\n🏠 Processing Real Estate...")

    result = parse_asset_file(REAL_ESTATE_FILE_PATH, "real_estate")
    if result:
        print(f"  ✓ {REAL_ESTATE_FILE_PATH.name}: ₹{result['total_value']:,.2f}")
        for asset in result["assets"]:
            if asset["value"] > 0:
                print(f"    - {asset['name']}: ₹{asset['value']:,.2f}")

        return {
            "generated_at": datetime.now().isoformat(),
            "assets": result["assets"],
            "total_value": result["total_value"],
            "source_file": result["source_file"],
        }

    return {
        "generated_at": datetime.now().isoformat(),
        "assets": [],
        "total_value": 0.0,
    }


def process_other_assets() -> dict:
    """Process other assets from CSV file.

    Returns:
        Dict containing other assets data
    """
    if not OTHER_ASSETS_FILE_PATH.exists():
        print(f"Other assets file not found: {OTHER_ASSETS_FILE_PATH}")
        return {
            "generated_at": datetime.now().isoformat(),
            "assets": [],
            "total_value": 0.0,
        }

    print("\n📦 Processing Other Assets...")

    result = parse_asset_file(OTHER_ASSETS_FILE_PATH, "other")
    if result:
        print(f"  ✓ {OTHER_ASSETS_FILE_PATH.name}: ₹{result['total_value']:,.2f}")
        for asset in result["assets"]:
            if asset["value"] > 0:
                print(f"    - {asset['name']}: ₹{asset['value']:,.2f}")

        return {
            "generated_at": datetime.now().isoformat(),
            "assets": result["assets"],
            "total_value": result["total_value"],
            "source_file": result["source_file"],
        }

    return {
        "generated_at": datetime.now().isoformat(),
        "assets": [],
        "total_value": 0.0,
    }


def save_real_estate_json(data: dict) -> Path:
    """Save real estate data to JSON file."""
    return save_json(data, OUTPUT_PATH / "real_estate_data.json", "Real estate")


def save_other_assets_json(data: dict) -> Path:
    """Save other assets data to JSON file."""
    return save_json(data, OUTPUT_PATH / "other_assets_data.json", "Other assets")
