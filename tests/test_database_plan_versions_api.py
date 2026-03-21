"""API tests for Settings > Database weekly plan versions (by-week, export, delete, admin backup)."""

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlmodel import Session

from backend.config import settings
from backend.database import plans as plans_module
from backend.database.plans import _recent_week_group_sort_key
from backend.schema import WeeklyPlan


@pytest.fixture
def client_plans(client_isolated_db):
    return client_isolated_db


def test_plans_by_week_lists_all_versions(client_plans, isolated_db):
    uid = isolated_db.create_user("Teacher A")
    week = "01/06-01/10"
    pid1 = isolated_db.create_weekly_plan(uid, week, "a.docx", "/w")
    pid2 = isolated_db.create_weekly_plan(uid, week, "b.docx", "/w")
    isolated_db.create_weekly_plan(uid, "02/03-02/07", "c.docx", "/w")

    r = client_plans.get(f"/api/users/{uid}/plans/by-week")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    multi = [g for g in data if len(g["plans"]) == 2]
    assert len(multi) == 1
    ids = {p["id"] for p in multi[0]["plans"]}
    assert ids == {pid1, pid2}
    singles = [g for g in data if len(g["plans"]) == 1]
    assert len(singles) >= 1


def test_export_plan_json(client_plans, isolated_db):
    uid = isolated_db.create_user("Teacher B")
    week = "04/01-04/05"
    pid = isolated_db.create_weekly_plan(uid, week, "out.docx", "/w")
    payload = {"days": [], "meta": "x"}
    isolated_db.update_weekly_plan(pid, lesson_json=payload)

    r = client_plans.get(f"/api/users/{uid}/plans/{pid}/export")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == pid
    assert body["user_id"] == uid
    assert body["week_of"]
    assert body["lesson_json"] == payload


def test_delete_plan(client_plans, isolated_db):
    uid = isolated_db.create_user("Teacher C")
    pid = isolated_db.create_weekly_plan(uid, "05/01-05/05", "z.docx", "/w")

    r = client_plans.delete(f"/api/users/{uid}/plans/{pid}")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert isolated_db.get_weekly_plan(pid) is None


def test_delete_plan_wrong_user_returns_404(client_plans, isolated_db):
    u1 = isolated_db.create_user("User One")
    u2 = isolated_db.create_user("User Two")
    pid = isolated_db.create_weekly_plan(u1, "06/01-06/05", "a.docx", "/w")

    r = client_plans.delete(f"/api/users/{u2}/plans/{pid}")
    assert r.status_code == 404


def test_admin_database_backup(client_plans, isolated_db, monkeypatch):
    db_path = Path(isolated_db.db_path)
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", db_path)

    r = client_plans.post("/api/admin/database/backup")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    backup_path = Path(data["backup_path"])
    assert backup_path.is_file()


def test_resolve_duplicates_keep_one(client_plans, isolated_db):
    uid = isolated_db.create_user("Teacher D")
    week = "07/01-07/05"
    p1 = isolated_db.create_weekly_plan(uid, week, "1.docx", "/w")
    p2 = isolated_db.create_weekly_plan(uid, week, "2.docx", "/w")

    r = client_plans.post(
        f"/api/users/{uid}/plans/resolve-duplicates",
        json={"week_of": week, "keep_plan_id": p2, "create_backup": False},
    )
    assert r.status_code == 200, r.text
    assert r.json()["removed_count"] == 1
    assert isolated_db.get_weekly_plan(p1) is None
    assert isolated_db.get_weekly_plan(p2) is not None


def test_recent_week_group_sort_key_mixed_naive_and_aware_iso():
    plans = [
        {"generated_at": "2025-01-01T00:00:00", "id": "a"},
        {"generated_at": "2025-06-15T00:00:00+00:00", "id": "b"},
    ]
    key = _recent_week_group_sort_key(plans)
    assert key[0] > datetime(2025, 1, 1)
    assert key[0] == datetime(2025, 6, 15)


