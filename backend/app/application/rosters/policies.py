from datetime import date

from app.application.common.utils.base_classes import BasePolicy
from app.application.rosters.types import (
    DivisionSnapshot, PlayerSnapshot, RosterSnapshot, SeasonSnapshot, TeamSnapshot,
)


class RosterConflictError(ValueError):
    pass


class RosterPolicy(BasePolicy):
    def validate_season_exists(self, season: SeasonSnapshot | None) -> None:
        if season is None:
            raise LookupError("Season not found.")

    def validate_team_exists(self, team: TeamSnapshot | None) -> None:
        if team is None:
            raise LookupError("Team not found.")

    def normalize_jersey_number(self, jersey_number: str) -> str:
        normalized = jersey_number.strip() if isinstance(jersey_number, str) else ""
        if not normalized:
            raise ValueError("Jersey number is required.")
        if len(normalized) > 10:
            raise ValueError("Jersey number must be 10 characters or fewer.")
        return normalized

    def validate_roster_capacity(self, current_size: int, maximum_size: int) -> None:
        if current_size >= maximum_size:
            raise ValueError("The team roster is already at its maximum size.")

    def validate_team_availability(self, team: TeamSnapshot | None) -> TeamSnapshot:
        if team is None:
            raise LookupError("Team not found.")
        if team.is_archived:
            raise ValueError("Players cannot be added to an archived team.")
        return team

    def validate_season_details(
        self, season: SeasonSnapshot | None, division: DivisionSnapshot | None, sport_id: int | None,
    ) -> tuple[SeasonSnapshot, DivisionSnapshot, int]:
        if season is None or division is None or sport_id is None:
            raise LookupError("Team season, sport, or division was not found.")
        return season, division, sport_id

    def validate_player_availability(self, player: PlayerSnapshot | None) -> PlayerSnapshot:
        if player is None or player.is_archived:
            raise LookupError("Active player not found.")
        return player

    def validate_player_not_on_team(self, already_on_team: bool) -> None:
        if already_on_team:
            raise RosterConflictError("This player is already on the team roster.")

    def validate_player_not_on_same_sport(self, already_assigned: bool) -> None:
        if already_assigned:
            raise RosterConflictError("This player is already assigned to a team in this sport and season.")

    def validate_jersey_available(self, jersey_exists: bool) -> None:
        if jersey_exists:
            raise RosterConflictError("This jersey number is already used by the team.")

    def validate_team_for_changes(self, team: TeamSnapshot | None) -> TeamSnapshot:
        if team is None:
            raise LookupError("Team not found.")
        if team.is_archived:
            raise ValueError("Roster entries cannot be changed for an archived team.")
        return team

    def validate_roster_ownership(self, roster: RosterSnapshot | None, team_id: int) -> None:
        if roster is None or roster.season_team_id != team_id:
            raise LookupError("Roster entry not found for this team.")

    @staticmethod
    def is_adult(birthdate: date, today: date) -> bool:
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        return age >= 18

    def validate_voter_details(
        self, birthdate: date, today: date, voter_verified: bool, voter_number: str | None,
    ) -> str | None:
        if not self.is_adult(birthdate, today):
            return None
        normalized_voter_number = (voter_number or "").strip()
        if not voter_verified or not normalized_voter_number:
            raise ValueError("Players aged 18 or older must be voter-verified before roster registration.")
        return normalized_voter_number