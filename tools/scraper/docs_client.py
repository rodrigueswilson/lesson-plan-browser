import os
import os.path
import re
from typing import Dict, Any, List, Optional, Tuple

import httplib2
import requests
from google_auth_httplib2 import AuthorizedHttp
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
_GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"

_SPREADSHEET_URL_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")
_GID_RE = re.compile(r"gid=(\d+)")


def parse_google_spreadsheet_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (spreadsheet_id, gid_or_none) for a docs.google.com/spreadsheets link."""
    m = _SPREADSHEET_URL_RE.search(url)
    if not m:
        return None, None
    spreadsheet_id = m.group(1)
    gid_m = _GID_RE.search(url)
    gid = gid_m.group(1) if gid_m else None
    return spreadsheet_id, gid


# If modifying these scopes, delete the file credentials/token.json.
SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/presentations.readonly',
]


def _authorized_http_for_apis(creds) -> AuthorizedHttp:
    """Longer socket read timeout for huge curriculum Docs (tabs + content)."""
    timeout = int(os.environ.get("GOOGLE_API_HTTP_TIMEOUT_SEC", "300"))
    return AuthorizedHttp(creds, http=httplib2.Http(timeout=timeout))


class DocsClient:
    """Wrapper for Google Docs and Drive APIs."""
    
    def __init__(self, credentials_dir="credentials"):
        self.credentials_dir = os.path.join(os.path.dirname(__file__), credentials_dir)
        self.creds_path = os.path.join(self.credentials_dir, 'credentials.json')
        self.token_path = os.path.join(self.credentials_dir, 'token.json')
        self.creds = self._authenticate()
        _http = _authorized_http_for_apis(self.creds)

        self.docs_service = build("docs", "v1", http=_http, cache_discovery=False)
        self.drive_service = build("drive", "v3", http=_http, cache_discovery=False)
        self.slides_service = build("slides", "v1", http=_http, cache_discovery=False)

    def _authenticate(self):
        """Handles the OAuth2 flow and token management."""
        creds = None
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    raise FileNotFoundError(
                        f"Missing {self.creds_path}. Please follow the instructions in SETUP.md"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            os.makedirs(self.credentials_dir, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        return creds

    def _ensure_valid_creds(self) -> None:
        """Refresh OAuth token if expired and persist token.json."""
        if self.creds.valid:
            return
        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
            os.makedirs(self.credentials_dir, exist_ok=True)
            with open(self.token_path, "w", encoding="utf-8") as token:
                token.write(self.creds.to_json())
            return
        raise RuntimeError(
            "OAuth credentials are invalid; delete credentials/token.json and re-authorize (see SETUP.md)."
        )

    def fetch_spreadsheet_export_text(
        self, spreadsheet_id: str, gid: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Export a Google Sheet as CSV text using the user's OAuth token.
        Tries: authenticated /export?format=csv (with gid if provided), then without gid,
        then Drive files.export (first sheet only as CSV).
        """
        self._ensure_valid_creds()
        token = self.creds.token
        errors: List[str] = []

        def looks_like_csv_body(s: str) -> bool:
            t = s.lstrip()
            if not t:
                return False
            low = t[:200].lower()
            if low.startswith("<!doctype") or low.startswith("<html"):
                return False
            return True

        attempts: List[Optional[str]] = [gid, None] if gid else [None]
        for attempt_gid in attempts:
            try:
                q = "format=csv"
                if attempt_gid is not None:
                    q += f"&gid={attempt_gid}"
                url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?{q}"
                resp = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=120,
                )
                if resp.status_code == 200:
                    text = resp.content.decode("utf-8", errors="replace")
                    if looks_like_csv_body(text):
                        return True, text
                errors.append(
                    f"sheet export gid={attempt_gid} http={resp.status_code}"
                )
            except Exception as e:
                errors.append(f"sheet export gid={attempt_gid}: {e}")

        try:
            meta = self.get_drive_file_metadata(spreadsheet_id)
            mime = (meta.get("mimeType") or "").strip()
            if mime and mime != _GOOGLE_SHEET_MIME:
                errors.append(f"drive export skipped: mimeType={mime!r}")
            else:
                req = self.drive_service.files().export_media(
                    fileId=spreadsheet_id, mimeType="text/csv"
                )
                data = req.execute()
                raw = data if isinstance(data, bytes) else bytes(data)
                text = raw.decode("utf-8", errors="replace")
                if looks_like_csv_body(text):
                    return True, text
                errors.append("drive csv export body did not look like csv")
        except Exception as e:
            errors.append(f"drive csv export: {e}")

        return False, "; ".join(errors)

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Fetches a Google Doc by ID, including all tabs."""
        try:
            return self.docs_service.documents().get(
                documentId=document_id,
                includeTabsContent=True  # Ensure all tabs are returned
            ).execute()
        except HttpError as e:
            print(f"Error fetching doc {document_id}: {e}")
            return {}

    def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Fetches a Google Slides presentation by ID."""
        try:
            return self.slides_service.presentations().get(
                presentationId=presentation_id
            ).execute()
        except HttpError as e:
            print(f"Error fetching slides {presentation_id}: {e}")
            return {}

    def download_drive_file(self, file_id, output_path):
        """Downloads a file from Google Drive (e.g., PDF or PPTX)."""
        request = self.drive_service.files().get_media(fileId=file_id)
        with open(output_path, 'wb') as f:
            f.write(request.execute())

    def get_drive_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Returns id, name, mimeType (empty dict on error)."""
        try:
            return (
                self.drive_service.files()
                .get(fileId=file_id, fields="id,name,mimeType")
                .execute()
            )
        except HttpError as e:
            print(f"Error fetching Drive metadata for {file_id}: {e}")
            return {}

    def fetch_docx_for_curriculum_result(self, file_id: str, output_path: str) -> tuple[bool, str]:
        """
        Write a .docx suitable for table_extractor: either export a native Google Doc
        or download an uploaded Word file (Drive returns fileNotExportable for the latter).
        """
        meta = self.get_drive_file_metadata(file_id)
        mime = (meta.get("mimeType") or "").strip()
        if not mime:
            return False, "missing Drive metadata or mimeType"
        if mime == _GOOGLE_DOC_MIME:
            return self.export_document_result(file_id, output_path, _DOCX_MIME)
        if mime == _DOCX_MIME:
            try:
                self.download_drive_file(file_id, output_path)
                if os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
                    return True, ""
                return False, "downloaded file missing or empty"
            except Exception as e:
                return False, str(e)
        return False, f"unsupported mimeType for DOCX pipeline: {mime}"

    def export_document_result(
        self, document_id: str, output_path: str, mime_type: str = "text/html"
    ) -> tuple[bool, str]:
        """Exports a Google Doc; returns (success, error_message)."""
        try:
            request = self.drive_service.files().export_media(
                fileId=document_id, mimeType=mime_type
            )
            with open(output_path, "wb") as f:
                f.write(request.execute())
            return True, ""
        except Exception as e:
            return False, str(e)

    def export_document(self, document_id: str, output_path: str, mime_type: str = "text/html"):
        """Exports a Google Doc to a specified MIME type (HTML, DOCX, etc.)."""
        ok, err = self.export_document_result(document_id, output_path, mime_type)
        if not ok:
            print(f"Error exporting doc {document_id} to {mime_type}: {err}")
        return ok

    def get_document_json(self, document_id: str, output_path: str):
        """Saves the raw Google Docs API JSON structure to a file."""
        try:
            doc = self.get_document(document_id)
            if doc:
                with open(output_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(doc, f, indent=2)
                return True
        except Exception as e:
            print(f"Error saving JSON for {document_id}: {e}")
        return False

if __name__ == '__main__':
    # Initial test run to trigger auth
    try:
        client = DocsClient()
        print("Successfully authenticated and connected to Google APIs!")
    except Exception as e:
        print(f"Error during setup: {e}")
