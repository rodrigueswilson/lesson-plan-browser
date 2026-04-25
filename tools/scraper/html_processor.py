from typing import Any, Optional

import requests
from bs4 import BeautifulSoup


class HTMLProcessor:
    """Parses HTML pages to extract curriculum content."""

    @staticmethod
    def _normalize_plain_text(text: str) -> str:
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    def extract_content(self, url: str, google_client: Optional[Any] = None) -> str:
        """
        Fetches a URL and extracts the main text content.

        For Google Sheets links, pass google_client (DocsClient): uses OAuth to export CSV
        (same access as the browser). Plain requests return 401 for private sheets.
        """
        if google_client is not None:
            from tools.scraper.docs_client import parse_google_spreadsheet_url

            sid, gid = parse_google_spreadsheet_url(url)
            if sid:
                ok, text = google_client.fetch_spreadsheet_export_text(sid, gid)
                if ok and text.strip():
                    return self._normalize_plain_text(text)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            return self._normalize_plain_text(text)
        except Exception as e:
            print(f"Error processing HTML {url}: {e}")
            return ""

if __name__ == "__main__":
    # Test with a dummy URL
    processor = HTMLProcessor()
    # processor.extract_content("https://example.com")
