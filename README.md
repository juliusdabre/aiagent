# AU Property Finder — Suburb Filters + Google Sheets Export (Streamlit Cloud Ready)

This app scrapes realestate.com.au for listings by **state** and **price range**.
It now supports:
- ✅ **Suburb filter** after results load
- ✅ **Export to Google Sheets** (service account)

## Deploy to Streamlit Cloud
1. Push these files to a GitHub repo (root):
   - `app.py`
   - `agents/scraper.py`
   - `requirements.txt`
   - `postBuild`
2. In Streamlit Cloud, set **App file** to `app.py`.
3. Add **Secrets** (`Settings → Secrets`) with your **Google service account JSON**:

```toml
# .streamlit/secrets.toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...yourkey...\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"
```

> **Important:** Share the destination Google Sheet with the service account email (or let the app create a new spreadsheet).

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
streamlit run app.py
```

## Usage
1. Pick **state**, **min/max price**, and **pages** to scan.
2. After results appear, use the **Suburb** multiselect to refine.
3. Enter **Spreadsheet** and **Worksheet** names → click **Export**.

---
*Please respect the target website’s Terms of Service and add delays if you increase the crawl size.*