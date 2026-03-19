import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db

# Use SQLite in-memory DB for tests (no MySQL needed)
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

TEST_USER = {"name": "Test User", "email": "test@example.com", "password": "secret123"}


def register_and_login():
    client.post("/api/auth/register", json=TEST_USER)
    res = client.post("/api/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    return res.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

def test_register_success():
    res = client.post("/api/auth/register", json=TEST_USER)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == TEST_USER["email"]
    assert data["name"] == TEST_USER["name"]


def test_register_duplicate_email():
    client.post("/api/auth/register", json=TEST_USER)
    res = client.post("/api/auth/register", json=TEST_USER)
    assert res.status_code == 400


def test_login_success():
    client.post("/api/auth/register", json=TEST_USER)
    res = client.post("/api/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password():
    client.post("/api/auth/register", json=TEST_USER)
    res = client.post("/api/auth/login", data={"username": TEST_USER["email"], "password": "wrongpass"})
    assert res.status_code == 401


def test_get_me():
    token = register_and_login()
    res = client.get("/api/auth/me", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["email"] == TEST_USER["email"]


# ── Application Tests ─────────────────────────────────────────────────────────

def test_create_application():
    token = register_and_login()
    payload = {"company": "Google", "position": "Software Engineer", "status": "applied"}
    res = client.post("/api/applications/", json=payload, headers=auth_header(token))
    assert res.status_code == 201
    assert res.json()["company"] == "Google"


def test_list_applications():
    token = register_and_login()
    client.post("/api/applications/", json={"company": "Google", "position": "SWE"}, headers=auth_header(token))
    client.post("/api/applications/", json={"company": "Meta", "position": "Backend Eng"}, headers=auth_header(token))
    res = client.get("/api/applications/", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_filter_by_status():
    token = register_and_login()
    client.post("/api/applications/", json={"company": "A", "position": "Eng", "status": "applied"}, headers=auth_header(token))
    client.post("/api/applications/", json={"company": "B", "position": "Eng", "status": "rejected"}, headers=auth_header(token))
    res = client.get("/api/applications/?status=rejected", headers=auth_header(token))
    assert res.json()["total"] == 1


def test_update_application():
    token = register_and_login()
    res = client.post("/api/applications/", json={"company": "Google", "position": "SWE"}, headers=auth_header(token))
    app_id = res.json()["id"]
    res2 = client.patch(f"/api/applications/{app_id}", json={"status": "interview"}, headers=auth_header(token))
    assert res2.status_code == 200
    assert res2.json()["status"] == "interview"


def test_delete_application():
    token = register_and_login()
    res = client.post("/api/applications/", json={"company": "Google", "position": "SWE"}, headers=auth_header(token))
    app_id = res.json()["id"]
    del_res = client.delete(f"/api/applications/{app_id}", headers=auth_header(token))
    assert del_res.status_code == 204


def test_stats_endpoint():
    token = register_and_login()
    client.post("/api/applications/", json={"company": "A", "position": "Eng", "status": "applied"}, headers=auth_header(token))
    client.post("/api/applications/", json={"company": "B", "position": "Eng", "status": "offer"}, headers=auth_header(token))
    res = client.get("/api/applications/stats", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["total"] == 2
    assert res.json()["offer"] == 1


def test_unauthorized_access():
    res = client.get("/api/applications/")
    assert res.status_code == 401


# ── Interview Tests ───────────────────────────────────────────────────────────

def test_create_interview():
    token = register_and_login()
    app_res = client.post("/api/applications/", json={"company": "Google", "position": "SWE"}, headers=auth_header(token))
    app_id = app_res.json()["id"]
    payload = {"interview_type": "Technical", "scheduled_at": "2025-09-01T10:00:00"}
    res = client.post(f"/api/applications/{app_id}/interviews/", json=payload, headers=auth_header(token))
    assert res.status_code == 201
    assert res.json()["interview_type"] == "Technical"


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ── CSV Import Tests ──────────────────────────────────────────────────────────

LINKEDIN_CSV = """Company Name,Job Title,Job URL,Applied On,Status,Notes,Location
Google,Software Engineer,https://linkedin.com/jobs/1,2024-01-15,Applied,Great company,Singapore
Meta,Backend Engineer,https://linkedin.com/jobs/2,2024-01-20,Interviewing,Good culture,Remote
Shopee,Data Analyst,https://linkedin.com/jobs/3,2024-01-22,Rejected,,Singapore
"""

JOBSTREET_CSV = """Company,Position,Location,Job URL,Date Applied,Application Status,Notes
Grab,Mobile Developer,Singapore,https://jobstreet.com/1,15/01/2024,Shortlisted,Promising
Sea Limited,DevOps Engineer,Singapore,https://jobstreet.com/2,20/01/2024,Under Review,
Lazada,Frontend Engineer,Remote,https://jobstreet.com/3,22/01/2024,New,Applied via referral
"""

INVALID_CSV = """Col1,Col2,Col3
foo,bar,baz
"""


def test_import_linkedin_csv():
    token = register_and_login()
    files = {"file": ("linkedin_export.csv", LINKEDIN_CSV.encode(), "text/csv")}
    res = client.post("/api/import/csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["platform_detected"] == "linkedin"
    assert data["imported"] == 3
    assert data["skipped_duplicates"] == 0


def test_import_jobstreet_csv():
    token = register_and_login()
    files = {"file": ("jobstreet_export.csv", JOBSTREET_CSV.encode(), "text/csv")}
    res = client.post("/api/import/csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["platform_detected"] == "jobstreet"
    assert data["imported"] == 3


def test_import_skips_duplicates():
    token = register_and_login()
    files = {"file": ("linkedin_export.csv", LINKEDIN_CSV.encode(), "text/csv")}
    client.post("/api/import/csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    # Import same file again
    res = client.post("/api/import/csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    data = res.json()
    assert data["imported"] == 0
    assert data["skipped_duplicates"] == 3


def test_import_invalid_format():
    token = register_and_login()
    files = {"file": ("bad.csv", INVALID_CSV.encode(), "text/csv")}
    res = client.post("/api/import/csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert res.status_code == 422


def test_import_wrong_file_type():
    token = register_and_login()
    files = {"file": ("export.txt", b"some text", "text/plain")}
    res = client.post("/api/import/csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert res.status_code == 400


def test_import_sample_endpoint_linkedin():
    res = client.get("/api/import/csv/sample/linkedin")
    assert res.status_code == 200
    assert res.json()["platform"] == "LinkedIn"


def test_import_sample_endpoint_jobstreet():
    res = client.get("/api/import/csv/sample/jobstreet")
    assert res.status_code == 200
    assert res.json()["platform"] == "JobStreet"


def test_import_unauthorized():
    files = {"file": ("linkedin_export.csv", LINKEDIN_CSV.encode(), "text/csv")}
    res = client.post("/api/import/csv", files=files)
    assert res.status_code == 401

