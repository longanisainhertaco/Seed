import atexit
import os
import tempfile

from fastapi.testclient import TestClient

# Use isolated database for integration-style route checks
tmp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_PATH"] = tmp_db.name

from app.main import app  # noqa: E402

client = TestClient(app)


def _cleanup_db():
    tmp_db.close()
    if os.path.exists(tmp_db.name):
        os.unlink(tmp_db.name)


atexit.register(_cleanup_db)


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_import_upload_rejects_non_excel():
    response = client.post(
        "/import/upload",
        files={"file": ("bad.txt", b"content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Please upload an Excel file" in response.text
