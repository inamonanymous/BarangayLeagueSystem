import pytest

from app import create_app
from app.domain.models.roles import Role
from app.domain.models.users import User
from app.extensions import db


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        role = Role(name="Administrator", description="System administrator")
        db.session.add(role)
        db.session.flush()
        user = User(username="admin", is_active=True)
        user.role_id = role.id
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_login_and_current_user_flow(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["message"] == "Login successful."

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    me_body = me_response.get_json()
    assert me_body["data"]["username"] == "admin"


def test_logout_clears_session(client):
    client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )

    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 401
