# Hugging Face Spaces - Quick Start Guide

## Fastest Deployment Path

```bash
# 1. Create a private Streamlit Space at https://huggingface.co/new-space
# 2. Clone the Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME

# 3. Copy deployable files from MeriNetWorth
cp -r /path/to/MeriNetWorth/web .
cp -r /path/to/MeriNetWorth/src .
cp -r /path/to/MeriNetWorth/output .
cp /path/to/MeriNetWorth/requirements.txt .
cp /path/to/MeriNetWorth/docs/README_HF.md README.md

# 4. Push to Hugging Face
git add .
git commit -m "Deploy dashboard"
git push
```

## File Checklist

Before pushing, ensure the Space contains:

- `web/app.py`
- `src/`
- `requirements.txt`
- `README.md`
- `output/*.json`

Do not push:

- `data/`
- `.streamlit/secrets.toml`
- Raw bank, equity, MF, pension, or liability statements

## Security Checklist

- [ ] Space visibility is **Private**
- [ ] `data/` is not included
- [ ] No secrets files are included
- [ ] `DASHBOARD_PASSWORD` is configured in Space secrets
- [ ] Output JSON files have been reviewed for sensitive fields before upload

## Test Locally First

```bash
export DASHBOARD_PASSWORD="test123"
python process_all.py
streamlit run web/app.py
```

Visit `http://localhost:8501`, enter the password, and confirm the dashboard renders.

## Common Issues

### “No data found”

Confirm `output/bank_data.json` exists before deployment.

### App file not found

Ensure the Space README metadata points to:

```yaml
app_file: web/app.py
```

### Password not working

- Wait for the Space to restart after setting the secret.
- Refresh the browser.
- Check Space logs for environment-variable errors.

## Space Settings

| Setting | Value |
| --- | --- |
| SDK | Streamlit |
| SDK Version | 1.28.0 or higher |
| Visibility | Private |
| Hardware | CPU basic |
| Secret | `DASHBOARD_PASSWORD` |
