from datetime import datetime
from fractions import Fraction

from app.application.common.utils.base_classes import BasePolicy
from app.application.games.types import (
    DivisionSnapshot, GameData, GameSnapshot, SeasonSnapshot, StandingData, StandingTeam, TeamSnapshot,
)


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

    def validate_division_exists(self, assignment: DivisionSnapshot | None) -> DivisionSnapshot:
        if assignment is None:
            raise LookupError("Season division assignment not found.")
        return assignment

    def validate_ongoing_season(self, season: SeasonSnapshot | None) -> None:
        if season is None:
            raise LookupError("Season not found for division assignment.")
        if season.season_status != "ONGOING":
            raise ValueError("Games can only be scheduled while the season is Ongoing.")

    def validate_team(self, team: TeamSnapshot, assignment_id: int) -> None:
        if team.is_archived or team.season_sport_division_id != assignment_id:
            raise ValueError("Both teams must be active in the selected division.")

    def check_overlapping_schedule(self, has_overlap: bool) -> None:
        if has_overlap:
            raise ScheduleConflictError("A team or venue already has an overlapping game.")

    def validate_reschedule(
        self, original_start: datetime, new_start: datetime, now: datetime,
    ) -> None:
        if original_start <= now:
            raise ValueError("A game cannot be rescheduled after it has started.")
        if new_start <= now:
            raise ValueError("The new start time must be in the future.")

    def validate_result_window(self, season: SeasonSnapshot | None, game: GameSnapshot, now: datetime) -> None:
        if season is None:
            raise LookupError("Season not found for division assignment.")
        if season.season_status != "ONGOING":
            raise ValueError("Game results can only be changed while the season is Ongoing.")
        if game.ends_at > now:
            raise ValueError("Game results can only be entered after the scheduled end.")

    def validate_result_scores(self, home_score: int, away_score: int) -> None:
        if (type(home_score) is not int or type(away_score) is not int
                or not 0 <= home_score <= 2147483647 or not 0 <= away_score <= 2147483647):
            raise ValueError("Scores must be non-negative whole numbers within the supported range.")
        if home_score == away_score:
            raise ValueError("Final scores must have a winner; include overtime in the score.")

    def validate_result_editable(self, game: GameSnapshot) -> None:
        if game.result_status not in ("SCHEDULED", "FOR_ENCODING"):
            raise ValueError("Reopen the finalized game before editing its scores.")

    def validate_finalization(self, game: GameSnapshot) -> None:
        if game.result_status != "FOR_ENCODING" or game.home_score is None or game.away_score is None:
            raise ValueError("Enter scores before finalizing the game.")
        self.validate_result_scores(game.home_score, game.away_score)

    def validate_reopening(self, game: GameSnapshot, reason: str) -> str:
        reason = reason.strip()
        if game.result_status != "FINALIZED":
            raise ValueError("Only finalized games can be reopened.")
        if game.home_score is None or game.away_score is None or game.finalized_at is None or game.finalized_by is None:
            raise ValueError("The finalized game is missing result or finalization details.")
        if not reason:
            raise ValueError("A reason is required to reopen a game.")
        return reason

    def calculate_standings(self, teams: list[StandingTeam], games: list[GameData]) -> list[StandingData]:
        records = {team.id: {"wins": 0, "losses": 0} for team in teams}
        results: list[tuple[int, int]] = []
        for game in games:
            home, away = game["home_team_id"], game["away_team_id"]
            home_score, away_score = game["home_score"], game["away_score"]
            if home not in records or away not in records or home_score is None or away_score is None:
                raise ValueError("A finalized game has missing teams or scores.")
            self.validate_result_scores(home_score, away_score)
            winner, loser = (home, away) if home_score > away_score else (away, home)
            records[winner]["wins"] += 1
            records[loser]["losses"] += 1
            results.append((winner, loser))

        output: list[StandingData] = []
        for wins in sorted({record["wins"] for record in records.values()}, reverse=True):
            tied = [team for team in teams if records[team.id]["wins"] == wins]
            ids = {team.id for team in tied}
            head = {team.id: [0, 0] for team in tied}
            for winner, loser in results:
                if winner in ids and loser in ids:
                    head[winner][0] += 1
                    head[winner][1] += 1
                    head[loser][1] += 1
            def ratio(team: StandingTeam) -> Fraction | None:
                won, played = head[team.id]
                return Fraction(won, played) if played else None
            tied.sort(key=lambda team: (
                ratio(team) is not None, ratio(team) or Fraction(0),
            ), reverse=True)
            previous: Fraction | None = None
            rank = 0
            for index, team in enumerate(tied):
                current = ratio(team)
                if index == 0 or current != previous:
                    rank = len(output) + 1
                output.append(StandingData(
                    rank=rank, team_id=team.id, team_name=team.name,
                    is_archived=team.is_archived, wins=wins, losses=records[team.id]["losses"],
                ))
                previous = current
        return output
