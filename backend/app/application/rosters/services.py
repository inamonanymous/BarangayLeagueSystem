from datetime import date

from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.rosters.policies import RosterConflictError as RosterConflictError, RosterPolicy
from app.application.rosters.types import PlayerData, RosterData, RosterEntryData, VoterStatus
from app.application.teams.policies import TeamPolicy
from app.infrastructure.database.roster_repository import RosterRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class RosterService(BaseService):
    def __init__(
        self,
        repository: RosterRepository | None = None,
        policy: RosterPolicy | None = None,
        team_policy: TeamPolicy | None = None,
        unit_of_work: SqlAlchemyUnitOfWork | None = None,
    ) -> None:
        self.repository = repository or RosterRepository()
        self.policy = policy or RosterPolicy()
        self.team_policy = team_policy or TeamPolicy()
        self.unit_of_work = unit_of_work or SqlAlchemyUnitOfWork()

    def list_for_team(self, team_id: int) -> list[RosterEntryData]:
        team = self.repository.get_team(team_id)
        self.policy.validate_team_exists(team)
        return self.repository.list_for_team(team_id)

    def list_available_players(self, team_id: int) -> list[PlayerData]:
        team = self.policy.validate_team_availability(self.repository.get_team(team_id))
        season, _, sport_id = self.policy.validate_season_details(
            *self.repository.get_season_details(team)
        )
        return self.repository.list_available_players(season.id, sport_id)

    def add_player(
        self,
        team_id: int,
        *,
        player_id: int,
        jersey_number: str,
        actor_id: int,
        voter_verified: bool = False,
        eligibility_notes: str | None = None,
    ) -> RosterData:
        try:
            with self.unit_of_work:
                self.repository.lock_team_roster(team_id)
                team = self.policy.validate_team_availability(
                    self.repository.get_team(team_id, for_update=True)
                )
                season, division, sport_id = self.policy.validate_season_details(
                    *self.repository.get_season_details(team)
                )
                self.team_policy.validate_registration(
                    season_status=season.season_status,
                    registration_start_date=season.registration_start_date,
                    registration_end_date=season.registration_end_date,
                    registered_on=date.today(),
                )
                self.repository.lock_player(player_id)
                player = self.policy.validate_player_availability(self.repository.get_player(player_id))
                jersey = self.policy.normalize_jersey_number(jersey_number)
                self.policy.validate_player_not_on_team(
                    self.repository.player_already_on_team(team_id, player_id)
                )
                self.policy.validate_player_not_on_same_sport(
                    self.repository.player_on_same_sport_in_season(player_id, season.id, sport_id)
                )
                self.policy.validate_jersey_available(self.repository.jersey_exists(team_id, jersey))
                self.policy.validate_roster_capacity(
                    self.repository.roster_count(team_id), division.maximum_roster_size,
                )
                if season.voter_required and self.policy.is_adult(player.birthdate, date.today()):
                    number, verified = self.repository.voter_status(player_id, season.id, season.year, for_update=True)
                    self.policy.validate_voter_details(
                        player.birthdate, date.today(), voter_verified or verified, number
                    )
                    if number is None:
                        raise ValueError("A voter ID is required for this season year.")
                    if not verified:
                        self.repository.save_eligibility(season.id, player_id, number, actor_id, eligibility_notes)
                roster = self.repository.add_roster(team_id, player_id, jersey)
        except IntegrityError as exc:
            raise RosterConflictError(
                "Roster player or jersey number conflicts with an existing entry."
            ) from exc
        return roster

    def voter_status(self, team_id: int, player_id: int) -> VoterStatus:
        """Return voter eligibility state without exposing voter IDs."""
        team = self.policy.validate_team_availability(self.repository.get_team(team_id))
        season, _, _ = self.policy.validate_season_details(*self.repository.get_season_details(team))
        player = self.policy.validate_player_availability(self.repository.get_player(player_id))
        number, verified = self.repository.voter_status(player_id, season.id, season.year, for_update=True)
        return {
            "required": season.voter_required and self.policy.is_adult(player.birthdate, date.today()),
            "has_voter_id": number is not None,
            "verified": verified,
            "year": season.year,
        }

    def verify_rostered_player(self, team_id: int, player_id: int, actor_id: int) -> None:
        """Verify an existing roster player's current season-year voter ID."""
        with self.unit_of_work:
            self.repository.lock_team_roster(team_id)
            team = self.policy.validate_team_availability(self.repository.get_team(team_id, for_update=True))
            season, _, _ = self.policy.validate_season_details(*self.repository.get_season_details(team))
            if not season.voter_required or season.season_status not in ("REGISTRATION", "ONGOING"):
                raise ValueError("Voter verification is not available for this season.")
            if not self.repository.player_already_on_team(team_id, player_id):
                raise LookupError("Player is not on this team.")
            self.repository.lock_player(player_id)
            player = self.policy.validate_player_availability(self.repository.get_player(player_id))
            if not self.policy.is_adult(player.birthdate, date.today()):
                raise ValueError("Voter verification is only required for adults.")
            number, verified = self.repository.voter_status(player_id, season.id, season.year)
            self.policy.validate_voter_details(player.birthdate, date.today(), True, number)
            if number is None:
                raise ValueError("A voter ID is required for this season year.")
            if not verified:
                self.repository.save_eligibility(season.id, player_id, number, actor_id, None)

    def update_jersey_number(self, team_id: int, roster_id: int, jersey_number: str) -> RosterData:
        team = self.policy.validate_team_for_changes(self.repository.get_team(team_id))
        season, _, _ = self.repository.get_season_details(team)
        self.policy.validate_season_exists(team)
        self.team_policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=date.today(),
        )
        self.policy.validate_roster_ownership(self.repository.get_roster(roster_id), team_id)
        jersey = self.policy.normalize_jersey_number(jersey_number)
        self.policy.validate_jersey_available(
            self.repository.jersey_exists(team_id, jersey, exclude_id=roster_id)
        )
        try:
            with self.unit_of_work:
                roster = self.repository.update_jersey(roster_id, jersey)
        except IntegrityError as exc:
            raise RosterConflictError("This jersey number is already used by the team.") from exc
        return roster

    def remove_player(self, team_id: int, roster_id: int) -> None:
        team = self.policy.validate_team_for_changes(self.repository.get_team(team_id))
        season, _, _ = self.repository.get_season_details(team)
        self.policy.validate_season_exists(team)
        self.team_policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=date.today(),
        )
        self.policy.validate_roster_ownership(self.repository.get_roster(roster_id), team_id)
        try:
            with self.unit_of_work:
                self.repository.delete_roster(roster_id)
        except IntegrityError as exc:
            raise RosterConflictError("Roster entry could not be removed.") from exc
