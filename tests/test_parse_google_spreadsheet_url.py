"""Unit tests for Google Sheets URL parsing (scraper HTML path)."""

from tools.scraper.docs_client import parse_google_spreadsheet_url


def test_parse_spreadsheet_url_with_gid_in_query_and_fragment() -> None:
    url = (
        "https://docs.google.com/spreadsheets/d/"
        "14m8cZc9PK1zhY4xwy9N-5itFIOCerkiIUc1YEdoHmnM/edit?"
        "gid=540639405#gid=540639405"
    )
    sid, gid = parse_google_spreadsheet_url(url)
    assert sid == "14m8cZc9PK1zhY4xwy9N-5itFIOCerkiIUc1YEdoHmnM"
    assert gid == "540639405"


def test_parse_spreadsheet_url_no_gid() -> None:
    url = "https://docs.google.com/spreadsheets/d/abc123_def/edit"
    sid, gid = parse_google_spreadsheet_url(url)
    assert sid == "abc123_def"
    assert gid is None


def test_parse_non_spreadsheet_url() -> None:
    assert parse_google_spreadsheet_url("https://example.com/page") == (None, None)
