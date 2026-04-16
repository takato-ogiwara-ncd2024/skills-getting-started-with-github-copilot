"""Backend FastAPI tests for the Mergington High School API."""

import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)
original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def restore_activities():
    """Reset activity data for each test to keep state isolated."""
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


class TestActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self):
        # Arrange
        expected_activities = {"Chess Club", "Programming Class", "Gym Class"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert expected_activities.issubset(set(data.keys()))

    def test_get_activities_returns_activity_with_required_fields(self):
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activity = response.json()[activity_name]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    def test_signup_adds_participant_to_activity(self):
        # Arrange
        activity_name = "Chess Club"
        email = "new_student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        assert email in activities[activity_name]["participants"]

    def test_signup_returns_400_for_duplicate_signup(self):
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up for this activity"


class TestRemoveParticipantEndpoint:
    def test_remove_participant_removes_from_activity(self):
        # Arrange
        activity_name = "Programming Class"
        email = "remove_student@mergington.edu"
        activities[activity_name]["participants"].append(email)

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Removed {email} from {activity_name}"}
        assert email not in activities[activity_name]["participants"]

    def test_remove_participant_returns_404_for_nonexistent_participant(self):
        # Arrange
        activity_name = "Programming Class"
        email = "missing_student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"


class TestRootEndpoint:
    def test_root_redirects_to_static_html(self):
        # Arrange
        # No setup needed.

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