def test_by_week_sort_recent_mixed_timezone_iso(client_plans, isolated_db):
    uid = isolated_db.create_user("Mixed ISO User")
    week = "01/06-01/10"
    p1 = isolated_db.create_weekly_plan(uid, week, "a.docx", "/w")
    p2 = isolated_db.create_weekly_plan(uid, week, "b.docx", "/w")
    with Session(isolated_db.engine) as s:
        o1 = s.get(WeeklyPlan, p1)
        o2 = s.get(WeeklyPlan, p2)
        o1.generated_at = datetime(2025, 1, 1, 12, 0, 0)
        o2.generated_at = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        s.add(o1)
        s.add(o2)
        s.commit()

    r = client_plans.get(f"/api/users/{uid}/plans/by-week?sort=recent")
    assert r.status_code == 200, r.text


def test_week_status_accepts_yy_w_week_path(client_plans, isolated_db):
    from urllib.parse import quote

    uid = isolated_db.create_user("YY Week User")
    week_label = "26 W13"
    isolated_db.create_weekly_plan(uid, week_label, "x.docx", "/w")
    enc = quote(week_label, safe="")
    r = client_plans.get(f"/api/plans/status/{uid}/{enc}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["week_of"] == "03/23-03/27"


def test_by_week_sort_school_vs_recent(client_plans, isolated_db):
    uid = isolated_db.create_user("Sort User")
    # Same school year (2024-25): March is later in the academic calendar than November
    w_nov = "11/10/2024-11/14/2024"
    w_mar = "03/03/2025-03/07/2025"
    p_nov = isolated_db.create_weekly_plan(uid, w_nov, "a.docx", "/w")
    p_mar = isolated_db.create_weekly_plan(uid, w_mar, "b.docx", "/w")
    with Session(isolated_db.engine) as s:
        o_nov = s.get(WeeklyPlan, p_nov)
        o_mar = s.get(WeeklyPlan, p_mar)
        o_mar.generated_at = datetime(2025, 1, 1)
        o_nov.generated_at = datetime(2025, 6, 15)
        s.add(o_nov)
        s.add(o_mar)
        s.commit()

    def _index_of_plan(data, pid):
        for i, g in enumerate(data):
            if any(p["id"] == pid for p in g["plans"]):
                return i
        raise AssertionError(f"plan {pid} not found")

    r_school = client_plans.get(f"/api/users/{uid}/plans/by-week?sort=school")
    assert r_school.status_code == 200
    data_s = r_school.json()
    assert _index_of_plan(data_s, p_mar) < _index_of_plan(data_s, p_nov)

    r_recent = client_plans.get(f"/api/users/{uid}/plans/by-week?sort=recent")
    assert r_recent.status_code == 200
    data_r = r_recent.json()
    assert _index_of_plan(data_r, p_nov) < _index_of_plan(data_r, p_mar)


def test_school_sort_ambiguous_week_uses_calendar_not_touch_year(
    client_plans, isolated_db, monkeypatch
):
    """Fall week without year must not sort above spring when both touched same day in 2026."""
    monkeypatch.setattr(
        plans_module, "_today_date_for_school_sort", lambda: date(2026, 3, 20)
    )
    uid = isolated_db.create_user("Ambiguous User")
    w_oct = "10/20-10/24"
    w_mar = "03/17-03/21"
    p_oct = isolated_db.create_weekly_plan(uid, w_oct, "a.docx", "/w")
    p_mar = isolated_db.create_weekly_plan(uid, w_mar, "b.docx", "/w")
    touch = datetime(2026, 3, 20, 12, 0, 0)
    with Session(isolated_db.engine) as s:
        o_oct = s.get(WeeklyPlan, p_oct)
        o_mar = s.get(WeeklyPlan, p_mar)
        o_oct.generated_at = touch
        o_mar.generated_at = touch
        s.add(o_oct)
        s.add(o_mar)
        s.commit()

    r = client_plans.get(f"/api/users/{uid}/plans/by-week?sort=school")
    assert r.status_code == 200
    data = r.json()

    def _ix(pid):
        for i, g in enumerate(data):
            if any(p["id"] == pid for p in g["plans"]):
                return i
        raise AssertionError(pid)

    assert _ix(p_mar) < _ix(p_oct)


def test_school_sort_ambiguous_september_below_near_future_march(
    client_plans, isolated_db, monkeypatch
):
    """
    In spring, Sep without year must map to last fall, not next Sep (closer in raw days).

    Regression: Mar 2026 ref used to rank Sep 15 as Sep 2026 above Mar 23 2026.
    """
    monkeypatch.setattr(
        plans_module, "_today_date_for_school_sort", lambda: date(2026, 3, 18)
    )
    uid = isolated_db.create_user("SepVsMar User")
    weeks = [
        ("09/15-09/19", "s1.docx"),
        ("09/08-09/12", "s2.docx"),
        ("09/02-09/05", "s3.docx"),
        ("03/23-03/27", "m.docx"),
    ]
    pids = [isolated_db.create_weekly_plan(uid, w, fn, "/w") for w, fn in weeks]

    r = client_plans.get(f"/api/users/{uid}/plans/by-week?sort=school")
    assert r.status_code == 200
    data = r.json()

    def _ix(pid):
        for i, g in enumerate(data):
            if any(p["id"] == pid for p in g["plans"]):
                return i
        raise AssertionError(pid)

    ix_mar = _ix(pids[3])
    assert ix_mar < _ix(pids[0])
    assert ix_mar < _ix(pids[1])
    assert ix_mar < _ix(pids[2])


def test_plans_within_week_newest_first(client_plans, isolated_db):
    uid = isolated_db.create_user("Order User")
    week = "10/01-10/05"
    p_old = isolated_db.create_weekly_plan(uid, week, "a.docx", "/w")
    p_new = isolated_db.create_weekly_plan(uid, week, "b.docx", "/w")
    r = client_plans.get(f"/api/users/{uid}/plans/by-week?sort=school")
    assert r.status_code == 200
    grp = next(g for g in r.json() if any(p["id"] == p_old for p in g["plans"]))
    assert grp["plans"][0]["id"] == p_new
    assert grp["plans"][1]["id"] == p_old


def test_restore_from_export_after_delete(client_plans, isolated_db):
    uid = isolated_db.create_user("Restore User")
    pid = isolated_db.create_weekly_plan(uid, "08/01-08/05", "x.docx", "/w")
    isolated_db.update_weekly_plan(pid, lesson_json={"restored": True}, status="completed")

    r_exp = client_plans.get(f"/api/users/{uid}/plans/{pid}/export")
    assert r_exp.status_code == 200
    export = r_exp.json()

    r_del = client_plans.delete(f"/api/users/{uid}/plans/{pid}")
    assert r_del.status_code == 200
    assert isolated_db.get_weekly_plan(pid) is None

    r_rest = client_plans.post(
        f"/api/users/{uid}/plans/restore-from-export", json=export
    )
    assert r_rest.status_code == 200, r_rest.text
    assert r_rest.json() == {"success": True, "plan_id": pid}
    back = isolated_db.get_weekly_plan(pid)
    assert back is not None
    assert back.lesson_json == {"restored": True}


def test_restore_conflict_409_without_replace(client_plans, isolated_db):
    uid = isolated_db.create_user("Conflict User")
    pid = isolated_db.create_weekly_plan(uid, "09/01-09/05", "z.docx", "/w")
    r_exp = client_plans.get(f"/api/users/{uid}/plans/{pid}/export")
    export = r_exp.json()
    r2 = client_plans.post(
        f"/api/users/{uid}/plans/restore-from-export", json=export
    )
    assert r2.status_code == 409


def test_restore_replace_existing(client_plans, isolated_db):
    uid = isolated_db.create_user("Replace User")
    pid = isolated_db.create_weekly_plan(uid, "11/01-11/05", "o.docx", "/w")
    isolated_db.update_weekly_plan(pid, lesson_json={"v": 1})
    r_exp = client_plans.get(f"/api/users/{uid}/plans/{pid}/export")
    export = r_exp.json()
    export["lesson_json"] = {"v": 2}
    export["replace_existing"] = True
    r = client_plans.post(
        f"/api/users/{uid}/plans/restore-from-export", json=export
    )
    assert r.status_code == 200, r.text
    assert isolated_db.get_weekly_plan(pid).lesson_json == {"v": 2}
