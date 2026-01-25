"""Bank interest rate calculator with pro-rata computation.

This module provides functions to calculate savings account interest
based on bank-specific rates and tiered balance slabs.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import date

# Path to interest rates config
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'bank_interest_rates.json'

# Cache for loaded config
_rates_config: Optional[dict] = None


def load_interest_rates() -> dict:
    """Load bank interest rates from configuration file.

    Returns:
        Dict containing bank interest rate configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    global _rates_config

    if _rates_config is not None:
        return _rates_config

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Interest rates config not found at {CONFIG_PATH}. "
            "Please create the configuration file."
        )

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        _rates_config = json.load(f)

    return _rates_config


def get_applicable_rate(bank_name: str, balance: float) -> float:
    """Get applicable interest rate for a bank and balance.

    Args:
        bank_name: Name of the bank (must match config key)
        balance: Account balance

    Returns:
        Applicable interest rate (percentage per annum)

    Examples:
        >>> get_applicable_rate("IDFC First Bank", 600000)
        7.0
        >>> get_applicable_rate("Kotak Mahindra Bank", 1000000)
        2.5
    """
    try:
        config = load_interest_rates()
        banks = config.get('banks', {})

        # Try exact match first
        bank_config = banks.get(bank_name)

        # If no match, try case-insensitive partial match
        if not bank_config:
            bank_name_lower = bank_name.lower()
            for key, value in banks.items():
                if key.lower() in bank_name_lower or bank_name_lower in key.lower():
                    bank_config = value
                    break

        # If still no match, use default
        if not bank_config:
            bank_config = banks.get('_default', {'type': 'flat', 'rate': 3.0})

        rate_type = bank_config.get('type', 'flat')

        if rate_type == 'flat':
            return bank_config.get('rate', 3.0)

        elif rate_type == 'tiered':
            slabs = bank_config.get('slabs', [])

            # Find applicable slab
            for slab in slabs:
                min_bal = slab.get('min_balance', 0)
                max_bal = slab.get('max_balance')

                if max_bal is None:
                    # Highest slab with no upper limit
                    if balance >= min_bal:
                        return slab.get('rate', 3.0)
                elif min_bal <= balance < max_bal:
                    return slab.get('rate', 3.0)

            # If no slab matched, return first slab rate
            return slabs[0].get('rate', 3.0) if slabs else 3.0

        return 3.0

    except Exception as e:
        print(f"⚠️  Error loading interest rates: {e}")
        return 3.0  # Fallback rate


def calculate_pro_rata_interest(
    balance: float,
    rate: float,
    days: int = 365,
    days_in_year: int = 365
) -> float:
    """Calculate pro-rata interest for a given period.

    Formula: (Balance × Rate × Days) / (100 × Days_in_Year)

    Args:
        balance: Account balance
        rate: Annual interest rate (percentage)
        days: Number of days for interest calculation (default: 365 for full year)
        days_in_year: Days in the year (365 or 366 for leap year)

    Returns:
        Interest amount for the period

    Examples:
        >>> calculate_pro_rata_interest(100000, 5.0, 365, 365)
        5000.0
        >>> calculate_pro_rata_interest(100000, 5.0, 182, 365)
        2493.15
    """
    if balance <= 0 or rate <= 0 or days <= 0:
        return 0.0

    interest = (balance * rate * days) / (100 * days_in_year)
    return round(interest, 2)


def calculate_bank_interest(
    bank_name: str,
    balance: float,
    days: int = 365,
    days_in_year: int = 365
) -> dict:
    """Calculate interest for a bank account with pro-rata calculation.

    Args:
        bank_name: Name of the bank
        balance: Account balance
        days: Number of days for interest calculation (default: 365)
        days_in_year: Days in the year (365 or 366)

    Returns:
        Dict with interest calculation details:
            - bank: Bank name
            - balance: Account balance
            - rate: Applicable interest rate (%)
            - days: Days calculated
            - interest: Calculated interest amount
            - annualized_interest: Full year interest (for reference)

    Examples:
        >>> result = calculate_bank_interest("IDFC First Bank", 600000)
        >>> result['rate']
        7.0
        >>> result['interest']
        42000.0
    """
    rate = get_applicable_rate(bank_name, balance)
    interest = calculate_pro_rata_interest(balance, rate, days, days_in_year)
    annualized_interest = calculate_pro_rata_interest(balance, rate, 365, 365)

    return {
        'bank': bank_name,
        'balance': balance,
        'rate': rate,
        'days': days,
        'days_in_year': days_in_year,
        'interest': interest,
        'annualized_interest': annualized_interest,
    }


