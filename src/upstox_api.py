"""
Upstox API Integration for fetching LTP (Last Traded Price)
"""

import requests
import json
from typing import Dict, Optional, List
from pathlib import Path
import time


class UpstoxAPI:
    """Upstox API client for fetching stock prices"""

    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self, access_token: str):
        """
        Initialize Upstox API client

        Args:
            access_token: Upstox API access token
        """
        self.access_token = access_token
        self.headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
        # Cache for ISIN to symbol mapping
        self.isin_symbol_cache = {}
        self._load_isin_mapping()

    def _load_isin_mapping(self):
        """Load ISIN to symbol mapping from local file if exists"""
        mapping_file = Path(__file__).parent / "isin_symbol_mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, "r") as f:
                    self.isin_symbol_cache = json.load(f)
                print(f"✅ Loaded {len(self.isin_symbol_cache)} ISIN mappings from cache")
            except Exception as e:
                print(f"⚠️  Warning: Could not load ISIN mapping: {e}")

    def _save_isin_mapping(self):
        """Save ISIN to symbol mapping to local file"""
        mapping_file = Path(__file__).parent / "isin_symbol_mapping.json"
        try:
            with open(mapping_file, "w") as f:
                json.dump(self.isin_symbol_cache, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save ISIN mapping: {e}")

    def search_instrument(self, isin: str) -> Optional[str]:
        """
        Search for trading symbol using ISIN

        Args:
            isin: ISIN code (e.g., INE885A01032)

        Returns:
            Instrument key (e.g., NSE_EQ|INE885A01032) or None
        """
        # Check cache first
        if isin in self.isin_symbol_cache:
            return self.isin_symbol_cache[isin]

        try:
            url = f"{self.BASE_URL}/market-quote/search"
            params = {"q": isin}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data"):
                    # Get the first matching instrument
                    instruments = data["data"]
                    for instrument in instruments:
                        # Prefer NSE_EQ (NSE Equity)
                        instrument_key = instrument.get("instrument_key", "")
                        if "NSE_EQ" in instrument_key or "BSE_EQ" in instrument_key:
                            self.isin_symbol_cache[isin] = instrument_key
                            self._save_isin_mapping()
                            return instrument_key

                    # If no equity found, return first result
                    if instruments:
                        instrument_key = instruments[0].get("instrument_key", "")
                        self.isin_symbol_cache[isin] = instrument_key
                        self._save_isin_mapping()
                        return instrument_key

            else:
                print(f"⚠️  API error for {isin}: {response.status_code}")

        except Exception as e:
            print(f"❌ Error searching instrument {isin}: {str(e)}")

        return None

    def get_ltp(self, instrument_key: str) -> Optional[float]:
        """
        Get Last Traded Price for an instrument

        Args:
            instrument_key: Instrument key (e.g., NSE_EQ|INE885A01032)

        Returns:
            Last traded price or None
        """
        try:
            url = f"{self.BASE_URL}/market-quote/ltp"
            params = {"instrument_key": instrument_key}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data"):
                    instrument_data = data["data"].get(instrument_key, {})
                    ltp = instrument_data.get("last_price")
                    return float(ltp) if ltp else None
            else:
                print(f"⚠️  API error for {instrument_key}: {response.status_code}")

        except Exception as e:
            print(f"❌ Error fetching LTP for {instrument_key}: {str(e)}")

        return None

    def get_ltp_by_isin(self, isin: str) -> Optional[float]:
        """
        Get Last Traded Price using ISIN

        Args:
            isin: ISIN code

        Returns:
            Last traded price or None
        """
        instrument_key = self.search_instrument(isin)
        if instrument_key:
            return self.get_ltp(instrument_key)
        return None

    def get_bulk_ltp(self, isins: List[str], delay: float = 0.1) -> Dict[str, float]:
        """
        Get LTP for multiple ISINs

        Args:
            isins: List of ISIN codes
            delay: Delay between API calls to avoid rate limiting (seconds)

        Returns:
            Dictionary mapping ISIN to LTP
        """
        results = {}
        total = len(isins)

        print(f"\n📊 Fetching LTP for {total} securities...")

        for i, isin in enumerate(isins, 1):
            print(f"  [{i}/{total}] Processing {isin}...", end=" ")

            ltp = self.get_ltp_by_isin(isin)
            if ltp is not None:
                results[isin] = ltp
                print(f"✓ ₹{ltp:,.2f}")
            else:
                print("✗ Failed")

            # Rate limiting
            if i < total:
                time.sleep(delay)

        print(f"\n✅ Successfully fetched {len(results)}/{total} prices")
        return results

    def update_holdings_with_ltp(self, holdings: List[Dict]) -> List[Dict]:
        """
        Update holdings list with current LTP data

        Args:
            holdings: List of holdings dictionaries with 'isin' and 'quantity' keys

        Returns:
            Updated holdings list with current 'last_price' and 'value'
        """
        # Get unique ISINs
        isins = list(set(h["isin"] for h in holdings))

        # Fetch LTPs
        ltp_data = self.get_bulk_ltp(isins)

        # Update holdings
        updated_count = 0
        for holding in holdings:
            isin = holding["isin"]
            if isin in ltp_data:
                holding["last_price"] = ltp_data[isin]
                holding["value"] = holding["quantity"] * ltp_data[isin]
                updated_count += 1

        print(f"\n✅ Updated {updated_count}/{len(holdings)} holdings with current prices")
        return holdings


def create_upstox_client(access_token: Optional[str] = None) -> Optional[UpstoxAPI]:
    """
    Create Upstox API client

    Args:
        access_token: Upstox access token (if None, tries to load from env)

    Returns:
        UpstoxAPI instance or None
    """
    import os

    if not access_token:
        access_token = os.environ.get("UPSTOX_ACCESS_TOKEN")

    if not access_token:
        print("❌ Error: Upstox access token not provided")
        print("   Set UPSTOX_ACCESS_TOKEN environment variable or pass as parameter")
        return None

    return UpstoxAPI(access_token)
