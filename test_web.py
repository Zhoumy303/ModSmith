"""Test the Web UI backend API."""

from fastapi.testclient import TestClient

from modsmith.web.app import app

client = TestClient(app)


def test_index():
    """Home page returns HTML."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "ModSmith" in resp.text


def test_generate_returns_task_id():
    """Creating a task returns a task_id."""
    resp = client.post("/api/generate", json={
        "description": "Create a ruby",
        "mod_id": "test-mod",
        "package_name": "com.test",
    })
    assert resp.status_code == 200
    assert "task_id" in resp.json()