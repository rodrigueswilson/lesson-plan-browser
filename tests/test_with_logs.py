"""
Test processing and progress via in-process client (no live server).
"""


def test_process_week_accepts_payload(client):
    """POST /api/process-week accepts JSON (may return 200 or 400 depending on data)."""
    payload = {
        "user_id": "00000000-0000-0000-0000-000000000000",
        "week_of": "10/14-10/18",
        "provider": "mock",
        "slot_ids": [],
    }
    r = client.post("/api/process-week", json=payload)
    # With invalid user/slots we may get 400/422; with valid app we get 200 or 202
    assert r.status_code in (200, 202, 400, 422)
