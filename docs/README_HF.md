---
title: MeriNetWorth Dashboard
emoji: colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: "1.28.0"
app_file: web/app.py
pinned: false
license: mit
--- # MeriNetWorth - Bank Account Dashboard A secure, password-protected financial dashboard for consolidating and visualizing bank account data. ## Features - Password-protected access
- Multi-bank account consolidation
- Interactive visualizations (Pie charts, Bar charts, Treemaps)
- Real-time balance tracking
- Support for IDFC, Equitas, Bandhan, ICICI, IndusInd banks ## Setup Instructions ### For Hugging Face Spaces Deployment 1. **Fork this repository**or create a new Space on Hugging Face 2. **Configure Secrets**: Go to Space Settings → Repository Secrets and add: - `DASHBOARD_PASSWORD`: Your secure password for accessing the dashboard 3. **Upload Data**: Ensure your `output/bank_data.json` file is present in the repository 4. **Deploy**: The space will automatically deploy ## Local Development ```bash
# Install dependencies
pip install -r requirements.txt # Set password (optional, defaults to 'changeme123')
export DASHBOARD_PASSWORD="your_secure_password" # Run the dashboard
streamlit run web/app.py
``` ## Data Processing To generate the `output/bank_data.json` file: 1. Place bank statements in `data/MM.YY/Bank/{BankName}/`
2. Run the Jupyter notebook: `notebooks/bank_data_processor.ipynb`
3. Execute all cells to process statements and generate output files ## Security - All data is processed locally
- Password protection using secure HMAC comparison
- No data is sent to external servers (except Hugging Face hosting)
- Bank statements are gitignored by default ## Support For issues or questions, please open an issue on GitHub.
