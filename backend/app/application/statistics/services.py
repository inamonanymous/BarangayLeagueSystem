from sqlalchemy.exc import IntegrityError

from app.application.games.services import GameService
from app.application.statistics.policies import StatisticsPolicy
from app.application.statistics.types import (
    GameStatistics, StatisticConfiguration, StatisticDefinitionInput, TeamStatisticsInput,
)
from app.infrastructure.database.game_repository import GameRepository
from app.infrastructure.database.statistics_repository import StatisticsRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class StatisticsService:
    def __init__(
        self, repository: StatisticsRepository | None = None, games: GameRepository | None = None,
        policy: StatisticsPolicy | None = None, unit_of_work: SqlAlchemyUnitOfWork | None = None,
    ) -> None:
        self.repository = repository or StatisticsRepository()
        self.games = games or GameRepository()
        self.policy = policy or StatisticsPolicy()
        self.unit_of_work = unit_of_work or SqlAlchemyUnitOfWork()

    def configuration(self, sport_id: int) -> StatisticConfiguration:
        if not self.repository.sport_exists(sport_id):
            raise LookupError("Season sport not found.")
        return self.repository.configuration(sport_id)

    def update_configuration(
        self, sport_id: int, definitions: list[StatisticDefinitionInput], allow_team_points: bool,
    ) -> StatisticConfiguration:
        definitions = self.policy.validate_configuration(definitions, allow_team_points)
        try:
            with self.unit_of_work:
                self.games.lock_schedule()
                current = self.configuration(sport_id)
                if current["locked"]:
                    raise ValueError("Statistic definitions cannot change after game statistics are recorded.")
                result = self.repository.replace_configuration(sport_id, definitions, allow_team_points)
        except IntegrityError as exc:
            raise ValueError("Statistic names and abbreviations must be unique within the sport.") from exc
        return result

    def game_statistics(self, game_id: int) -> GameStatistics:
        game = self.games.get_game(game_id)
        if game is None:
            raise LookupError("Game not found.")
        division = self.games.get_division_assignment(game.season_sport_division_id)
        if division is None:
            raise LookupError("Season division assignment not found.")
        return self.repository.game_statistics(game, division.season_sport_id)

    def save_game_statistics(self, game_id: int, teams: list[TeamStatisticsInput]) -> GameStatistics:
        with self.unit_of_work:
            self.games.lock_schedule()
            game_service = GameService(repository=self.games, unit_of_work=self.unit_of_work)
            game, division = game_service.result_game_for_update(game_id)
            game_service.policy.validate_result_editable(game)
            current = self.repository.game_statistics(game, division.season_sport_id)
            self.policy.validate_draft(current, teams)
            self.repository.replace_game_statistics(game_id, division.season_sport_id, teams)
            result = self.repository.game_statistics(game, division.season_sport_id)
        return result

