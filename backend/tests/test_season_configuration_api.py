import pytest

from app import create_app
from app.domain.models.divisions import Division
from app.domain.models.roles import Role
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.sports import Sport
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


def login(client, username="admin", password="admin-pass-123"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def create_season(client):
    response = client.post(
        "/api/v1/seasons/",
        json={"name": "Summer League", "year": 2026},
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def test_admin_can_configure_season_sports_and_divisions(client):
    login(client)
    season_id = create_season(client)
    sport_response = client.post("/api/v1/catalogs/sports", json={"name": "Basketball"})
    division_response = client.post(
        "/api/v1/catalogs/divisions",
        json={
            "name": "Senior",
            "gender_policy": "ANY",
            "minimum_roster_size": 5,
            "maximum_roster_size": 15,
        },
    )
    assert sport_response.status_code == 201
    assert division_response.status_code == 201

    assignment_response = client.post(
        f"/api/v1/seasons/{season_id}/sports",
        json={"sport_id": sport_response.get_json()["data"]["id"]},
    )
    season_sport_id = assignment_response.get_json()["data"]["id"]
    division_assignment = client.post(
        f"/api/v1/seasons/sports/{season_sport_id}/divisions",
        json={"division_id": division_response.get_json()["data"]["id"]},
    )

    assert assignment_response.status_code == 201
    assert division_assignment.status_code == 201
    configuration = client.get(f"/api/v1/seasons/{season_id}/configuration")
    body = configuration.get_json()["data"]
    assert body["sports"][0]["sport"]["name"] == "Basketball"
    assert body["sports"][0]["divisions"][0]["name"] == "Senior"
    assert SeasonSport.query.count() == 1
    assert SeasonSportDivision.query.count() == 1


def test_non_admin_cannot_create_catalog_or_configure_season(client):
    login(client, "encoder", "encoder-pass-123")
    assert client.post("/api/v1/catalogs/sports", json={"name": "Basketball"}).status_code == 403


def test_duplicate_sport_assignment_returns_conflict(client):
    login(client)
    season_id = create_season(client)
    sport = Sport(name="Basketball")
    db.session.add(sport)
    db.session.commit()
    payload = {"sport_id": sport.id}
    client.post(f"/api/v1/seasons/{season_id}/sports", json=payload)

    response = client.post(f"/api/v1/seasons/{season_id}/sports", json=payload)

    assert response.status_code == 409
    assert SeasonSport.query.count() == 1


def test_cannot_configure_season_after_it_is_ongoing(client):
    login(client)
    season_id = create_season(client)
    season = db.session.get(Season, season_id)
    season.season_status = "ONGOING"
    db.session.commit()
    sport = Sport(name="Volleyball")
    db.session.add(sport)
    db.session.commit()

    response = client.post(
        f"/api/v1/seasons/{season_id}/sports",
        json={"sport_id": sport.id},
    )

    assert response.status_code == 400


def test_admin_can_update_sport_and_division_catalog(client):
    login(client)
    sport = client.post("/api/v1/catalogs/sports", json={"name": "Basketball"}).get_json()["data"]
    division = client.post(
        "/api/v1/catalogs/divisions",
        json={"name": "Senior", "minimum_roster_size": 5, "maximum_roster_size": 15},
    ).get_json()["data"]

    updated_sport = client.put(
        f"/api/v1/catalogs/sports/{sport['id']}",
        json={"name": "Indoor Basketball", "description": "Court sport"},
    )
    updated_division = client.put(
        f"/api/v1/catalogs/divisions/{division['id']}",
        json={
            "name": "Open Division",
            "gender_policy": "MIXED",
            "minimum_roster_size": 6,
            "maximum_roster_size": 12,
        },
    )

    assert updated_sport.status_code == 200
    assert updated_sport.get_json()["data"]["name"] == "Indoor Basketball"
    assert updated_division.status_code == 200
    assert updated_division.get_json()["data"]["gender_policy"] == "MIXED"


def test_catalog_delete_is_rejected_when_item_is_assigned(client):
    login(client)
    season_id = create_season(client)
    sport = client.post("/api/v1/catalogs/sports", json={"name": "Basketball"}).get_json()["data"]
    client.post(f"/api/v1/seasons/{season_id}/sports", json={"sport_id": sport["id"]})

    response = client.delete(f"/api/v1/catalogs/sports/{sport['id']}")

    assert response.status_code == 409
    assert Sport.query.filter_by(id=sport["id"]).one().name == "Basketball"


def test_admin_can_remove_season_assignments_without_deleting_catalogs(client):
    login(client)
    season_id = create_season(client)
    sport = client.post("/api/v1/catalogs/sports", json={"name": "Basketball"}).get_json()["data"]
    division = client.post(
        "/api/v1/catalogs/divisions",
        json={"name": "Senior", "minimum_roster_size": 5, "maximum_roster_size": 15},
    ).get_json()["data"]
    season_sport = client.post(
        f"/api/v1/seasons/{season_id}/sports",
        json={"sport_id": sport["id"]},
    ).get_json()["data"]
    division_assignment = client.post(
        f"/api/v1/seasons/sports/{season_sport['id']}/divisions",
        json={"division_id": division["id"]},
    ).get_json()["data"]

    remove_division = client.delete(
        f"/api/v1/seasons/sports/{season_sport['id']}/divisions/{division_assignment['id']}"
    )
    remove_sport = client.delete(f"/api/v1/seasons/{season_id}/sports/{season_sport['id']}")

    assert remove_division.status_code == 200
    assert remove_sport.status_code == 200
    assert Sport.query.filter_by(id=sport["id"]).one() is not None
    assert Division.query.filter_by(id=division["id"]).one() is not None
    assert SeasonSport.query.count() == 0
    assert SeasonSportDivision.query.count() == 0