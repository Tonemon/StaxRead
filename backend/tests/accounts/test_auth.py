import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
    )


@pytest.mark.django_db
class TestLogin:
    def test_login_returns_access_and_refresh_tokens(self, api_client, user):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "securepassword123"},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password_rejected(self, api_client, user):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == 401

    def test_login_nonexistent_user_rejected(self, api_client, db):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "nobody", "password": "whatever"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_returns_new_access_token(self, api_client, user):
        login = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "securepassword123"},
            format="json",
        )
        refresh = login.data["refresh"]
        response = api_client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data

    def test_invalid_refresh_token_rejected(self, api_client, db):
        response = api_client.post(
            reverse("token_refresh"),
            {"refresh": "notarealtoken"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, user):
        login = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "securepassword123"},
            format="json",
        )
        refresh = login.data["refresh"]
        response = api_client.post(
            reverse("token_blacklist"),
            {"refresh": refresh},
            format="json",
        )
        assert response.status_code == 200

        # Blacklisted token should now be rejected
        retry = api_client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )
        assert retry.status_code == 401



@pytest.mark.django_db
class TestUserModel:
    def test_user_has_uuid_primary_key(self, user):
        import uuid
        assert isinstance(user.pk, uuid.UUID)

    def test_user_is_not_superuser_by_default(self, user):
        assert not user.is_superuser

    def test_superuser_has_is_superuser_flag(self, superuser):
        assert superuser.is_superuser
