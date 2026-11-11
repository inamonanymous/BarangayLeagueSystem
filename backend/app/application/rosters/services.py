from datetime import date, datetime

from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.rosters.policies import RosterPolicy
from app.application.teams.policies import TeamPolicy
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.extensions import db
from app.infrastructure.database.roster_repository import RosterRepository


class RosterConflictError(ValueError):
    pass


class RosterService(BaseService):
    def __init__(
        self,
        repository: RosterRepository | None = None,
        policy: RosterPolicy | None = None,
        team_policy: TeamPolicy | None = None,
    ) -> None:
        self.repository = repository or RosterRepository()
        self.policy = policy or RosterPolicy()
        self.team_policy = team_policy or TeamPolicy()

    def list_for_team(self, team_id: int) -> list[dict]:
        team = self.repository.get_team(team_id)
        if team is None:
            raise LookupError("Team not found.")
        entries = []
        for roster in self.repository.list_for_team(team_id):
            player = self.repository.get_player(roster.player_id)
            if player is not None:
                entries.append({**roster.to_dict(), "player": player.to_dict()})
        return entries

    def add_player(
        self,
        team_id: int,
        *,
        player_id: int,
        jersey_number: str,
        actor_id: int,
        voter_verified: bool = False,
        voter_number: str | None = None,
        eligibility_notes: str | None = None,
    ) -> Roster:
        team = self.repository.get_team(team_id)
        if team is None:
            raise LookupError("Team not found.")
        if team.is_archived:
            raise ValueError("Players cannot be added to an archived team.")

        season, division, sport_id = self.repository.get_season_details(team)
        if season is None or division is None or sport_id is None:
            raise LookupError("Team season, sport, or division was not found.")
        self.team_policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=date.today(),
        )

        player = self.repository.get_player(player_id)
        if player is None or player.is_archived:
            raise LookupError("Active player not found.")
        jersey = self.policy.normalize_jersey_number(jersey_number)
        if self.repository.player_already_on_team(team_id, player_id):
            raise RosterConflictError("This player is already on the team roster.")
        if self.repository.player_on_same_sport_in_season(player_id, season.id, sport_id):
            raise RosterConflictError("This player is already assigned to a team in this sport and season.")
        if self.repository.jersey_exists(team_id, jersey):
            raise RosterConflictError("This jersey number is already used by the team.")
        self.policy.validate_roster_capacity(
            self.repository.roster_count(team_id),
            division.maximum_roster_size,
        )

        if self._is_adult(player.birthdate):
            normalized_voter_number = (voter_number or "").strip()
            if not voter_verified or not normalized_voter_number:
                raise ValueError("Players aged 18 or older must be voter-verified before roster registration.")
            eligibility = self.repository.find_eligibility(season.id, player_id)
            if eligibility is None:
                eligibility = SeasonPlayerEligibility(
                    season_id=season.id,
                    player_id=player_id,
                    is_voter_verified=True,
                    voter_number=normalized_voter_number,
                    verified_by=actor_id,
                    verified_at=datetime.utcnow(),
                    notes=(eligibility_notes or "").strip() or None,
                )
                self.repository.add(eligibility)
            else:
                eligibility.is_voter_verified = True
                eligibility.voter_number = normalized_voter_number
                eligibility.verified_by = actor_id
                eligibility.verified_at = datetime.utcnow()
                eligibility.notes = (eligibility_notes or "").strip() or eligibility.notes

        roster = Roster(
            season_team_id=team_id,
            player_id=player_id,
            jersey_number=jersey,
        )
        self.repository.add(roster)
        self._commit("Roster player or jersey number conflicts with an existing entry.")
        return roster

    def update_jersey_number(self, team_id: int, roster_id: int, jersey_number: str) -> Roster:
        team = self.repository.get_team(team_id)
        if team is None:
            raise LookupError("Team not found.")
        season, _, _ = self.repository.get_season_details(team)
        if season is None:
            raise LookupError("Season not found for team.")
        self.team_policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=date.today(),
        )
        roster = self.repository.get_roster(roster_id)
        if roster is None or roster.season_team_id != team_id:
            raise LookupError("Roster entry not found for this team.")
        jersey = self.policy.normalize_jersey_number(jersey_number)
        if self.repository.jersey_exists(team_id, jersey, exclude_id=roster_id):
            raise RosterConflictError("This jersey number is already used by the team.")
        roster.jersey_number = jersey
        self._commit("This jersey number is already used by the team.")
        return roster

    def remove_player(self, team_id: int, roster_id: int) -> None:
        team = self.repository.get_team(team_id)
        if team is None:
            raise LookupError("Team not found.")
        season, _, _ = self.repository.get_season_details(team)
        if season is None:
            raise LookupError("Season not found for team.")
        self.team_policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=date.today(),
        )
        roster = self.repository.get_roster(roster_id)
        if roster is None or roster.season_team_id != team_id:
            raise LookupError("Roster entry not found for this team.")
        self.repository.delete(roster)
        self._commit("Roster entry could not be removed.")

    @staticmethod
    def _is_adult(birthdate: date) -> bool:
        today = date.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        return age >= 18

    @staticmethod
    def _commit(conflict_message: str) -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise RosterConflictError(conflict_message) from exc
