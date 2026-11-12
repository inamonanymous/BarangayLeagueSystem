import argparse
from datetime import date

from app import create_app
from app.application.catalogs.services import CatalogService
from app.application.players.services import PlayerService
from app.application.rosters.services import RosterService
from app.application.teams.policies import TeamPolicy
from app.application.teams.services import SeasonTeamService
from app.domain.models.divisions import Division
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.sports import Sport
from app.domain.models.users import User
from app.extensions import db
from app.infrastructure.database.season_repository import SeasonRepository
from seed_demo_seasons import DEMO_TEAMS, ensure_division_assignment


SEASON_NAME = "DEMO - Registration Season 2027"
JUNIOR_TEAMS = [
    {"name": "DEMO - Junior Warriors", "barangay": "Puting Kahoy", "team_color": "Green"},
    {"name": "DEMO - Junior Eagles", "barangay": "San Isidro", "team_color": "Blue"},
    {"name": "DEMO - Junior Tigers", "barangay": "Poblacion", "team_color": "Orange"},
]
PLAYER_NAMES = ("Alex", "Blake", "Casey", "Drew", "Eli", "Francis", "Gabriel", "Hayden", "Ivan", "Jordan")
DEMO_DIVISIONS = (
    ("Senior", DEMO_TEAMS, date(2000, 1, 1)),
    ("Junior", JUNIOR_TEAMS, date(2012, 1, 1)),
)


def demo_player_identity(division_name: str, team_index: int, number: int) -> dict:
    return {
        "first_name": PLAYER_NAMES[(number - 1) % len(PLAYER_NAMES)],
        "middle_name": "",
        "last_name": f"Demo {division_name} Team {team_index} Player {number}",
    }


def is_demo_eligibility(
    eligibility: SeasonPlayerEligibility | None,
    division_name: str,
    team_index: int,
    number: int,
) -> bool:
    return (
        eligibility is not None
        and eligibility.is_voter_verified
        and eligibility.verified_by is not None
        and eligibility.verified_at is not None
        and eligibility.voter_number == f"DEMO-{division_name.upper()}-{team_index}-{number}"
        and eligibility.notes == "Fictional demo player; voter details are not real."
    )


def verify_demo_teams() -> None:
    season = Season.query.filter_by(name=SEASON_NAME).first()
    if season is None:
        raise ValueError(f"Demo verification failed: {SEASON_NAME} does not exist.")

    errors = []
    for division_name, teams, birthdate in DEMO_DIVISIONS:
        assignment = (
            db.session.query(SeasonSportDivision, Division)
            .join(Division, Division.id == SeasonSportDivision.division_id)
            .join(SeasonSport, SeasonSport.id == SeasonSportDivision.season_sport_id)
            .join(Sport, Sport.id == SeasonSport.sport_id)
            .filter(
                SeasonSport.season_id == season.id,
                Sport.name == "Basketball",
                Division.name == division_name,
            )
            .first()
        )
        if assignment is None:
            errors.append(f"{division_name}: Basketball division assignment is missing.")
            continue
        division_assignment, division = assignment
        for team_index, team_data in enumerate(teams, start=1):
            team = SeasonTeam.query.filter_by(
                season_sport_division_id=division_assignment.id, name=team_data["name"]
            ).first()
            if team is None or team.is_archived or team.barangay != team_data["barangay"]:
                errors.append(f"{division_name} / {team_data['name']}: team missing, archived, or changed.")
                continue
            active_count = (
                db.session.query(Roster)
                .join(Player, Player.id == Roster.player_id)
                .filter(Roster.season_team_id == team.id, Player.is_archived.is_(False))
                .count()
            )
            if active_count < division.minimum_roster_size:
                errors.append(
                    f"{division_name} / {team.name}: {active_count}/{division.minimum_roster_size} active players."
                )
            for number in range(1, max(5, division.minimum_roster_size) + 1):
                identity = demo_player_identity(division_name, team_index, number)
                player = Player.query.filter_by(**identity, birthdate=birthdate).first()
                label = f"{division_name} / {team.name} / {identity['last_name']}"
                if (
                    player is None
                    or player.is_archived
                    or player.address != f"DEMO - {team_data['barangay']}"
                    or player.gender != "MALE"
                    or Roster.query.filter_by(season_team_id=team.id, player_id=player.id).first() is None
                ):
                    errors.append(f"{label}: demo player missing, changed, archived, or not on this roster.")
                    continue
                if RosterService._is_adult(player.birthdate):
                    eligibility = SeasonPlayerEligibility.query.filter_by(
                        season_id=season.id, player_id=player.id
                    ).first()
                    if not is_demo_eligibility(eligibility, division_name, team_index, number):
                        errors.append(f"{label}: fictional voter verification is missing or changed.")
            print(f"CHECKED: {division_name} / {team.name}: {active_count}/{division.minimum_roster_size} active players")

    if errors:
        raise ValueError("Demo verification failed:\n- " + "\n- ".join(errors))

    print("VERIFIED: all sample teams and players are present.")
    incomplete = SeasonRepository().list_teams_below_minimum_roster_size(season.id)
    if incomplete:
        for team in incomplete:
            print(
                f"SEASON NOT READY: {team['division_name']} / {team['team_name']}: "
                f"{team['roster_count']}/{team['minimum_roster_size']} active players"
            )
    else:
        print("SEASON ROSTERS READY: all active teams meet their division minimum.")


