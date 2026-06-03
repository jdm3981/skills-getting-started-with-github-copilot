import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module


# Snapshot of original activities to reset between tests
_ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: reset the in-memory activities for test isolation
    app_module.activities = copy.deepcopy(_ORIGINAL_ACTIVITIES)
    yield


@pytest.fixture
def client():
    # Arrange: provide a TestClient for the app
    return TestClient(app_module.app)


def test_get_activities(client):
    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success(client):
    activity = "Chess Club"
    test_email = "newstudent@mergington.edu"

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": test_email})

    # Assert
    assert resp.status_code == 200
    assert test_email in resp.json().get("message", "")

    # Verify participant was added
    data = client.get("/activities").json()
    assert test_email in data[activity]["participants"]


def test_signup_duplicate(client):
    activity = "Programming Class"
    test_email = "duplicate@mergington.edu"

    # Act: first signup should succeed
    r1 = client.post(f"/activities/{activity}/signup", params={"email": test_email})
    assert r1.status_code == 200

    # Act: second signup should fail with 400
    r2 = client.post(f"/activities/{activity}/signup", params={"email": test_email})
    assert r2.status_code == 400


def test_signup_missing_activity(client):
    # Act
    resp = client.post("/activities/NoSuchClub/signup", params={"email": "a@b.com"})

    # Assert
    assert resp.status_code == 404


def test_unregister_success(client):
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert resp.status_code == 200
    data = client.get("/activities").json()
    assert email not in data[activity]["participants"]


def test_unregister_not_found(client):
    # Act: non-existent email
    resp = client.delete("/activities/Chess Club/participants", params={"email": "noone@x.com"})
    assert resp.status_code == 404

    # Act: non-existent activity
    resp2 = client.delete("/activities/Nonexistent/participants", params={"email": "a@b.com"})
    assert resp2.status_code == 404
