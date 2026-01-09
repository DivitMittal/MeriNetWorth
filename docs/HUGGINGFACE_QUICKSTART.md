# Hugging Face Spaces - Quick Start Guide ## TL;DR - Fastest Deployment Path ```bash
# 1. Create Space on HuggingFace.co
# Visit: https://huggingface.co/new-space
# Choose: Streamlit SDK, Private visibility # 2. Clone the space
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME # 3. Copy essential files
cp -r /Users/div/Projects/Misc/MeriNetWorth/web .
cp /Users/div/Projects/Misc/MeriNetWorth/requirements.txt .
cp /Users/div/Projects/Misc/MeriNetWorth/README_HF.md README.md
cp -r /Users/div/Projects/Misc/MeriNetWorth/.streamlit .
cp -r /Users/div/Projects/Misc/MeriNetWorth/output . # 4. Push to Hugging Face
git add .
git commit -m "Initial deployment"
git push # 5. Set password in Space Settings
# Go to: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/settings
# Add secret: DASHBOARD_PASSWORD = your_secure_password # Done! Visit your space URL
``` ## File Checklist Before pushing, ensure you have: - `web/app.py` - Main dashboard (with authentication)
- `requirements.txt` - Python dependencies
- `README.md` - Space metadata and description
- `.streamlit/config.toml` - Streamlit configuration
- `output/bank_data.json` - Your financial data
- **NOT**`data/` directory (contains raw bank statements)
- **NOT**`.streamlit/secrets.toml` (contains password) ## Security Checklist Before deployment: - [ ] Space visibility set to **Private**
- [ ] `data/` directory is NOT being pushed (check .gitignore)
- [ ] `.streamlit/secrets.toml` is NOT being pushed
- [ ] Strong password set in Hugging Face secrets (12+ chars)
- [ ] Verified no sensitive account numbers in `bank_data.json` ## Testing Locally First ```bash
# Set test password
export DASHBOARD_PASSWORD="test123" # Or use the provided script
./test_auth_local.sh # Visit http://localhost:8501 and test
``` ## Common First-Time Issues ### 1. "No data found" error
```bash
# Ensure output directory exists with data
ls output/bank_data.json # Should show the file
``` ### 2. Can't find app file
```markdown
# In README.md, ensure this line is correct:
app_file: web/app.py
``` ### 3. Password not working
- Wait 30 seconds after setting the secret
- Try refreshing the browser
- Check Space logs for errors ## Space Settings You Need | Setting | Value |
|---------|-------|
| SDK | Streamlit |
| SDK Version | 1.28.0 or higher |
| Visibility | Private |
| Hardware | CPU basic (free) |
| **Secret: DASHBOARD_PASSWORD**| Your secure password | ## Your Space URLs After deployment, you'll have: - **App**: `https://huggingface.co/spaces/USERNAME/SPACE_NAME`
- **Settings**: `https://huggingface.co/spaces/USERNAME/SPACE_NAME/settings`
- **Logs**: Check the "Logs" tab in your space ## Need Help? See full guide: [DEPLOYMENT.md](DEPLOYMENT.md)
