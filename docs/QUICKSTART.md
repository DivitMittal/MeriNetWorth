# Quick Start Guide Get up and running with MeriNetWorth in 3 simple steps! ## Step 1: Install Dependencies (2 minutes) ```bash
# Navigate to project directory
cd /Users/div/Projects/MeriNetWorth # Install required packages
pip install -r requirements.txt
``` ## Step 2: Process Your Bank Data (5 minutes) ### Option A: Using Jupyter Notebook (Recommended) ```bash
# Launch Jupyter
jupyter notebook notebooks/bank_data_processor.ipynb
``` Then:
1. Click "Cell" → "Run All" (or press Shift+Enter on each cell)
2. Wait for all cells to execute
3. Check the output for any errors ### Option B: Using Python Script (Coming Soon) ```bash
python src/process_banks.py
``` ## Step 3: Launch the Dashboard (30 seconds) ```bash
# Easy way
./run_dashboard.sh # Or manually
streamlit run web/app.py
``` Your browser will automatically open to `http://localhost:8501` --- ## What You'll See ### In Jupyter Notebook:
- Bank statements being parsed
- Summary tables by bank
- Total balance calculations
- Generated Excel files
- Quick visualization charts ### In Web Dashboard:
- Total balance across all accounts
- Bank-wise breakdown
- Interactive charts (pie, bar, treemap)
- Filterable views
- Detailed account tables --- ## Expected Output ### Console Output:
``` PROCESSING ALL BANK STATEMENTS
================================================ Processing IDFC First Bank... IDFCFIRSTBankstatement_10000548236.xlsx: ₹29,98,651.70 IDFCFIRSTBankstatement_10055827715.xlsx: ₹15,88,203.69 ... Processing Equitas Bank... Account_Summary_Report_20250604120542539.xlsx: ₹37,52,678.90 ... ================================================ Total accounts processed: 15 TOTAL BALANCE: ₹301.94 Lakhs
``` ### Generated Files:
- `output/bank_data.json` - Data for web dashboard
- `output/Bank-Consolidated-Jun'25.xlsx` - Excel report with 3 sheets --- ## Troubleshooting ### Issue: Module not found
```bash
pip install -r requirements.txt --upgrade
``` ### Issue: "No data found" in dashboard
Run the Jupyter notebook first to generate the data files. ### Issue: Excel file won't open
Check that openpyxl is installed: `pip install openpyxl` ### Issue: Charts not showing in dashboard
Install plotly: `pip install plotly` --- ## Customization Tips ### Change Data Period
Edit the notebook path configuration:
```python
DATA_PATH = BASE_PATH / 'data' / '06.25' # Change to '07.25', etc.
``` ### Add More Banks
Add a new parser function in `notebooks/bank_data_processor.ipynb`:
```python
def parse_newbank_statement(file_path): # Your logic here return {...}
``` ### Modify Dashboard Colors
Edit `web/app.py` CSS section:
```python
st.markdown("""
<style> .metric-card { background: your-gradient-here; }
</style>
""")
``` --- ## Next Steps 1. **Explore the Data**: Click around the dashboard, use filters
2. **Check Excel Output**: Open the generated Excel file
3. **Customize**: Modify parsers for your specific needs
4. **Automate**: Set up monthly processing (see README.md) --- ## Need Help? - Full documentation: See `README.md`
- Found a bug: Open an issue on GitHub
- Have an idea: Submit a feature request --- **Happy Financial Tracking! **
