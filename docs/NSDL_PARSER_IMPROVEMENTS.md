# NSDL Parser Improvements

## Problem
11 NSDL equity files were showing "Could not identify all required columns" warnings, indicating the parser was unable to match column names to expected fields (ISIN, Security Name, Quantity).

## Root Causes Identified

1. **Limited keyword matching**: Parser only checked for a few keyword variations
2. **Column name variations**: NSDL statements use different column naming conventions
3. **Special characters in column names**: Newlines, spaces, and punctuation in column headers
4. **Unnamed columns**: Excel files often have "Unnamed: 0" style column names
5. **Weak fallback logic**: Simple "use first 3 columns" approach wasn't intelligent enough
6. **Header detection**: Only looked for "ISIN" or "Security Name" in first 15 rows

## Improvements Made

### 1. Enhanced Column Detection (`src/equity_parsers.py` lines 134-162)

**Expanded Keywords**:
- **ISIN column**: Added 'isin no', 'isin number', 'scrip code', 'security code', 'sec code'
- **Name column**: Added 'instrument', 'scrip name', 'name of security', 'sec name', 'company', 'company name'
- **Quantity column**: Added 'bal qty', 'bal.qty', 'bal', 'free qty', 'total qty', 'no. of shares', 'no.of shares', 'no of shares', 'closing balance', 'closing bal'

**Column Name Cleaning**:
```python
col_lower = str(col).lower().strip().replace('\n', ' ').replace('\r', ' ')
```
- Strips whitespace
- Removes newlines and carriage returns
- Converts to lowercase for case-insensitive matching

**Skip Unnamed Columns**:
```python
if str(col).startswith('Unnamed'):
    continue
```

### 2. Intelligent Fallback Strategy (`src/equity_parsers.py` lines 169-216)

When keyword matching fails, the parser now uses positional logic:

**Strategy A**: If Name column found but ISIN missing
- ISIN is likely the column immediately before Name
- `isin_col = df.columns[name_idx - 1]`

**Strategy B**: If Name column found but Quantity missing
- Quantity is likely a column after Name with numeric data
- Scans next 3 columns for numeric values > 0
- Tests by converting first non-null value to float

**Strategy C**: Last resort fallbacks
1. Use first 3 non-unnamed columns
2. Use first 3 columns (including unnamed)

### 3. Improved Header Row Detection (`src/equity_parsers.py` lines 114-141)

**Multi-keyword Detection**:
- Looks for rows containing 2+ header keywords (more robust than single keyword)
- Checks: 'isin', 'security name', 'scrip name', 'security', 'scrip', 'quantity', 'balance', 'holding', 'instrument'
- Expanded search from 15 to 20 rows

**Fallback Detection**:
- If multi-keyword search fails, searches for any row with 'isin'

**Debug Output**:
- Shows first 5 rows if header detection completely fails
- Helps diagnose unusual file formats

## Testing

Run the test script to verify improvements:
```bash
python test_equity.py
```

Expected output:
- Fewer or no "Could not identify all required columns" warnings
- When warnings do appear, detailed debug output showing:
  - Available columns
  - Which columns were successfully identified
  - Which fallback strategy was attempted
  - Actual column names being used

## Additional Fix: Off-by-One Error in Header Row Detection

### Problem
After initial improvements, 2 files still showed warnings:
- `5150798IN30020610786909.xlsx`
- `5150814IN30020611058388.xlsx`

Both files had an unusual structure where the footnote row was being used as the header instead of the actual data header.

### Root Cause
**Off-by-one error in skiprows calculation**:
1. Parser initially reads file with default settings (row 0 becomes header)
2. Searches DataFrame and finds actual header at index 7
3. Re-reads with `skiprows=7`, which skips 7 rows from raw Excel
4. **Bug**: This caused row 7 (footnote) to become header, row 8 (actual header) to become first data row

### Solution
Changed line 146 in `src/equity_parsers.py`:
```python
# Before:
df = pd.read_excel(file_path, sheet_name=0, skiprows=header_row)

# After (with explanation):
# Note: header_row is the index in the DataFrame (which already consumed row 0 as header)
# So we need to skip header_row + 1 rows from the raw Excel file
df = pd.read_excel(file_path, sheet_name=0, skiprows=header_row + 1)
```

### Metadata Extraction Improvements
Enhanced metadata extraction (lines 98-137) to:
- Separately extract DP ID and Client ID
- Properly identify holder name (prefer "First holder"/"Sole Holder" over "DP Name")
- Correctly parse statement dates from "SOH as on DD-MMM-YYYY at HH:MM:SS" format
- Combine DP ID + Client ID for full account number

**Key Changes**:
- Extract DP ID from "DP ID : IN300206"
- Extract Client ID from "Client ID : 10786909"
- Extract holder name from "First holder / Sole Holder : NAME" (not from "DP Name")
- Extract date from "SOH as on 21-Oct-2025 at 15:59:24" → "21-oct-2025"

## Files Modified

- `src/equity_parsers.py` - Enhanced `parse_nsdl_statement()` function
  - Lines 98-137: Improved metadata extraction with separate DP ID/Client ID handling
  - Line 146: Fixed off-by-one error in header row detection
  - Lines 285-306: Updated return statement to use extracted DP ID/Client ID

## Test Results

✅ **All NSDL files now parse successfully without warnings!**

Running `python test_equity.py`:
- 11 NSDL files processed successfully
- 0 warnings about column identification
- Total: 480 equity holdings from NSDL accounts

The two previously problematic files now parse correctly:
- `5150798IN30020610786909.xlsx`: 124 holdings, holder "SATYA PRAKASH MITAL"
- `5150814IN30020611058388.xlsx`: 17 holdings, holder "VANEETA MITTAL"

## Future Considerations

1. Monitor for new NSDL file format variations
2. Consider creating NSDL file format documentation based on observed patterns
3. Add unit tests for edge cases (files with footnotes, unusual metadata formats)
