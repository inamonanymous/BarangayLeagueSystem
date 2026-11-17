import pytest

from app import create_app
from app.domain.models.roles import Role
from app.domain.models.games import ScheduleLock
from app.domain.models.statistics import StatisticType, SportStatisticConfiguration
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.users import User
from app.extensions import db


@pytest.fixture()
def client():
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
        for name, role_name in (("admin", "Administrator"), ("encoder", "Encoder")):
            role = Role(name=role_name)
            db.session.add(role)
            db.session.flush()
            user = User(username=name, role_id=role.id, is_active=True)
            user.set_password("password-123")
            db.session.add(user)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def login(client, username="admin"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": "password-123"})


def create_season(client, name):
    response = client.post("/api/v1/seasons/", json={"name": name, "year": 2026})
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def division_payload(name="Senior", minimum=5, maximum=15):
    return {"name": name, "gender_policy": "ANY", "minimum_roster_size": minimum, "maximum_roster_size": maximum}


def test_season_configuration_is_independent(client):
    login(client)
    seasons = [create_season(client, name) for name in ("Season A", "Season B")]
    sports = []
    divisions = []
    for season in seasons:
        sport = client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Basketball"})
        assert sport.status_code == 201
        sports.append(sport.get_json()["data"]["id"])
        division = client.post(f"/api/v1/seasons/sports/{sports[-1]}/divisions", json=division_payload())
        assert division.status_code == 201
        divisions.append(division.get_json()["data"]["id"])
    assert sports[0] != sports[1] and divisions[0] != divisions[1]
    assert client.put(f"/api/v1/seasons/{seasons[0]}/sports/{sports[0]}", json={"name": "Basketball A"}).status_code == 200
    assert client.put(f"/api/v1/seasons/sports/{sports[0]}/divisions/{divisions[0]}", json=division_payload(maximum=12)).status_code == 200
    first, second = [client.get(f"/api/v1/seasons/{season}/configuration").get_json()["data"] for season in seasons]
    assert first["sports"][0]["name"] == "Basketball A"
    assert first["sports"][0]["divisions"][0]["maximum_roster_size"] == 12
    assert second["sports"][0]["name"] == "Basketball"
    assert second["sports"][0]["divisions"][0]["maximum_roster_size"] == 15
    assert client.delete(f"/api/v1/seasons/{seasons[0]}/sports/{sports[0]}").status_code == 200
    assert client.get(f"/api/v1/seasons/{seasons[1]}/configuration").get_json()["data"]["sports"][0]["id"] == sports[1]


def test_season_configuration_scopes_names_and_ownership(client):
    login(client)
    season_a, season_b = [create_season(client, name) for name in ("A", "B")]
    sport = client.post(f"/api/v1/seasons/{season_a}/sports", json={"name": " Basketball "}).get_json()["data"]
    assert client.post(f"/api/v1/seasons/{season_a}/sports", json={"name": "basketball"}).status_code == 409
    division = client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload()).get_json()["data"]
    assert client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload("senior")).status_code == 409
    assert client.put(f"/api/v1/seasons/{season_b}/sports/{sport['id']}", json={"name": "Wrong"}).status_code == 404
    other = client.post(f"/api/v1/seasons/{season_b}/sports", json={"name": "Basketball"}).get_json()["data"]
    assert client.put(f"/api/v1/seasons/sports/{other['id']}/divisions/{division['id']}", json=division_payload()).status_code == 404
    assert client.delete(f"/api/v1/seasons/sports/{other['id']}/divisions/{division['id']}").status_code == 404


def test_season_configuration_requires_admin_and_configurable_status(client):
    login(client)
    season = create_season(client, "Season")
    sport = client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Basketball"}).get_json()["data"]
    division = client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload()).get_json()["data"]
    db.session.get(Season, season).season_status = "ONGOING"
    db.session.commit()
    assert client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Volleyball"}).status_code == 400
    assert client.put(f"/api/v1/seasons/{season}/sports/{sport['id']}", json={"name": "Volleyball"}).status_code == 400
    assert client.delete(f"/api/v1/seasons/{season}/sports/{sport['id']}").status_code == 400
    assert client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload("Junior")).status_code == 400
    assert client.put(f"/api/v1/seasons/sports/{sport['id']}/divisions/{division['id']}", json=division_payload()).status_code == 400
    assert client.delete(f"/api/v1/seasons/sports/{sport['id']}/divisions/{division['id']}").status_code == 400
    client.post("/api/v1/auth/logout")
    assert client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Tennis"}).status_code == 401
    login(client, "encoder")
    assert client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Tennis"}).status_code == 403
    assert client.get(f"/api/v1/seasons/{season}/configuration").status_code == 200


def test_invalid_division_and_unassigned_removal(client):
    login(client)
    season = create_season(client, "Season")
    sport = client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Basketball"}).get_json()["data"]
    assert client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload(maximum=4)).status_code == 400
    division = client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload()).get_json()["data"]
    assert client.delete(f"/api/v1/seasons/sports/{sport['id']}/divisions/{division['id']}").status_code == 200
    assert client.delete(f"/api/v1/seasons/{season}/sports/{sport['id']}").status_code == 200
    assert SeasonSport.query.count() == 0 and SeasonSportDivision.query.count() == 0


def test_removing_unassigned_sport_removes_its_statistic_configuration(client):
    login(client)
    db.session.add(ScheduleLock(id=1))
    db.session.commit()
    season = create_season(client, "Season")
    sport_id = client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Basketball"}).get_json()["data"]["id"]
    response = client.put(f"/api/v1/season-sports/{sport_id}/statistics-configuration", json={
        "allow_team_points": False,
        "types": [{"name": "Points", "abbreviation": "PTS", "required": True, "is_scoring": True}],
    })
    assert response.status_code == 200
    assert client.delete(f"/api/v1/seasons/{season}/sports/{sport_id}").status_code == 200
    assert StatisticType.query.count() == 0 and SportStatisticConfiguration.query.count() == 0


def test_sport_and_division_with_teams_cannot_be_removed(client):
    login(client)
    season = create_season(client, "Season")
    sport = client.post(f"/api/v1/seasons/{season}/sports", json={"name": "Basketball"}).get_json()["data"]
    division = client.post(f"/api/v1/seasons/sports/{sport['id']}/divisions", json=division_payload()).get_json()["data"]
    db.session.add(SeasonTeam(season_sport_division_id=division["id"], name="Team", barangay="Demo"))
    db.session.commit()
    assert client.delete(f"/api/v1/seasons/sports/{sport['id']}/divisions/{division['id']}").status_code == 409
    assert client.delete(f"/api/v1/seasons/{season}/sports/{sport['id']}").status_code == 409
