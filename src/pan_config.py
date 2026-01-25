"""PAN card configuration and holder mappings for tax computation.

This module loads PAN registry from a private JSON file (not committed to git).
Copy config/pan_registry.example.json to config/pan_registry.private.json
and fill in your actual PAN details.
"""

import json
from pathlib import Path
from typing import Optional

# Path to private PAN registry (not committed to git)
_CONFIG_DIR = Path(__file__).parent.parent / "config"
_PRIVATE_CONFIG = _CONFIG_DIR / "pan_registry.private.json"
_EXAMPLE_CONFIG = _CONFIG_DIR / "pan_registry.example.json"


def _load_pan_registry() -> dict:
    """Load PAN registry from private config file.

    Falls back to example config if private config doesn't exist.
    """
    if _PRIVATE_CONFIG.exists():
        with open(_PRIVATE_CONFIG, "r") as f:
            return json.load(f)

    if _EXAMPLE_CONFIG.exists():
        print(
            f"Warning: Private PAN config not found at {_PRIVATE_CONFIG}\n"
            f"Using example config. Copy {_EXAMPLE_CONFIG.name} to "
            f"{_PRIVATE_CONFIG.name} and update with your details."
        )
        with open(_EXAMPLE_CONFIG, "r") as f:
            return json.load(f)

    print("Warning: No PAN registry config found. Tax computation will be limited.")
    return {}


# Load PAN registry at module import
PAN_REGISTRY: dict = _load_pan_registry()


def reload_pan_registry() -> None:
    """Reload PAN registry from config file.

    Useful if the config file was updated during runtime.
    """
    global PAN_REGISTRY
    PAN_REGISTRY = _load_pan_registry()


def normalize_name(name: str) -> str:
    """Normalize holder name for matching."""
    if not name:
        return ""
    # Remove extra spaces and convert to uppercase
    return " ".join(name.upper().split())


def find_pan_for_holder(holder_name: str) -> Optional[str]:
    """Find PAN for a given holder name.

    Args:
        holder_name: The holder name from account data

    Returns:
        PAN if found, None otherwise
    """
    if not holder_name:
        return None

    normalized = normalize_name(holder_name)

    for pan, info in PAN_REGISTRY.items():
        variants = [normalize_name(v) for v in info.get("name_variants", [])]
        if normalized in variants:
            return pan

    return None


def get_holder_info(pan: str) -> Optional[dict]:
    """Get holder information for a PAN.

    Args:
        pan: The PAN card number

    Returns:
        Holder info dict if found, None otherwise
    """
    return PAN_REGISTRY.get(pan)


def get_all_pans() -> list[str]:
    """Get list of all registered PANs."""
    return list(PAN_REGISTRY.keys())


def get_holder_name(pan: str) -> str:
    """Get primary holder name for a PAN."""
    info = PAN_REGISTRY.get(pan)
    return info["name"] if info else "Unknown"