def calculate_total_interest(bank_accounts: list[dict], days: int = 365) -> dict:
    """Calculate total interest across multiple bank accounts.

    Args:
        bank_accounts: List of account dicts with 'bank' and 'balance' keys
        days: Number of days for interest calculation

    Returns:
        Dict with:
            - total_interest: Sum of all interest
            - accounts: List of per-account interest details
            - summary_by_bank: Interest grouped by bank

    Examples:
        >>> accounts = [
        ...     {'bank': 'IDFC First Bank', 'balance': 600000},
        ...     {'bank': 'Kotak Mahindra Bank', 'balance': 200000}
        ... ]
        >>> result = calculate_total_interest(accounts)
        >>> result['total_interest']
        47000.0
    """
    # Determine if leap year for current calculation
    current_year = date.today().year
    days_in_year = 366 if is_leap_year(current_year) else 365

    account_details = []
    total_interest = 0.0
    summary_by_bank = {}

    for account in bank_accounts:
        bank = account.get('bank', 'Unknown')
        balance = account.get('balance', 0)

        if balance <= 0:
            continue

        result = calculate_bank_interest(bank, balance, days, days_in_year)
        account_details.append({
            'bank': bank,
            'account_number': account.get('account_number', 'N/A'),
            'balance': balance,
            'rate': result['rate'],
            'interest': result['interest'],
        })

        total_interest += result['interest']

        # Group by bank
        if bank not in summary_by_bank:
            summary_by_bank[bank] = {
                'total_balance': 0,
                'total_interest': 0,
                'account_count': 0,
            }

        summary_by_bank[bank]['total_balance'] += balance
        summary_by_bank[bank]['total_interest'] += result['interest']
        summary_by_bank[bank]['account_count'] += 1

    return {
        'total_interest': round(total_interest, 2),
        'accounts': account_details,
        'summary_by_bank': summary_by_bank,
        'calculation_days': days,
        'days_in_year': days_in_year,
    }


def is_leap_year(year: int) -> bool:
    """Check if a year is a leap year.

    Args:
        year: Year to check

    Returns:
        True if leap year, False otherwise
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def get_rate_info(bank_name: str) -> dict:
    """Get detailed rate information for a bank.

    Args:
        bank_name: Name of the bank

    Returns:
        Dict with rate configuration details
    """
    try:
        config = load_interest_rates()
        banks = config.get('banks', {})

        # Try exact match
        bank_config = banks.get(bank_name)

        # Try partial match
        if not bank_config:
            bank_name_lower = bank_name.lower()
            for key, value in banks.items():
                if key.lower() in bank_name_lower or bank_name_lower in key.lower():
                    bank_config = value
                    bank_name = key
                    break

        if not bank_config:
            return {
                'bank': bank_name,
                'type': 'unknown',
                'message': 'Bank not found in configuration',
            }

        return {
            'bank': bank_name,
            'type': bank_config.get('type'),
            'config': bank_config,
        }

    except Exception as e:
        return {
            'bank': bank_name,
            'error': str(e),
        }


if __name__ == '__main__':
    # Test the module
    print("🏦 Bank Interest Rate Calculator - Test Run\n")

    test_accounts = [
        {'bank': 'IDFC First Bank', 'account_number': 'XXX123', 'balance': 600000},
        {'bank': 'Kotak Mahindra Bank', 'account_number': 'YYY456', 'balance': 200000},
        {'bank': 'Bandhan Bank', 'account_number': 'ZZZ789', 'balance': 1500000},
        {'bank': 'ICICI Bank', 'account_number': 'AAA111', 'balance': 500000},
    ]

    result = calculate_total_interest(test_accounts)

    print(f"Total Interest (Annual): ₹{result['total_interest']:,.2f}\n")
    print("Per-Account Breakdown:")
    print("-" * 70)

    for acc in result['accounts']:
        print(f"{acc['bank']:25} | Balance: ₹{acc['balance']:>10,.0f} | "
              f"Rate: {acc['rate']:>4.2f}% | Interest: ₹{acc['interest']:>10,.2f}")

    print("\n" + "=" * 70)
    print(f"{'TOTAL':25} | {'':19} | {'':11} | ₹{result['total_interest']:>10,.2f}")
