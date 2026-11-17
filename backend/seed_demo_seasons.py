from datetime import date

from app import create_app
from app.application.catalogs.services import CatalogService
from app.application.season.services import SeasonService
from app.application.teams.services import SeasonTeamService
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam


DEMO_TEAMS = [
    {
        "name": "Puting Kahoy Warriors",
        "barangay": "Puting Kahoy",
        "coach_name": "Sample Coach A",
        "manager_name": "Sample Manager A",
        "team_color": "Green",
    },
    {
        "name": "San Isidro Eagles",
        "barangay": "San Isidro",
        "coach_name": "Sample Coach B",
        "manager_name": "Sample Manager B",
        "team_color": "Blue",
    },
    {
        "name": "Poblacion Tigers",
        "barangay": "Poblacion",
        "coach_name": "Sample Coach C",
        "manager_name": "Sample Manager C",
        "team_color": "Orange",
    },
    {
        "name": "Mabini Falcons",
        "barangay": "Mabini",
        "coach_name": "Sample Coach D",
        "manager_name": "Sample Manager D",
        "team_color": "Red",
    },
]


DEMO_SEASONS = [
    {
        "name": "DEMO - Planning Season 2028",
        "year": 2028,
        "registration_start_date": date(2028, 1, 1),
        "registration_end_date": date(2028, 1, 31),
        "start_date": date(2028, 2, 1),
        "end_date": date(2028, 4, 30),
        "transitions": (),
    },
    {
        "name": "DEMO - Completed Season 2025",
        "year": 2025,
        "registration_start_date": date(2025, 1, 1),
        "registration_end_date": date(2025, 1, 31),
        "start_date": date(2025, 2, 1),
        "end_date": date(2025, 4, 30),
        "transitions": ("REGISTRATION", "ONGOING", "COMPLETED"),
    },
    {
        "name": "DEMO - Archived Season 2024",
        "year": 2024,
        "registration_start_date": date(2024, 1, 1),
        "registration_end_date": date(2024, 1, 31),
        "start_date": date(2024, 2, 1),
        "end_date": date(2024, 4, 30),
        "transitions": ("ARCHIVED",),
    },
    {
        "name": "DEMO - Registration Season 2027",
        "year": 2027,
        "registration_start_date": date(2027, 1, 1),
        "registration_end_date": date(2027, 1, 31),
        "start_date": date(2027, 2, 1),
        "end_date": date(2027, 4, 30),
        "transitions": ("REGISTRATION",),
    },
]


def ensure_division_assignment(
    catalog_service: CatalogService,
    season: Season,
    sport_name: str,
    division_name: str,
) -> SeasonSportDivision:
    season_sport = SeasonSport.query.filter_by(
        season_id=season.id,
        name=sport_name,
    ).first()
    if season_sport is None:
        season_sport = catalog_service.create_sport(season.id, name=sport_name)

    division_assignment = SeasonSportDivision.query.filter_by(
        season_sport_id=season_sport.id,
        name=division_name,
    ).first()
    if division_assignment is None:
        division_assignment = catalog_service.create_division(
            season_sport.id, name=division_name, minimum_roster_size=5, maximum_roster_size=15,
        )
    return division_assignment


def main() -> None:
    app = create_app("development")
    with app.app_context():
        service = SeasonService()
        for demo in DEMO_SEASONS:
            data = {key: value for key, value in demo.items() if key != "transitions"}
            existing = Season.query.filter_by(name=demo["name"]).first()
            if existing is not None:
                print(f"SKIPPED existing: {existing.id} {existing.name} [{existing.season_status}]")
                continue

            season = service.create_season(**data)
            for next_status in demo["transitions"]:
                season = service.transition_season(season.id, next_status)
            print(f"CREATED: {season.id} {season.name} [{season.season_status}]")

        catalog_service = CatalogService()
        planning_season = Season.query.filter_by(
            name="DEMO - Planning Season 2028"
        ).one()

        ensure_division_assignment(catalog_service, planning_season, "Basketball", "Senior")
        print(
            f"CONFIGURED: {planning_season.name} -> "
            "Basketball -> Senior"
        )

        registration_season = Season.query.filter_by(
            name="DEMO - Registration Season 2027"
        ).one()
        registration_assignment = ensure_division_assignment(
            catalog_service,
            registration_season,
            "Basketball",
            "Senior",
        )
        team_service = SeasonTeamService()
        for team_data in DEMO_TEAMS:
            existing_team = SeasonTeam.query.filter_by(
                season_sport_division_id=registration_assignment.id,
                name=team_data["name"],
            ).first()
            if existing_team is not None:
                print(f"SKIPPED existing team: {existing_team.name}")
                continue
            team = team_service.register_team(
                registration_assignment.id,
                **team_data,
            )
            print(f"CREATED team: {team.name} [{team.barangay}]")


if __name__ == "__main__":
    main()
