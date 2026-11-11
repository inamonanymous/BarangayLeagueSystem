import pytest

from app import create_app
from app.domain.models.roles import Role
from app.domain.models.users import User
from app.extensions import db


@pytest.fixture()
def client():
    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()

        admin_role = Role(name="Administrator", description="System administrator")
        encoder_role = Role(name="Encoder", description="Game encoder")
        db.session.add_all([admin_role, encoder_role])
        db.session.flush()

        admin = User(username="admin", role_id=admin_role.id, is_active=True)
        admin.set_password("admin-pass-123")
        encoder = User(username="encoder", role_id=encoder_role.id, is_active=True)
        encoder.set_password("encoder-pass-123")
        db.session.add_all([admin, encoder])
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def login(client, username, password):
    return client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


def test_create_user_requires_authentication(client):
    response = client.post(
        "/api/v1/users/",
        json={"username": "viewer1", "password": "viewer-pass-123", "role": "Viewer"},
    )

    assert response.status_code == 401


def test_non_admin_cannot_create_user(client):
    login(client, "encoder", "encoder-pass-123")

    response = client.post(
        "/api/v1/users/",
        json={"username": "viewer1", "password": "viewer-pass-123", "role": "Viewer"},
    )

    assert response.status_code == 403


def test_admin_can_create_user_with_hashed_password(client):
    login(client, "admin", "admin-pass-123")

    response = client.post(
        "/api/v1/users/",
        json={"username": "viewer1", "password": "viewer-pass-123", "role": "Viewer"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["data"]["username"] == "viewer1"
    assert body["data"]["role"] == "Viewer"
    assert "password" not in body["data"]

    created_user = User.query.filter_by(username="viewer1").one()
    assert created_user.password_hash != "viewer-pass-123"
    assert created_user.verify_password("viewer-pass-123")


def test_admin_cannot_create_duplicate_username(client):
    login(client, "admin", "admin-pass-123")

    response = client.post(
        "/api/v1/users/",
        json={"username": "encoder", "password": "viewer-pass-123", "role": "Viewer"},
    )

    assert response.status_code == 409