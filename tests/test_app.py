import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from scoring import MAX_SCORE, fit_score  # noqa: E402

VALID = {
    "full_name": "Test Founder", "email": "founder@example.com", "linkedin": "https://linkedin.com/in/test",
    "phone": "050-000-0000", "role_in_company": "CEO", "company_name": "TestCo", "primary_sector": "AI",
    "startup_stage": "Seed", "cofounders_count": "2", "time_working_on_startup": "6_24",
    "gain": ["Mentoring"], "consent": "on",
}


@pytest.fixture
def client(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True})
    return app.test_client()


def csrf(client, path="/apply"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'(?:name="csrf" value|name="csrf-token" content)="([^"]+)"', html).group(1)


def login(client, password="demo"):
    return client.post("/admin/login", data={"password": password, "csrf": csrf(client, "/admin/login")})


def test_public_pages_load(client):
    for path in ["/", "/apply", "/submitted", "/community"]:
        assert client.get(path).status_code == 200


def test_admin_requires_login(client):
    assert client.get("/admin").status_code == 302
    assert client.get("/admin/export.csv").status_code == 302
    assert login(client, "wrong").status_code == 200
    assert client.get("/admin").status_code == 302


def test_valid_submission_is_stored(client):
    resp = client.post("/apply", data={**VALID, "csrf": csrf(client)})
    assert resp.status_code == 302
    login(client)
    assert "TestCo" in client.get("/admin").get_data(as_text=True)


def test_submission_without_csrf_is_rejected(client):
    assert client.post("/apply", data=VALID).status_code == 400


def test_invalid_submission_shows_errors(client):
    data = {**VALID, "email": "not-an-email", "startup_stage": "Series Z", "csrf": csrf(client)}
    data.pop("consent")
    resp = client.post("/apply", data=data)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 400
    assert "valid email" in html and "Consent is required" in html


def test_real_submissions_are_masked_in_demo_mode(client):
    client.post("/apply", data={**VALID, "csrf": csrf(client)})
    login(client)
    html = client.get("/admin").get_data(as_text=True)
    assert "founder@example.com" not in html
    assert "f***@example.com" in html


def test_intro_request(client):
    token = csrf(client, "/community")
    ok = client.post("/community/intro", headers={"X-CSRF-Token": token},
                     data={"target_type": "mentor", "target_name": "Dana Rosen", "email": "a@b.com", "message": "Hi"})
    bad = client.post("/community/intro", headers={"X-CSRF-Token": token},
                      data={"target_type": "mentor", "target_name": "Nobody", "email": "a@b.com", "message": "Hi"})
    assert ok.json["ok"] and bad.status_code == 400


def test_fit_score():
    best = {"startup_stage": "Seed", "cofounders_count": "3", "time_working_on_startup": "6_24",
            "current_customers": "Pilots", "raised_funding": "Yes"}
    assert fit_score(best) == MAX_SCORE
    assert fit_score({}) == 0
    assert fit_score({**best, "time_working_on_startup": "gt_24"}) == MAX_SCORE - 2
