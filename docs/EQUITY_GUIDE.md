# Equity Holdings Integration Guide This guide explains how to use the equity holdings tracking feature with Upstox API integration. ## Features - **CDSL & NSDL Parser**: Automatically extracts holdings from demat statements
- **Upstox API Integration**: Fetches current LTP (Last Traded Price) on-demand
- **Sync Button**: Manual price refresh without auto-updates
- **Consolidated View**: Shows all holdings across multiple demat accounts
- **Dashboard Integration**: Equity section integrated into main dashboard --- ## Setup ### 1. Install Dependencies ```bash
pip install -r requirements.txt
``` ### 2. Get Upstox API Access Token You need an access token to use Upstox API: #### Option A: Via Upstox Developer Portal (Recommended) 1. Go to https://developers.upstox.com/
2. Sign in with your Upstox account
3. Create a new app (if you haven't already)
4. Get your **API Key**and **API Secret**
5. Generate an **Access Token**using OAuth flow **Quick Token Generation Script**(save as `get_upstox_token.py`): ```python
from upstox_api import Session # Your app credentials
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
redirect_uri = "https://127.0.0.1" # Initialize session
session = Session(api_key)
session.set_redirect_uri(redirect_uri)
session.set_api_secret(api_secret) # Get login URL
print("Visit this URL to authorize:")
print(session.get_login_url()) # After authorization, you'll be redirected to redirect_uri with a code
# Enter that code here:
code = input("Enter authorization code: ") # Get access token
session.set_code(code)
access_token = session.retrieve_access_token() print(f"\nYour Access Token:\n{access_token}")
print("\nSet this as environment variable:")
print(f"export UPSTOX_ACCESS_TOKEN='{access_token}'")
``` #### Option B: Manual OAuth Flow 1. Visit: `https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=YOUR_API_KEY&redirect_uri=YOUR_REDIRECT_URI`
2. Authorize the app
3. Extract the `code` from redirect URL
4. Make POST request to get token: ```bash
curl -X POST https://api.upstox.com/v2/login/authorization/token \ -H 'Content-Type: application/x-www-form-urlencoded' \ -d 'code=YOUR_CODE&client_id=YOUR_API_KEY&client_secret=YOUR_API_SECRET&redirect_uri=YOUR_REDIRECT_URI&grant_type=authorization_code'
``` ### 3. Set Environment Variable ```bash
# For current session
export UPSTOX_ACCESS_TOKEN="your_access_token_here" # For permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export UPSTOX_ACCESS_TOKEN="your_access_token_here"' >> ~/.bashrc
source ~/.bashrc
``` --- ## Data Processing Workflow ### Step 1: Place Your Equity Files Organize your demat statements in the following structure: ```
data/10.25/equity/ cdsl/ ankurMO.csv divitUpstox.csv hufDhan.csv nsdl/ 5150801IN30021411722076.xlsx abhipra/ 5150798IN30020610786909.xlsx
``` **Supported Formats:**
- **CDSL**: CSV files with standard CDSL format
- **NSDL**: Excel files (.xlsx, .xls) ### Step 2: Process Equity Data You have **two options**: #### Option A: Using Python Script (Standalone) ```bash
cd /Users/div/Projects/Misc/MeriNetWorth # Without price sync (uses prices from statement)
python src/process_equity.py # With Upstox price sync
UPSTOX_ACCESS_TOKEN="your_token" python src/process_equity.py
``` #### Option B: Using Jupyter Notebook (Integrated) Open `notebooks/bank_data_processor.ipynb` and add these cells at the end: ```python
# Cell 1: Import equity processor
import sys
sys.path.append(str(BASE_PATH / 'src'))
from process_equity import process_all_equity_statements, save_equity_json, combine_bank_and_equity_data # Cell 2: Process equity (without price sync)
equity_data = process_all_equity_statements( equity_path=EQUITY_PATH, sync_prices=False # Set to True for Upstox sync
) # Cell 3: Save equity data
save_equity_json(equity_data, OUTPUT_PATH) # Cell 4: Combine with bank data
combine_bank_and_equity_data(web_data, equity_data, OUTPUT_PATH) print("\n Equity data processed successfully!")
``` ### Step 3: Launch Dashboard ```bash
streamlit run web/app.py
# Or use the launcher script
./run_dashboard.sh
``` --- ## Using the Sync Button ### In the Dashboard 1. Open the dashboard: `streamlit run web/app.py`
2. Login with your password
3. In the **sidebar**, find " Equity Actions"
4. Click **Sync Prices (Upstox)**
5. Wait for the sync to complete (shows progress)
6. Dashboard will auto-refresh with updated prices **Note**: The sync button:
- Fetches real-time LTP from Upstox
- Updates `output/equity_data.json`
- Recalculates portfolio value
- Updates the dashboard display ### Sync Frequency Recommendations - **Daily traders**: Sync 2-3 times per day
- **Investors**: Once daily or weekly
- **Long-term holders**: Weekly or before major decisions **Rate Limits**: Upstox API has rate limits. The script includes automatic delays (0.1s between requests) to avoid hitting limits. --- ## Dashboard Features ### Equity Section Includes: 1. **Top Metrics**: - Total Net Worth (Banks + Equity) - Bank Balance - Equity Value - Total Assets count 2. **Equity Holdings Summary**: - Total holdings count - Total portfolio value - Number of demat accounts 3. **Top Holdings Table**: - Security name - Quantity held - Last Traded Price (LTP) - Total value 4. **Visual Charts**: - Pie chart of top 10 holdings - Distribution analysis 5. **Holdings by Demat Account**: - Expandable sections for each account - ISIN codes - Detailed holding information --- ## Troubleshooting ### Issue 1: "No module named 'equity_parsers'" **Solution**: Ensure `src/` directory is in Python path ```python
import sys
sys.path.append('/Users/div/Projects/Misc/MeriNetWorth/src')
``` ### Issue 2: "UPSTOX_ACCESS_TOKEN not found" **Solution**: Set environment variable ```bash
export UPSTOX_ACCESS_TOKEN="your_token"
# Verify it's set
echo $UPSTOX_ACCESS_TOKEN
``` ### Issue 3: "API error: 401 Unauthorized" **Solution**: Your access token expired. Upstox tokens typically expire after 24 hours. 1. Regenerate token using the OAuth flow
2. Update environment variable
3. Try sync again ### Issue 4: Sync takes too long **Solution**: Reduce the delay between API calls Edit `src/upstox_api.py`: ```python
# Change this line in get_bulk_ltp method
time.sleep(delay) # Default is 0.1s # To:
time.sleep(0.05) # Faster, but higher risk of rate limiting
``` ### Issue 5: Some stocks not found **Solution**: ISIN to symbol mapping failed 1. Check `src/isin_symbol_mapping.json` - this file caches mappings
2. Manually add missing mappings: ```json
{ "INE855B01025": "NSE_EQ|INE855B01025", "INE123A01012": "NSE_EQ|SBIN"
}
``` ### Issue 6: NSDL Excel file not parsing **Solution**: NSDL formats vary by broker 1. Open the file manually and check structure
2. Update `src/equity_parsers.py` → `parse_nsdl_statement()` function
3. Adjust row offsets and column names to match your format --- ## Output Files After processing, you'll have: ### 1. `output/equity_data.json` Contains:
- All holdings across accounts
- Consolidated view by ISIN
- Prices (from statement or Upstox)
- Total portfolio value ### 2. `output/networth_data.json` Contains:
- Combined bank + equity data
- Total net worth calculation
- Summary statistics ### 3. ISIN Mapping Cache `src/isin_symbol_mapping.json`:
- Cached ISIN → Symbol mappings
- Speeds up subsequent syncs
- Auto-generated and updated --- ## Advanced Usage ### Custom Sync Schedule For automated daily sync, create a cron job: ```bash
# Edit crontab
crontab -e # Add this line (runs at 6 PM daily)
0 18 * * * cd /Users/div/Projects/Misc/MeriNetWorth && /usr/bin/python3 src/process_equity.py
``` ### API Rate Limit Management To avoid hitting Upstox rate limits: 1. **Batch processing**: Group ISINs and process in batches
2. **Caching**: ISIN mappings are cached automatically
3. **Delay adjustment**: Increase delay in `get_bulk_ltp()` if needed ### Adding New Demat Accounts 1. Export statement from your broker
2. Place in appropriate directory (cdsl/ or nsdl/)
3. Run the processor - it will auto-detect new files --- ## Security Notes 1. **Access Token**: Never commit tokens to git
2. **Statement Files**: Contains sensitive ISIN and holdings data
3. **Output Files**: Gitignored by default for privacy
4. **.env Support**: Consider using python-dotenv for token management ```bash
# Install python-dotenv
pip install python-dotenv # Create .env file
echo "UPSTOX_ACCESS_TOKEN=your_token" > .env # Update scripts to load from .env
from dotenv import load_dotenv
load_dotenv()
``` --- ## References - [Upstox API Documentation](https://upstox.com/developer/api-documentation)
- [Upstox Python SDK](https://github.com/upstox/upstox-python)
- [CDSL Statement Format](https://www.cdslindia.com/)
- [NSDL Statement Format](https://nsdl.co.in/) --- ## Tips 1. **First Run**: Process without sync to verify parsers work correctly
2. **Regular Backups**: Backup `output/` directory before syncing
3. **Version Control**: Keep statements in dated folders (data/MM.YY/)
4. **Testing**: Test with small sample files first
5. **Token Expiry**: Set reminders to regenerate tokens --- ## Need Help? If you encounter issues: 1. Check logs in terminal output
2. Verify file formats match expected structure
3. Test Upstox API connection separately
4. Review error messages in dashboard --- **Congratulations!**Your equity holdings are now tracked alongside bank accounts with real-time LTP sync capability!
