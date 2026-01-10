"""
Mutual Fund Holdings Parsers for MF Central Statements
"""

import re
from pathlib import Path
from typing import Optional, Dict, List


def convert_pdf_to_markdown(file_path: Path) -> Optional[str]:
    """
    Convert PDF to markdown using markitdown CLI

    Args:
        file_path: Path to PDF file

    Returns:
        Markdown content as string, or None on error
    """
    try:
        import subprocess
        # Run markitdown via uv tool
        result = subprocess.run(
            ['uv', 'tool', 'run', 'markitdown[all]', str(file_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )

        if result.returncode != 0:
            print(f"  ⚠️  markitdown returned error for {file_path.name}: {result.stderr}")
            return None

        return result.stdout
    except Exception as e:
        print(f"  ⚠️  Error running markitdown for {file_path.name}: {str(e)}")
        return None


def parse_mf_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse MF Central consolidated account statement (PDF format)

    Args:
        file_path: Path to MF statement PDF file

    Returns:
        Dictionary with account and holdings information, or None on error
    """
    try:
        # Convert PDF to markdown
        content = convert_pdf_to_markdown(file_path)

        if not content:
            return None

        # Extract PAN
        pan_match = re.search(r'PAN\s*:([A-Z0-9]+)', content)
        pan = pan_match.group(1).strip() if pan_match else ""

        # Extract holder name (line after PAN)
        holder_name = ""
        if pan:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if f'PAN :{pan}' in line or f'PAN:{pan}' in line:
                    if i + 2 < len(lines):
                        holder_name = lines[i + 2].strip()
                    break

        # Extract mobile
        mobile_match = re.search(r'Mobile:\s*([\d]+)', content)
        mobile = mobile_match.group(1).strip() if mobile_match else ""

        # Extract email
        email_match = re.search(r'Email:\s*([\S]+@[\S]+)', content, re.IGNORECASE)
        email = email_match.group(1).strip() if email_match else ""

        # Extract statement date
        date_match = re.search(r'As on Date:\s*([\d]{2}-[A-Za-z]{3}-[\d]{4})', content)
        statement_date = date_match.group(1).strip() if date_match else ""

        # Parse SoA Holdings (Non-Demat)
        soa_holdings = parse_soa_holdings(content)

        # Parse Demat Holdings
        demat_holdings = parse_demat_holdings(content)

        # Calculate totals
        soa_value = sum(h['market_value'] for h in soa_holdings)
        demat_value = sum(h['market_value'] for h in demat_holdings)
        total_value = soa_value + demat_value

        return {
            "pan": pan,
            "holder_name": holder_name,
            "mobile": mobile,
            "email": email,
            "statement_date": statement_date,
            "soa_holdings": soa_holdings,
            "demat_holdings": demat_holdings,
            "soa_value": soa_value,
            "demat_value": demat_value,
            "total_value": total_value,
            "total_holdings": len(soa_holdings) + len(demat_holdings),
            "source_file": file_path.name,
        }

    except Exception as e:
        print(f"❌ Error parsing MF file {file_path.name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def parse_soa_holdings(content: str) -> List[Dict]:
    """Parse SoA Holdings section from markdown content"""
    holdings = []

    lines = content.split('\n')

    # Find the SoA Holdings table (after "Folio No." header)
    in_soa_section = False
    in_table = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Start of SoA table (look for "Folio No." header)
        if line == "Folio No." and not in_soa_section:
            # Check if "Scheme Details" appears in next few lines (with empty lines in between)
            has_scheme_details = any("Scheme Details" in lines[j].strip() for j in range(i + 1, min(i + 5, len(lines))))
            if has_scheme_details:
                in_soa_section = True
                in_table = True
                # Skip forward until we find a line that looks like a folio number (long digit string)
                while i < len(lines) and not (lines[i].strip().isdigit() and len(lines[i].strip()) >= 8):
                    i += 1
                continue

        # End of SoA table (when we hit "Client Id" which starts Demat section or "Total")
        if in_soa_section and (line == "Client Id" or line.startswith("Total")):
            break

        # Parse holdings (pattern: Folio number, then scheme name, then numbers)
        if in_table and line and line[0].isdigit() and len(line) > 5:
            try:
                # Check if this is a folio number (long digit string)
                if len(line) >= 8 and line.isdigit():
                    folio = line

                    # Next line: scheme name (may span multiple lines, skip empty lines)
                    i += 1
                    while i < len(lines) and not lines[i].strip():
                        i += 1  # Skip empty lines

                    scheme_lines = []
                    while i < len(lines) and lines[i].strip() and not re.match(r'^[\d,]+\.', lines[i].strip()):
                        scheme_lines.append(lines[i].strip())
                        i += 1
                        # Skip empty lines
                        while i < len(lines) and not lines[i].strip():
                            i += 1

                    scheme = ' '.join(scheme_lines) if scheme_lines else ""

                    # Extract numeric fields (invested value, units, nav date, nav, market value)
                    # Each field may be followed by empty lines
                    invested_value = 0.0
                    units = 0.0
                    nav_date = ""
                    nav = 0.0
                    market_value = 0.0

                    # Invested value
                    if i < len(lines):
                        invested_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d{2}$', invested_str):
                            invested_value = float(invested_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1  # Skip empty lines

                    # Units
                    if i < len(lines):
                        units_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d+$', units_str):
                            units = float(units_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    # NAV Date
                    if i < len(lines):
                        date_str = lines[i].strip()
                        if re.match(r'^\d{2}-[A-Za-z]{3}-\d{4}$', date_str):
                            nav_date = date_str
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    # NAV
                    if i < len(lines):
                        nav_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d+$', nav_str):
                            nav = float(nav_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    # Market Value
                    if i < len(lines):
                        value_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d{2}$', value_str):
                            market_value = float(value_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    if scheme and market_value > 0:
                        holdings.append({
                            "folio": folio,
                            "scheme": scheme,
                            "invested_value": invested_value,
                            "units": units,
                            "nav_date": nav_date,
                            "nav": nav,
                            "market_value": market_value,
                            "holding_type": "SOA"
                        })
                        continue
            except Exception as e:
                pass

        i += 1

    return holdings


def parse_demat_holdings(content: str) -> List[Dict]:
    """Parse Demat Holdings section from markdown content"""
    holdings = []

    # Check if no demat holdings
    if "No MF holdings in Demat" in content:
        return holdings

    lines = content.split('\n')

    # Find the Demat Holdings table (after "Client Id" header)
    in_demat_section = False
    in_table = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Start of Demat table (look for "Client Id" header)
        if line == "Client Id" and not in_demat_section:
            # Check if "Scheme Details" appears in next few lines (with empty lines in between)
            has_scheme_details = any("Scheme Details" in lines[j].strip() for j in range(i + 1, min(i + 5, len(lines))))
            if has_scheme_details:
                in_demat_section = True
                in_table = True
                # Skip forward until we find a line that looks like a client ID (contains dash and digits)
                while i < len(lines):
                    line_stripped = lines[i].strip()
                    if '-' in line_stripped and re.search(r'\d', line_stripped) and len(line_stripped) > 5:
                        break
                    i += 1
                continue

        # End of Demat table (when we hit "Please note:" or "Total")
        if in_demat_section and (line.startswith("Please note") or line.startswith("Total")):
            break

        # Parse holdings (pattern: Client ID, then scheme parts, then numbers)
        if in_table and line and '-' in line and re.search(r'\d', line):
            try:
                # Check if this is a client ID (format: 12081800-41948166 or IN300214-11722076)
                if re.match(r'^[A-Z0-9]+-\d+$', line) or re.match(r'^[A-Z]{2}\d+-\d+$', line):
                    client_id = line

                    # Next lines: scheme name parts (may span multiple lines, skip empty lines)
                    i += 1
                    while i < len(lines) and not lines[i].strip():
                        i += 1  # Skip empty lines

                    scheme_lines = []
                    # Collect scheme parts (stop when we hit a numeric value)
                    while i < len(lines):
                        next_line = lines[i].strip()

                        # Stop if we hit another client ID or a numeric value
                        if re.match(r'^[A-Z0-9]+-\d+$', next_line) or re.match(r'^[\d,]+\.\d{2}$', next_line):
                            break

                        # Add to scheme if it's not empty
                        if next_line and not re.match(r'^\d{4}-\d{2}-\d{2}$', next_line):
                            scheme_lines.append(next_line)
                            i += 1
                            # Skip empty lines
                            while i < len(lines) and not lines[i].strip():
                                i += 1
                        else:
                            break

                    scheme = ' '.join(scheme_lines) if scheme_lines else ""

                    # Extract numeric fields (skip empty lines between fields)
                    invested_value = 0.0
                    units = 0.0
                    nav_date = ""
                    nav = 0.0
                    market_value = 0.0

                    # Invested value
                    if i < len(lines):
                        invested_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d{2}$', invested_str):
                            invested_value = float(invested_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    # Units
                    if i < len(lines):
                        units_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d+$', units_str):
                            units = float(units_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    # NAV date or number
                    if i < len(lines):
                        next_str = lines[i].strip()
                        if re.match(r'^\d{2}-[A-Za-z]{3}-\d{4}$', next_str):
                            nav_date = next_str
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1
                        elif re.match(r'^[\d,]+\.\d+$', next_str):
                            # Skip this if it's 0.0000 (placeholder)
                            if float(next_str.replace(',', '')) == 0.0:
                                i += 1
                                while i < len(lines) and not lines[i].strip():
                                    i += 1
                            else:
                                nav = float(next_str.replace(',', ''))
                                i += 1
                                while i < len(lines) and not lines[i].strip():
                                    i += 1

                    # NAV (if not parsed yet)
                    if nav == 0.0 and i < len(lines):
                        nav_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d+$', nav_str):
                            # Skip if 0.0000
                            if float(nav_str.replace(',', '')) != 0.0:
                                nav = float(nav_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    # Market value
                    if i < len(lines):
                        value_str = lines[i].strip()
                        if re.match(r'^[\d,]+\.\d{2}$', value_str):
                            market_value = float(value_str.replace(',', ''))
                            i += 1
                            while i < len(lines) and not lines[i].strip():
                                i += 1

                    if scheme and market_value > 0:
                        holdings.append({
                            "client_id": client_id,
                            "scheme": scheme,
                            "invested_value": invested_value,
                            "units": units,
                            "nav_date": nav_date,
                            "nav": nav,
                            "market_value": market_value,
                            "holding_type": "DEMAT"
                        })
                        continue
            except Exception as e:
                pass

        i += 1

    return holdings


def consolidate_mf_data(mf_accounts: List[Dict]) -> Dict:
    """
    Consolidate mutual fund data from multiple accounts

    Args:
        mf_accounts: List of parsed MF account dictionaries

    Returns:
        Consolidated MF data dictionary
    """
    if not mf_accounts:
        return {
            "total_value": 0.0,
            "total_holdings": 0,
            "total_accounts": 0,
            "soa_value": 0.0,
            "demat_value": 0.0,
            "accounts": [],
        }

    # Calculate totals
    total_value = sum(acc["total_value"] for acc in mf_accounts)
    total_holdings = sum(acc["total_holdings"] for acc in mf_accounts)
    soa_value = sum(acc["soa_value"] for acc in mf_accounts)
    demat_value = sum(acc["demat_value"] for acc in mf_accounts)

    # Consolidate all holdings across accounts
    all_holdings = []
    for acc in mf_accounts:
        for holding in acc["soa_holdings"]:
            all_holdings.append({
                **holding,
                "account": acc["holder_name"],
                "pan": acc["pan"],
            })
        for holding in acc["demat_holdings"]:
            all_holdings.append({
                **holding,
                "account": acc["holder_name"],
                "pan": acc["pan"],
            })

    # Sort holdings by value descending
    all_holdings.sort(key=lambda x: x["market_value"], reverse=True)

    return {
        "total_value": total_value,
        "total_holdings": total_holdings,
        "total_accounts": len(mf_accounts),
        "soa_value": soa_value,
        "demat_value": demat_value,
        "accounts": mf_accounts,
        "consolidated_holdings": all_holdings,
    }
