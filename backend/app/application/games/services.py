from datetime import datetime, timezone

from app.application.common.utils.base_classes import BaseService
from app.application.games.policies import GamePolicy, ScheduleConflictError as ScheduleConflictError
from app.application.games.types import DivisionSnapshot, GameData, GameSnapshot, StandingData
from app.application.statistics.policies import StatisticsPolicy
from app.infrastructure.database.game_repository import GameRepository
from app.infrastructure.database.statistics_repository import StatisticsRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class GameService(BaseService):
    def __init__(
        self,
        repository: GameRepository | None = None,
        policy: GamePolicy | None = None,
        unit_of_work: SqlAlchemyUnitOfWork | None = None,
        statistics_repository: StatisticsRepository | None = None,
        statistics_policy: StatisticsPolicy | None = None,
    ) -> None:
        self.repository = repository or GameRepository()
        self.policy = policy or GamePolicy()
        self.unit_of_work = unit_of_work or SqlAlchemyUnitOfWork()
        self.statistics_repository = statistics_repository or StatisticsRepository()
        self.statistics_policy = statistics_policy or StatisticsPolicy()

    def list_for_division(self, assignment_id: int) -> list[GameData]:
        self.policy.validate_division_exists(self.repository.get_division_assignment(assignment_id))
        return self.repository.list_for_division(assignment_id)

    def standings(self, assignment_id: int) -> list[StandingData]:
        self.policy.validate_division_exists(self.repository.get_division_assignment(assignment_id))
        return self.policy.calculate_standings(
            self.repository.standings_teams(assignment_id),
            self.repository.finalized_games(assignment_id),
        )

    def result_game_for_update(self, game_id: int) -> tuple[GameSnapshot, DivisionSnapshot]:
        game = self.repository.get_game_for_update(game_id)
        if game is None:
            raise LookupError("Game not found.")
        assignment = self.policy.validate_division_exists(
            self.repository.get_division_assignment(game.season_sport_division_id)
        )
        season = self.repository.get_season_for_update(assignment)
        self.policy.validate_result_window(season, game, datetime.now())
        return game, assignment

    def save_result(self, game_id: int, home_score: int, away_score: int) -> GameData:
        self.policy.validate_result_scores(home_score, away_score)
        with self.unit_of_work:
            self.repository.lock_schedule()
            game, _ = self.result_game_for_update(game_id)
            self.policy.validate_result_editable(game)
            result = self.repository.save_result(game_id, home_score, away_score)
        return result

    def finalize_result(self, game_id: int, actor_id: int) -> GameData:
        with self.unit_of_work:
            self.repository.lock_schedule()
            game, assignment = self.result_game_for_update(game_id)
            self.policy.validate_finalization(game)
            statistics = self.statistics_repository.game_statistics(game, assignment.season_sport_id)
            self.statistics_policy.validate_finalization(game, statistics)
            result = self.repository.finalize_result(game_id, actor_id, datetime.now(timezone.utc).replace(tzinfo=None))
        return result

    def reopen_result(self, game_id: int, actor_id: int, reason: str) -> GameData:
        with self.unit_of_work:
            self.repository.lock_schedule()
            game, _ = self.result_game_for_update(game_id)
            reason = self.policy.validate_reopening(game, reason)
            result = self.repository.reopen_result(game_id, actor_id, reason, datetime.now(timezone.utc).replace(tzinfo=None))
        return result

    def schedule_game(
        self,
        assignment_id: int,
        *,
        home_team_id: int,
        away_team_id: int,
        venue: str,
        starts_at: datetime,
        ends_at: datetime,
    ) -> GameData:
        venue, venue_key = self.policy.validate_schedule(venue, starts_at, ends_at)
        self.policy.validate_distinct_teams(home_team_id, away_team_id)

        with self.unit_of_work:
            self.repository.lock_schedule()
            assignment = self.policy.validate_division_exists(
                self.repository.get_division_assignment(assignment_id)
            )
            season = self.repository.get_season_for_update(assignment)
            self.policy.validate_ongoing_season(season)

            for team_id in (home_team_id, away_team_id):
                team = self.repository.get_team_for_update(team_id)
                if team is None:
                    raise LookupError("Team not found.")
                self.policy.validate_team(team, assignment_id)

            has_overlap = self.repository.has_overlap(
                home_team_id, away_team_id, venue_key, starts_at, ends_at,
            )
            self.policy.check_overlapping_schedule(has_overlap)

            game_data = self.repository.add_game(
                season_sport_division_id=assignment_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                venue=venue,
                venue_key=venue_key,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        return game_data

    def reschedule_game(
        self, game_id: int, *, venue: str, starts_at: datetime, ends_at: datetime,
    ) -> GameData:
        venue, venue_key = self.policy.validate_schedule(venue, starts_at, ends_at)

        with self.unit_of_work:
            self.repository.lock_schedule()
            game = self.repository.get_game_for_update(game_id)
            if game is None:
                raise LookupError("Game not found.")
            assignment = self.policy.validate_division_exists(
                self.repository.get_division_assignment(game.season_sport_division_id)
            )
            season = self.repository.get_season_for_update(assignment)
            self.policy.validate_ongoing_season(season)

            self.policy.validate_reschedule(game.starts_at, starts_at, datetime.now())
            has_overlap = self.repository.has_overlap(
                game.home_team_id, game.away_team_id, venue_key, starts_at, ends_at,
                exclude_game_id=game.id,
            )
            self.policy.check_overlapping_schedule(has_overlap)
            updated_game = self.repository.update_schedule(
                game.id, venue, venue_key, starts_at, ends_at,
            )
            if updated_game is None:
                raise LookupError("Game not found.")
        return updated_game
