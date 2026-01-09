# Deploying MeriNetWorth to Hugging Face Spaces This guide walks you through deploying your password-protected financial dashboard to Hugging Face Spaces. ## Prerequisites - [ ] Hugging Face account (create one at https://huggingface.co/join)
- [ ] `output/bank_data.json` file generated (run the Jupyter notebook)
- [ ] Git installed on your machine ## Step-by-Step Deployment ### 1. Create a Hugging Face Space 1. Go to https://huggingface.co/new-space
2. Fill in the details: - **Space name**: `merinetworth` (or your preferred name) - **License**: MIT - **Select SDK**: Choose **Streamlit**- **Space hardware**: CPU basic (free tier is sufficient) - **Visibility**: **Private**(recommended for financial data)
3. Click **Create Space**### 2. Prepare Your Repository **IMPORTANT: Security Check Before Deployment**Before pushing to Hugging Face, verify that sensitive data is protected: ```bash
# Check what will be committed
git status # Ensure data/ directory is NOT in the list
# Ensure .streamlit/secrets.toml is NOT in the list # If you see sensitive files, add them to .gitignore
echo "data/" >> .gitignore
echo ".streamlit/secrets.toml" >> .gitignore
``` ### 3. Clone Your Space Repository ```bash
# Clone the space (replace USERNAME and SPACE_NAME)
git clone https://huggingface.co/spaces/USERNAME/SPACE_NAME
cd SPACE_NAME
``` ### 4. Copy Your Project Files Copy these essential files to the cloned space directory: ```bash
# Copy from your MeriNetWorth directory
cp -r web/ /path/to/SPACE_NAME/
cp requirements.txt /path/to/SPACE_NAME/
cp README_HF.md /path/to/SPACE_NAME/README.md
cp -r .streamlit/ /path/to/SPACE_NAME/
cp -r output/ /path/to/SPACE_NAME/ # Contains bank_data.json
``` **Optional**: If you also want to include the data processing notebook:
```bash
cp -r notebooks/ /path/to/SPACE_NAME/
cp -r src/ /path/to/SPACE_NAME/
``` ### 5. Configure Secrets on Hugging Face **Method 1: Via Web Interface (Recommended)**1. Go to your Space: `https://huggingface.co/spaces/USERNAME/SPACE_NAME`
2. Click **Settings**tab
3. Scroll to **Repository secrets**
4. Click **Add a secret**
5. Add: - **Name**: `DASHBOARD_PASSWORD` - **Value**: Your secure password (e.g., `MySecureP@ss123!`)
6. Click **Add****Method 2: Via secrets.toml (Local Testing Only)**For local testing, create `.streamlit/secrets.toml`: ```bash
cd /path/to/SPACE_NAME
echo 'DASHBOARD_PASSWORD = "MySecureP@ss123!"' > .streamlit/secrets.toml
``` **Never commit**`.streamlit/secrets.toml` to git! ### 6. Update README.md Edit the `README.md` (copied from README_HF.md) in your space directory: ```markdown
---
title: MeriNetWorth Dashboard
emoji: colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: "1.28.0"
app_file: web/app.py
pinned: false
license: mit
---
``` Make sure `app_file: web/app.py` points to the correct path. ### 7. Commit and Push ```bash
cd /path/to/SPACE_NAME # Add all files
git add . # Commit
git commit -m "Initial deployment of MeriNetWorth dashboard" # Push to Hugging Face
git push
``` ### 8. Wait for Build - Go to your Space URL: `https://huggingface.co/spaces/USERNAME/SPACE_NAME`
- Watch the build logs in the **App**tab
- The build typically takes 2-3 minutes
- Once complete, you'll see the login screen ### 9. Test Your Deployment 1. Visit your Space URL
2. You should see the password login screen
3. Enter the password you set in secrets
4. Verify all features work correctly ## Updating Your Dashboard When you have new data or want to update the app: ```bash
cd /path/to/SPACE_NAME # Update files (e.g., new bank_data.json)
cp /path/to/MeriNetWorth/output/bank_data.json output/ # Commit and push
git add .
git commit -m "Update bank data for [Month Year]"
git push
``` The Space will automatically rebuild and redeploy. ## Troubleshooting ### Issue: "No data found" error **Solution**: Ensure `output/bank_data.json` exists in your Space repository ```bash
# Check if file exists
ls -la output/bank_data.json # If missing, copy it
cp /path/to/MeriNetWorth/output/bank_data.json output/
git add output/bank_data.json
git commit -m "Add bank data file"
git push
``` ### Issue: Password not working **Solution**: Verify the secret is set correctly 1. Go to Space Settings → Repository secrets
2. Check `DASHBOARD_PASSWORD` exists
3. Delete and re-create if needed
4. Wait a few seconds for the Space to reload ### Issue: "ModuleNotFoundError" **Solution**: Missing dependency in requirements.txt 1. Add the missing package to `requirements.txt`
2. Commit and push
3. Space will rebuild with new dependencies ### Issue: Path errors (FileNotFoundError) **Solution**: The app uses environment-based paths Check `web/app.py` line 93:
```python
BASE_PATH = Path(os.environ.get("BASE_PATH", "/Users/div/Projects/MeriNetWorth"))
``` For Hugging Face Spaces, you may need to adjust paths. Update to:
```python
BASE_PATH = Path(os.environ.get("BASE_PATH", "/home/user/app"))
``` Or set the `BASE_PATH` environment variable in Space settings. ### Issue: Space keeps restarting **Solution**: Check build logs for errors 1. Go to Space → Logs tab
2. Look for Python errors or missing files
3. Fix issues and push again ## Security Best Practices 1. **Use Private Space**: Keep your Space visibility set to "Private"
2. **Strong Password**: Use a strong, unique password (12+ characters, mixed case, numbers, symbols)
3. **Don't Commit Secrets**: Never commit passwords or API keys to git
4. **Sanitize Data**: Consider anonymizing account numbers in `bank_data.json` before deployment
5. **Regular Updates**: Update dependencies regularly for security patches
6. **Monitor Access**: Check Space analytics to see who's accessing your dashboard ## Optional: Custom Domain Hugging Face Spaces supports custom domains (Pro feature): 1. Upgrade to Hugging Face Pro
2. Go to Space Settings → Custom domain
3. Follow instructions to point your domain ## Need Help? - Hugging Face Spaces Docs: https://huggingface.co/docs/hub/spaces
- Streamlit Issues: https://github.com/streamlit/streamlit/issues
- Community Forum: https://discuss.huggingface.co/c/spaces ## Quick Reference Commands ```bash
# Clone space
git clone https://huggingface.co/spaces/USERNAME/SPACE_NAME # Update and push
cd SPACE_NAME
git add .
git commit -m "Update message"
git push # Test locally before pushing
streamlit run web/app.py
``` --- **Congratulations!**Your secure financial dashboard is now live on Hugging Face Spaces!
