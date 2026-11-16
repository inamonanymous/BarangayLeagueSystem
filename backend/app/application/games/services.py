from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.application.common.utils.base_classes import BaseService
from app.application.games.policies import GamePolicy, ScheduleConflictError as ScheduleConflictError
from app.domain.models.games import Game
from app.extensions import db
from app.infrastructure.database.game_repository import GameRepository


class GameService(BaseService):
    def __init__(
        self,
        repository: GameRepository | None = None,
        policy: GamePolicy | None = None,
    ) -> None:
        self.repository = repository or GameRepository()
        self.policy = policy or GamePolicy()

    def list_for_division(self, assignment_id: int) -> list[Game]:
        if self.repository.get_division_assignment(assignment_id) is None:
            raise LookupError("Season division assignment not found.")
        return self.repository.list_for_division(assignment_id)

    def schedule_game(
        self,
        assignment_id: int,
        *,
        home_team_id: int,
        away_team_id: int,
        venue: str,
        starts_at: datetime,
        ends_at: datetime,
    ) -> Game:
        venue, venue_key = self.policy.validate_schedule(venue, starts_at, ends_at)
        self.policy.validate_distinct_teams(home_team_id, away_team_id)

        try:
            self.repository.lock_schedule()
            self._validate_ongoing_season(assignment_id)

            for team_id in (home_team_id, away_team_id):
                team = self.repository.get_team_for_update(team_id)
                if team is None:
                    raise LookupError("Team not found.")
                self.policy.validate_team(team, assignment_id)

            self._check_overlap(home_team_id, away_team_id, venue_key, starts_at, ends_at)

            game = Game(
                season_sport_division_id=assignment_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                venue=venue,
                venue_key=venue_key,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            self.repository.add(game)
            db.session.commit()
            return game
        except (ValueError, LookupError, RuntimeError, SQLAlchemyError):
            db.session.rollback()
            raise

    def reschedule_game(
        self, game_id: int, *, venue: str, starts_at: datetime, ends_at: datetime,
    ) -> Game:
        venue, venue_key = self.policy.validate_schedule(venue, starts_at, ends_at)

        try:
            self.repository.lock_schedule()
            game = self.repository.get_game_for_update(game_id)
            if game is None:
                raise LookupError("Game not found.")
            self._validate_ongoing_season(game.season_sport_division_id)

            self.policy.validate_reschedule(game.starts_at, starts_at, datetime.now())
            self._check_overlap(
                game.home_team_id, game.away_team_id, venue_key, starts_at, ends_at,
                exclude_game_id=game.id,
            )
            game.venue = venue
            game.venue_key = venue_key
            game.starts_at = starts_at
            game.ends_at = ends_at
            db.session.commit()
            return game
        except (ValueError, LookupError, RuntimeError, SQLAlchemyError):
            db.session.rollback()
            raise

    def _validate_ongoing_season(self, assignment_id: int) -> None:
        assignment = self.repository.get_division_assignment(assignment_id)
        if assignment is None:
            raise LookupError("Season division assignment not found.")
        season = self.repository.get_season_for_update(assignment)
        if season is None:
            raise LookupError("Season not found for division assignment.")
        self.policy.validate_ongoing_season(season)

    def _check_overlap(
        self,
        home_team_id: int,
        away_team_id: int,
        venue_key: str,
        starts_at: datetime,
        ends_at: datetime,
        *,
        exclude_game_id: int | None = None,
    ) -> None:
        has_overlap = self.repository.has_overlap(
            home_team_id, away_team_id, venue_key, starts_at, ends_at,
            exclude_game_id=exclude_game_id,
        )
        self.policy.validate_no_overlap(has_overlap)
