"""Indian Tax Computation Module for MeriNetWorth.

This module implements tax calculation rules as per Indian Income Tax Act.
Updated for FY 2025-26 (AY 2026-27) tax rules.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from .interest_calculator import calculate_total_interest


@dataclass
class TaxSlabConfig:
    """Tax slab configuration."""
    min_income: float
    max_income: Optional[float]  # None means no upper limit
    rate: float  # Percentage


# New Tax Regime Slabs FY 2025-26 (Budget 2024 onwards)
NEW_REGIME_SLABS = [
    TaxSlabConfig(0, 300000, 0),           # Up to 3L - Nil
    TaxSlabConfig(300000, 700000, 5),       # 3L to 7L - 5%
    TaxSlabConfig(700000, 1000000, 10),     # 7L to 10L - 10%
    TaxSlabConfig(1000000, 1200000, 15),    # 10L to 12L - 15%
    TaxSlabConfig(1200000, 1500000, 20),    # 12L to 15L - 20%
    TaxSlabConfig(1500000, None, 30),       # Above 15L - 30%
]

# Old Tax Regime Slabs
OLD_REGIME_SLABS_REGULAR = [
    TaxSlabConfig(0, 250000, 0),           # Up to 2.5L - Nil
    TaxSlabConfig(250000, 500000, 5),       # 2.5L to 5L - 5%
    TaxSlabConfig(500000, 1000000, 20),     # 5L to 10L - 20%
    TaxSlabConfig(1000000, None, 30),       # Above 10L - 30%
]

OLD_REGIME_SLABS_SENIOR = [  # Age 60-80
    TaxSlabConfig(0, 300000, 0),           # Up to 3L - Nil
    TaxSlabConfig(300000, 500000, 5),       # 3L to 5L - 5%
    TaxSlabConfig(500000, 1000000, 20),     # 5L to 10L - 20%
    TaxSlabConfig(1000000, None, 30),       # Above 10L - 30%
]

OLD_REGIME_SLABS_SUPER_SENIOR = [  # Age 80+
    TaxSlabConfig(0, 500000, 0),           # Up to 5L - Nil
    TaxSlabConfig(500000, 1000000, 20),     # 5L to 10L - 20%
    TaxSlabConfig(1000000, None, 30),       # Above 10L - 30%
]

# Capital Gains Tax Rates (FY 2024-25 onwards - Budget 2024)
LTCG_EQUITY_RATE = 12.5  # Long-term capital gains on listed equity
STCG_EQUITY_RATE = 20.0  # Short-term capital gains on listed equity
LTCG_EXEMPTION = 125000  # Annual LTCG exemption limit

# Equity MF is treated same as equity for tax
LTCG_EQUITY_MF_RATE = 12.5
STCG_EQUITY_MF_RATE = 20.0

# Debt MF (purchased after Apr 2023 - no LTCG benefit)
DEBT_MF_RATE = "SLAB"  # Taxed at slab rate regardless of holding period

# Interest Income
TDS_INTEREST_THRESHOLD_REGULAR = 40000  # TDS threshold for regular taxpayers
TDS_INTEREST_THRESHOLD_SENIOR = 50000   # TDS threshold for senior citizens
TDS_INTEREST_RATE = 10.0  # TDS rate on interest

# Surcharge Rates
SURCHARGE_SLABS = [
    (5000000, 10000000, 10),    # 50L to 1Cr - 10%
    (10000000, 20000000, 15),   # 1Cr to 2Cr - 15%
    (20000000, 50000000, 25),   # 2Cr to 5Cr - 25%
    (50000000, None, 37),       # Above 5Cr - 37%
]

# LTCG Surcharge capped at 15%
LTCG_SURCHARGE_CAP = 15

# Health & Education Cess
CESS_RATE = 4.0

# NPS Tax Benefits (Old Regime)
NPS_80CCD_1_LIMIT = 150000    # Combined with 80C
NPS_80CCD_1B_LIMIT = 50000    # Additional deduction
NPS_80CCD_2_LIMIT_PERCENT = 10  # Employer contribution (% of basic)


@dataclass
class TaxableIncome:
    """Breakdown of taxable income by category."""
    salary: float = 0.0
    interest_income: float = 0.0
    rental_income: float = 0.0
    business_income: float = 0.0
    capital_gains_stcg: float = 0.0
    capital_gains_ltcg: float = 0.0
    other_income: float = 0.0

    # Deductions (Old Regime)
    deduction_80c: float = 0.0
    deduction_80d: float = 0.0
    deduction_80ccd_1b: float = 0.0
    deduction_hra: float = 0.0
    deduction_other: float = 0.0

    @property
    def total_income(self) -> float:
        """Total income before deductions."""
        return (
            self.salary
            + self.interest_income
            + self.rental_income
            + self.business_income
            + self.capital_gains_stcg
            + self.capital_gains_ltcg
            + self.other_income
        )

    @property
    def total_deductions(self) -> float:
        """Total deductions under old regime."""
        return (
            self.deduction_80c
            + self.deduction_80d
            + self.deduction_80ccd_1b
            + self.deduction_hra
            + self.deduction_other
        )


@dataclass
class TaxBreakdown:
    """Detailed tax computation breakdown."""
    pan: str
    holder_name: str
    assessment_year: str
    tax_regime: str

    # Income Summary
    total_income: float = 0.0
    total_deductions: float = 0.0
    taxable_income: float = 0.0

    # Asset Summary
    bank_balance: float = 0.0
    equity_value: float = 0.0
    mf_value: float = 0.0
    nps_value: float = 0.0
    total_assets: float = 0.0

    # Estimated Annual Interest (for tax estimation)
    estimated_interest: float = 0.0
    interest_by_bank: dict = field(default_factory=dict)

    # Estimated Dividend Income
    estimated_dividend: float = 0.0
    dividend_tds: float = 0.0

    # Capital Gains (estimated unrealized)
    unrealized_stcg: float = 0.0
    unrealized_ltcg: float = 0.0

    # Tax Components
    tax_on_salary: float = 0.0
    tax_on_interest: float = 0.0
    tax_on_dividend: float = 0.0
    tax_on_stcg: float = 0.0
    tax_on_ltcg: float = 0.0
    tax_on_other: float = 0.0

    # Final Tax
    basic_tax: float = 0.0
    surcharge: float = 0.0
    cess: float = 0.0
    total_tax: float = 0.0

    # TDS already deducted (estimated)
    tds_deducted: float = 0.0
    net_tax_payable: float = 0.0

    # Warnings and notes
    notes: list = field(default_factory=list)


def calculate_age(dob: Optional[str], reference_date: Optional[date] = None) -> Optional[int]:
    """Calculate age from date of birth.

    Args:
        dob: Date of birth as string (YYYY-MM-DD)
        reference_date: Reference date for age calculation (default: today)

    Returns:
        Age in years, or None if DOB not provided
    """
    if not dob:
        return None

    try:
        birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
        ref = reference_date or date.today()
        age = ref.year - birth_date.year
        if (ref.month, ref.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except ValueError:
        return None


def get_tax_slabs(regime: str, age: Optional[int]) -> list[TaxSlabConfig]:
    """Get applicable tax slabs based on regime and age.

    Args:
        regime: 'new' or 'old'
        age: Age of taxpayer

    Returns:
        List of applicable tax slabs
    """
    if regime == "new":
        return NEW_REGIME_SLABS

    # Old regime - age-based slabs
    if age is None or age < 60:
        return OLD_REGIME_SLABS_REGULAR
    elif age < 80:
        return OLD_REGIME_SLABS_SENIOR
    else:
        return OLD_REGIME_SLABS_SUPER_SENIOR


def calculate_slab_tax(income: float, slabs: list[TaxSlabConfig]) -> float:
    """Calculate tax based on income and slabs.

    Args:
        income: Taxable income
        slabs: List of tax slabs

    Returns:
        Tax amount
    """
    if income <= 0:
        return 0.0

    tax = 0.0
    remaining = income

    for slab in slabs:
        if remaining <= 0:
            break

        slab_max = slab.max_income if slab.max_income else float('inf')
        slab_range = slab_max - slab.min_income

        if income > slab.min_income:
            taxable_in_slab = min(remaining, slab_range)
            if income > slab_max:
                taxable_in_slab = slab_range
            else:
                taxable_in_slab = income - slab.min_income

            # Ensure we don't exceed what's left
            taxable_in_slab = min(taxable_in_slab, remaining)
            tax += taxable_in_slab * (slab.rate / 100)
            remaining -= taxable_in_slab

    return tax


def calculate_surcharge(tax: float, income: float, has_ltcg: bool = False) -> float:
    """Calculate surcharge on tax.

    Args:
        tax: Basic tax amount
        income: Total income
        has_ltcg: Whether income includes LTCG (surcharge capped at 15%)

    Returns:
        Surcharge amount
    """
    if income <= 5000000:
        return 0.0

    surcharge_rate = 0
    for min_inc, max_inc, rate in SURCHARGE_SLABS:
        if max_inc is None:
            if income > min_inc:
                surcharge_rate = rate
                break
        elif min_inc < income <= max_inc:
            surcharge_rate = rate
            break

    if has_ltcg and surcharge_rate > LTCG_SURCHARGE_CAP:
        surcharge_rate = LTCG_SURCHARGE_CAP

    return tax * (surcharge_rate / 100)


def calculate_cess(tax_plus_surcharge: float) -> float:
    """Calculate Health & Education Cess.

    Args:
        tax_plus_surcharge: Tax amount including surcharge

    Returns:
        Cess amount
    """
    return tax_plus_surcharge * (CESS_RATE / 100)


def estimate_interest_income(
    bank_accounts: Optional[list[dict]] = None,
    bank_balance: Optional[float] = None,
    assumed_rate: float = 4.0,
    days: int = 365
) -> dict:
    """Estimate annual interest income from bank accounts.

    This function now uses bank-specific interest rates from configuration
    and calculates pro-rata interest based on actual rates.

    Args:
        bank_accounts: List of bank account dicts with 'bank' and 'balance' keys
        bank_balance: Total bank balance (fallback if bank_accounts not provided)
        assumed_rate: Assumed interest rate for fallback (default 4%)
        days: Number of days for interest calculation (default 365)

    Returns:
        Dict with:
            - total_interest: Total estimated interest
            - by_bank: Interest breakdown by bank
            - used_config: Whether bank-specific config was used
    """
    if bank_accounts:
        try:
            result = calculate_total_interest(bank_accounts, days)
            return {
                'total_interest': result['total_interest'],
                'by_bank': result['summary_by_bank'],
                'accounts': result['accounts'],
                'used_config': True,
            }
        except Exception as e:
            print(f"⚠️  Error calculating bank-specific interest: {e}")
            print("   Falling back to simple calculation")

    # Fallback to simple calculation
    total = bank_balance or 0.0
    interest = total * (assumed_rate / 100) * (days / 365)

    return {
        'total_interest': round(interest, 2),
        'by_bank': {},
        'accounts': [],
        'used_config': False,
    }


def estimate_tds_on_interest(
    interest: float,
    is_senior: bool = False,
    has_form_15g_h: bool = False
) -> float:
    """Estimate TDS deducted on interest income.

    Args:
        interest: Annual interest income
        is_senior: Whether taxpayer is senior citizen
        has_form_15g_h: Whether Form 15G/15H submitted

    Returns:
        Estimated TDS amount
    """
    if has_form_15g_h:
        return 0.0

    threshold = TDS_INTEREST_THRESHOLD_SENIOR if is_senior else TDS_INTEREST_THRESHOLD_REGULAR

    if interest <= threshold:
        return 0.0

    return interest * (TDS_INTEREST_RATE / 100)


def compute_tax_for_individual(
    pan: str,
    holder_info: dict,
    bank_balance: float = 0.0,
    bank_accounts: Optional[list[dict]] = None,
    equity_value: float = 0.0,
    mf_value: float = 0.0,
    nps_value: float = 0.0,
    mf_gains: Optional[dict] = None,
    dividend_income: float = 0.0,
    dividend_tds: float = 0.0,
) -> TaxBreakdown:
    """Compute estimated tax for an individual.

    This provides an ESTIMATE based on available asset data.
    Actual tax depends on realized gains, other income sources, etc.

    Args:
        pan: PAN card number
        holder_info: Holder information from PAN registry
        bank_balance: Total bank balance
        bank_accounts: List of bank account dicts for accurate interest calculation
        equity_value: Total equity holdings value
        mf_value: Total mutual fund value
        nps_value: NPS corpus value
        mf_gains: Dict with 'invested' and 'current' for gain calculation
        dividend_income: Estimated annual dividend income
        dividend_tds: TDS already deducted on dividends

    Returns:
        TaxBreakdown with estimated tax computation
    """
    result = TaxBreakdown(
        pan=pan,
        holder_name=holder_info.get("name", "Unknown"),
        assessment_year="2026-27",
        tax_regime=holder_info.get("tax_regime", "new"),
    )

    # Calculate age
    age = calculate_age(holder_info.get("dob"))
    is_senior = age is not None and age >= 60
    is_super_senior = age is not None and age >= 80
    is_huf = holder_info.get("is_huf", False)

    # Asset Summary
    result.bank_balance = bank_balance
    result.equity_value = equity_value
    result.mf_value = mf_value
    result.nps_value = nps_value
    result.total_assets = bank_balance + equity_value + mf_value + nps_value

    # Estimate Interest Income (using bank-specific rates)
    interest_calc = estimate_interest_income(
        bank_accounts=bank_accounts,
        bank_balance=bank_balance,
        days=365
    )
    result.estimated_interest = interest_calc['total_interest']
    result.interest_by_bank = interest_calc['by_bank']

    if interest_calc['used_config']:
        result.notes.append("Interest calculated using bank-specific rates")
    else:
        result.notes.append("Interest calculated using default 4% rate")

    # Dividend Income (passed in from dividend estimator)
    result.estimated_dividend = dividend_income
    result.dividend_tds = dividend_tds
    if dividend_income > 0:
        result.notes.append(f"Dividend income: ₹{dividend_income:,.0f} (TDS: ₹{dividend_tds:,.0f})")

    # Estimate MF Gains (unrealized)
    if mf_gains:
        invested = mf_gains.get("invested", 0)
        current = mf_gains.get("current", 0)
        if current > invested:
            # Simplified: assume all gains are LTCG for equity MF
            result.unrealized_ltcg = current - invested
        result.notes.append(f"MF unrealized gains: ₹{result.unrealized_ltcg:,.0f}")

    # Tax Computation
    # Include interest income and dividend income (since capital gains are unrealized)

    taxable_income = TaxableIncome(
        interest_income=result.estimated_interest,
        other_income=result.estimated_dividend,  # Dividends taxed at slab rate
    )

    result.total_income = taxable_income.total_income
    regime = holder_info.get("tax_regime", "new")

    # Get applicable slabs
    slabs = get_tax_slabs(regime, age)

    # Standard deduction under new regime
    standard_deduction = 75000 if regime == "new" else 0

    # Calculate taxable income
    result.taxable_income = max(0, result.total_income - standard_deduction)

    # Calculate basic tax on regular income (interest)
    result.tax_on_interest = calculate_slab_tax(result.taxable_income, slabs)
    result.basic_tax = result.tax_on_interest

    # Rebate under 87A (New Regime: income up to 7L, rebate up to 25000)
    rebate = 0.0
    if regime == "new" and result.taxable_income <= 700000:
        rebate = min(result.basic_tax, 25000)
        result.notes.append(f"Rebate u/s 87A: ₹{rebate:,.0f}")

    result.basic_tax = max(0, result.basic_tax - rebate)

    # Surcharge
    result.surcharge = calculate_surcharge(result.basic_tax, result.total_income)

    # Cess
    result.cess = calculate_cess(result.basic_tax + result.surcharge)

    # Total Tax
    result.total_tax = result.basic_tax + result.surcharge + result.cess

    # TDS already deducted (interest + dividend)
    interest_tds = estimate_tds_on_interest(result.estimated_interest, is_senior)
    result.tds_deducted = interest_tds + result.dividend_tds

    # Net tax payable
    result.net_tax_payable = max(0, result.total_tax - result.tds_deducted)

    # Add notes
    if is_super_senior:
        result.notes.append("Super Senior Citizen (80+): Higher basic exemption in old regime")
    elif is_senior:
        result.notes.append("Senior Citizen (60+): Higher basic exemption, higher TDS threshold")
    if is_huf:
        result.notes.append("HUF: Taxed as separate entity")

    result.notes.append("Note: This is an ESTIMATE based on current holdings.")
    result.notes.append("Actual tax depends on realized gains and other income sources.")

    return result


def format_tax_summary(breakdown: TaxBreakdown) -> str:
    """Format tax breakdown as readable summary.

    Args:
        breakdown: TaxBreakdown object

    Returns:
        Formatted string summary
    """
    lines = [
        f"=== Tax Summary for {breakdown.holder_name} ({breakdown.pan}) ===",
        f"Assessment Year: {breakdown.assessment_year}",
        f"Tax Regime: {breakdown.tax_regime.upper()}",
        "",
        "--- Asset Summary ---",
        f"Bank Balance: ₹{breakdown.bank_balance:,.2f}",
        f"Equity Value: ₹{breakdown.equity_value:,.2f}",
        f"MF Value: ₹{breakdown.mf_value:,.2f}",
        f"NPS Value: ₹{breakdown.nps_value:,.2f}",
        f"Total Assets: ₹{breakdown.total_assets:,.2f}",
        "",
        "--- Estimated Income ---",
        f"Interest Income (Est.): ₹{breakdown.estimated_interest:,.2f}",
        f"Unrealized LTCG: ₹{breakdown.unrealized_ltcg:,.2f}",
        "",
        "--- Tax Computation ---",
        f"Taxable Income: ₹{breakdown.taxable_income:,.2f}",
        f"Basic Tax: ₹{breakdown.basic_tax:,.2f}",
        f"Surcharge: ₹{breakdown.surcharge:,.2f}",
        f"Cess (4%): ₹{breakdown.cess:,.2f}",
        f"Total Tax: ₹{breakdown.total_tax:,.2f}",
        "",
        f"TDS Deducted: ₹{breakdown.tds_deducted:,.2f}",
        f"Net Payable: ₹{breakdown.net_tax_payable:,.2f}",
        "",
        "--- Notes ---",
    ]
    lines.extend([f"• {note}" for note in breakdown.notes])

    return "\n".join(lines)
