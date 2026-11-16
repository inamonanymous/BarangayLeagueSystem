from datetime import datetime

from app.application.common.utils.base_classes import BasePolicy
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.seasons import Season


class ScheduleConflictError(ValueError):
    pass


class GamePolicy(BasePolicy):
    def validate_schedule(
        self, venue: str, starts_at: datetime, ends_at: datetime,
    ) -> tuple[str, str]:
        venue = " ".join(venue.split())
        venue_key = venue.casefold()
        if not venue or len(venue) > 150 or len(venue_key) > 150:
            raise ValueError("Venue must be between 1 and 150 characters.")
        if starts_at.utcoffset() is not None or ends_at.utcoffset() is not None:
            raise ValueError("Use local date and time without a timezone offset.")
        if starts_at.microsecond or ends_at.microsecond:
            raise ValueError("Game times must use whole seconds.")
        if ends_at <= starts_at:
            raise ValueError("Game end time must be after its start time.")
        return venue, venue_key

    def validate_distinct_teams(self, home_team_id: int, away_team_id: int) -> None:
        if home_team_id == away_team_id:
            raise ValueError("Choose two different teams.")

    def validate_ongoing_season(self, season: Season) -> None:
        if season.season_status != "ONGOING":
            raise ValueError("Games can only be scheduled while the season is Ongoing.")

    def validate_team(self, team: SeasonTeam, assignment_id: int) -> None:
        if team.is_archived or team.season_sport_division_id != assignment_id:
            raise ValueError("Both teams must be active in the selected division.")

    def validate_no_overlap(self, has_overlap: bool) -> None:
        if has_overlap:
            raise ScheduleConflictError("A team or venue already has an overlapping game.")

    def validate_reschedule(
        self, original_start: datetime, new_start: datetime, now: datetime,
    ) -> None:
        if original_start <= now:
            raise ValueError("A game cannot be rescheduled after it has started.")
        if new_start <= now:
            raise ValueError("The new start time must be in the future.")