def seed_demo_teams(actor_id: int) -> None:
    actor = db.session.get(User, actor_id)
    if actor is None or not actor.is_active or actor.role != "Administrator":
        raise ValueError("An active Administrator user ID is required for demo voter verification.")

    season = Season.query.filter_by(name=SEASON_NAME).first()
    if season is None:
        raise ValueError(f"{SEASON_NAME} does not exist. Create it before seeding teams.")
    TeamPolicy().validate_registration(
        season_status=season.season_status,
        registration_start_date=season.registration_start_date,
        registration_end_date=season.registration_end_date,
        registered_on=date.today(),
    )

    catalog_service = CatalogService()
    sport = Sport.query.filter_by(name="Basketball").first()
    if sport is None:
        sport = catalog_service.create_sport("Basketball")

    for division_name, teams, birthdate in DEMO_DIVISIONS:
        division = Division.query.filter_by(name=division_name).first()
        if division is None:
            division = catalog_service.create_division(
                name=division_name, minimum_roster_size=5, maximum_roster_size=15
            )
        if division.gender_policy not in {"ANY", "MALE_ONLY"}:
            raise ValueError(f"{division_name} does not allow the male demo players.")

        assignment = ensure_division_assignment(catalog_service, season, sport, division)
        team_service = SeasonTeamService()
        player_service = PlayerService()
        roster_service = RosterService()
        for team_index, team_data in enumerate(teams, start=1):
            team = SeasonTeam.query.filter_by(
                season_sport_division_id=assignment.id, name=team_data["name"]
            ).first()
            if team is None:
                team = team_service.register_team(assignment.id, **team_data)
                print(f"CREATED {division_name} team: {team.name}")
            if team.is_archived:
                raise ValueError(f"Demo team {team.name} is archived; restore it before seeding.")
            if team.barangay != team_data["barangay"]:
                raise ValueError(f"Demo team {team.name} has a different barangay; check it before seeding.")

            for number in range(1, max(5, division.minimum_roster_size) + 1):
                identity = demo_player_identity(division_name, team_index, number)
                player = Player.query.filter_by(**identity, birthdate=birthdate).first()
                address = f"DEMO - {team_data['barangay']}"
                if player is None:
                    player = player_service.create_player(
                        first_name=identity["first_name"],
                        middle_name=None,
                        last_name=identity["last_name"],
                        birthdate=birthdate,
                        gender="MALE",
                        address=address,
                    )
                elif player.is_archived or player.address != address or player.gender != "MALE":
                    raise ValueError(f"Demo player {identity['first_name']} {identity['last_name']} was changed or archived.")

                if Roster.query.filter_by(season_team_id=team.id, player_id=player.id).first():
                    continue
                eligibility = SeasonPlayerEligibility.query.filter_by(
                    season_id=season.id, player_id=player.id
                ).first()
                if eligibility is not None and not is_demo_eligibility(
                    eligibility, division_name, team_index, number
                ):
                    raise ValueError(
                        f"Demo player {identity['first_name']} {identity['last_name']} "
                        "has changed voter details; check them before seeding."
                    )
                used_jerseys = {
                    entry.jersey_number.casefold()
                    for entry in Roster.query.filter_by(season_team_id=team.id).all()
                }
                jersey = 1
                while str(jersey) in used_jerseys:
                    jersey += 1
                roster_service.add_player(
                    team.id,
                    player_id=player.id,
                    jersey_number=str(jersey),
                    actor_id=actor_id,
                    voter_verified=True,
                    voter_number=f"DEMO-{division_name.upper()}-{team_index}-{number}",
                    eligibility_notes="Fictional demo player; voter details are not real.",
                )
    verify_demo_teams()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add fictional teams and players to the demo registration season."
    )
    parser.add_argument("--actor-id", type=int, help="Active Administrator user ID (required for seeding)")
    parser.add_argument("--check", action="store_true", help="Verify existing demo data without changing it")
    args = parser.parse_args()
    if not args.check and args.actor_id is None:
        parser.error("--actor-id is required unless using --check")
    app = create_app("development")
    with app.app_context():
        if args.check:
            verify_demo_teams()
        else:
            seed_demo_teams(args.actor_id)


if __name__ == "__main__":
    main()
