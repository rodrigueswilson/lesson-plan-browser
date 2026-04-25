# Scraper Setup Guide

To use the curriculum scraper with your Board of Education account, you need to set up a Google Cloud Project and obtain OAuth2 credentials.

## Step 1: Create a Google Cloud Project
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Click **Select a project** > **New Project**.
3.  Give it a name (e.g., `LP-Curriculum-Scraper`) and click **Create**. 
    *   **Project Name vs. ID**: The **Name** is a human-readable label (changeable). The **ID** is a globally unique, machine-readable identifier (permanent).
    *   **Tip**: Use your **personal/regular** Google account for this project, as Board of Ed accounts often have project creation restricted.

## Step 2: Enable APIs
1.  In the sidebar, go to **APIs & Services** > **Library**.
2.  Search for and **Enable** the following:
    - **Google Docs API**
    - **Google Drive API**
    - **Google Slides API** (optional but recommended — linked Slides in unit docs fail with 403 if disabled)
    *   *Note: It may take a few minutes for these changes to take effect.*

Private **Google Sheets** links in curriculum docs are exported as CSV using your OAuth token (`drive.readonly`); no separate Sheets API enable step is required for that export path.

## Step 3: Configure OAuth Consent Screen
1.  Go to **APIs & Services** > **OAuth consent screen**.
2.  Select **External** and click **Create**.
    *   **Internal**: Restricted to your organization's users (often blocked).
    *   **External**: Allows you to manually add "Test Users" (like your Board of Ed email).
3.  Fill in the required fields (App name, User support email, Developer contact info).
4.  In the **Scopes** step, add these "Least Privilege" scopes:
    - `https://www.googleapis.com/auth/documents.readonly` (To read curriculum text)
    - `https://www.googleapis.com/auth/drive.readonly` (To find and download linked PDFs)
5.  **Crucial**: In the **Test users** step, click **Add Users** and enter your **Board of Education email address**.

## Step 4: Create Credentials
1.  Go to **APIs & Services** > **Credentials**.
2.  Click **Create Credentials** > **OAuth client ID**.
3.  Select **Desktop app** as the Application type. 
    *   **Why?** This is required for local Python scripts that need to open your browser for the "one-click" authentication flow.
4.  Provide a name and click **Create**.
5.  After creation, click **Download JSON**.
6.  Rename the file to `credentials.json` and save it here:
    `d:\LP\tools\scraper\credentials\credentials.json`
    *   > [!CAUTION]
        > **Security**: Never share `credentials.json` or `token.json` files. These contain sensitive keys used to access your Google account. We have added a `.gitignore` to protect them.

## Step 5: Run the Authorization
We recommend using a Python virtual environment to keep dependencies isolated.

### Windows (PowerShell)
```powershell
python -m venv .venv                       # Create virtual environment
.\.venv\Scripts\Activate.ps1               # Activate
pip install -r d:\LP\tools\scraper\requirements.txt
python d:\LP\tools\scraper\docs_client.py
```

### Windows (Command Prompt)
```cmd
python -m venv .venv                       # Create virtual environment
.venv\Scripts\activate.bat                 # Activate
pip install -r d:\LP\tools\scraper\requirements.txt
python d:\LP\tools\scraper\docs_client.py
```

### Linux / macOS
```bash
python3 -m venv .venv                      # Create virtual environment
source .venv/bin/activate                  # Activate
pip install -r d:/LP/tools/scraper/requirements.txt
python3 d:/LP/tools/scraper/docs_client.py
```

### Authorization Note
A browser window will open. Select your Board of Education account and click **Allow**. A `token.json` file will be created in the `credentials/` folder. This file stores your active session tokens, so you won't need to log in again until they expire or are revoked.

## Discovering linked unit Doc ids (pacing / curriculum hub)

Some grades use a **parent Google Doc** (pacing guide or curriculum guide) that links to each unit’s teacher-guide Doc. To list every linked `docs.google.com/document/d/...` id from such a hub (after OAuth works):

```text
python tools/scraper/list_gdoc_links_in_document.py --doc-id <HUB_FILE_ID>
```

Use the output to fill `reference_docs/scraped_registry.json` and `tools/db/g2_math_corpus.py` (or the right grade/subject corpus) once you match ids to unit titles in Drive.

## Troubleshooting
- **"LP-Curriculum-Scraper has not completed the Google verification process" / `Error 403: access_denied`**: The OAuth client is in **Testing** mode. Only addresses listed under **OAuth consent screen → Audience (or Test users) → Add users** may sign in. Add the **exact** Google account you use in the browser (personal vs work), save, wait a minute, delete `credentials/token.json`, and run the scraper again. The account that owns the Cloud project is **not** automatically a test user unless it appears in that list.
- **"API not enabled"**: Re-check Step 2. API enablement can sometimes take 5-10 minutes to propagate across Google's servers.
- **"Access Blocked: Project has not been configured"**: 
    1. Double-check that your Board of Ed email was added as a **Test User** in Step 3.
    2. Ensure the consent screen is set to **External**.
    3. Wait a few minutes for configuration changes to sync.
- **"Insufficient permissions"**: 
    1. Ensure the correct "ReadOnly" scopes were added in Step 3.
    2. Verify your Board of Ed account itself has "View" permissions for the specific Google Doc/File you are trying to access.
    3. Delete `tools/scraper/credentials/token.json` and run the script again to refresh your session.
