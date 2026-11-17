from datetime import datetime

from sqlalchemy import or_, update

from app.application.common.utils.base_classes import BaseRepository
from app.application.games.types import (
    DivisionSnapshot,
    GameData,
    GameSnapshot,
    SeasonSnapshot,
    StandingTeam,
    TeamSnapshot,
)
from app.domain.models.games import Game, GameResultReopening, ScheduleLock
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.seasons import Season
from app.extensions import db


class GameRepository(BaseRepository):
    def get_division_assignment(self, assignment_id: int) -> DivisionSnapshot | None:
        assignment = db.session.get(SeasonSportDivision, assignment_id)
        if assignment is None:
            return None
        return DivisionSnapshot(season_sport_id=assignment.season_sport_id)

    def get_season_for_update(self, assignment: DivisionSnapshot) -> SeasonSnapshot | None:
        season_sport = db.session.get(SeasonSport, assignment.season_sport_id)
        if season_sport is None:
            return None
        season = Season.query.filter_by(id=season_sport.season_id).with_for_update().first()
        if season is None:
            return None
        return SeasonSnapshot(season_status=season.season_status)

    def list_for_division(self, assignment_id: int) -> list[GameData]:
        games = Game.query.filter_by(season_sport_division_id=assignment_id).order_by(
            Game.starts_at, Game.id,
        ).all()
        return [self._game_data(game) for game in games]

    def lock_schedule(self) -> None:
        # Serialize writes across all seasons before checking for overlaps.
        locked = db.session.execute(
            update(ScheduleLock).where(ScheduleLock.id == 1).values(id=1)
        )
        if locked.rowcount != 1:
            raise RuntimeError("Schedule lock is missing; apply the latest database migration.")

    def get_team_for_update(self, team_id: int) -> TeamSnapshot | None:
        team = SeasonTeam.query.filter_by(id=team_id).with_for_update().first()
        if team is None:
            return None
        return TeamSnapshot(
            season_sport_division_id=team.season_sport_division_id,
            is_archived=team.is_archived,
        )

    def get_game(self, game_id: int, *, for_update: bool = False) -> GameSnapshot | None:
        query = Game.query.filter_by(id=game_id)
        game = (query.with_for_update() if for_update else query).first()
        if game is None:
            return None
        return GameSnapshot(
            id=game.id,
            season_sport_division_id=game.season_sport_division_id,
            home_team_id=game.home_team_id,
            away_team_id=game.away_team_id,
            starts_at=game.starts_at,
            ends_at=game.ends_at,
            result_status=game.result_status,
            home_score=game.home_score,
            away_score=game.away_score,
            finalized_at=game.finalized_at,
            finalized_by=game.finalized_by,
        )

    def get_game_for_update(self, game_id: int) -> GameSnapshot | None:
        return self.get_game(game_id, for_update=True)

    def standings_teams(self, assignment_id: int) -> list[StandingTeam]:
        teams = SeasonTeam.query.filter_by(season_sport_division_id=assignment_id).order_by(SeasonTeam.id).all()
        return [StandingTeam(team.id, team.name, team.is_archived) for team in teams]

    def finalized_games(self, assignment_id: int) -> list[GameData]:
        games = Game.query.filter_by(
            season_sport_division_id=assignment_id, result_status="FINALIZED",
        ).all()
        return [self._game_data(game) for game in games]

    def save_result(self, game_id: int, home_score: int, away_score: int) -> GameData:
        game = db.session.get(Game, game_id)
        if game is None:
            raise LookupError("Game not found.")
        game.home_score, game.away_score = home_score, away_score
        game.result_status = "FOR_ENCODING"
        db.session.flush()
        return self._game_data(game)

    def finalize_result(self, game_id: int, actor_id: int, now: datetime) -> GameData:
        game = db.session.get(Game, game_id)
        if game is None:
            raise LookupError("Game not found.")
        game.result_status = "FINALIZED"
        game.finalized_by = actor_id
        game.finalized_at = now
        db.session.flush()
        return self._game_data(game)

    def reopen_result(self, game_id: int, actor_id: int, reason: str, now: datetime) -> GameData:
        game = db.session.get(Game, game_id)
        if game is None:
            raise LookupError("Game not found.")
        db.session.add(GameResultReopening(
            game_id=game.id, reason=reason, reopened_by=actor_id, reopened_at=now,
            home_score=game.home_score, away_score=game.away_score,
            finalized_by=game.finalized_by, finalized_at=game.finalized_at,
        ))
        game.result_status = "FOR_ENCODING"
        game.finalized_by = None
        game.finalized_at = None
        db.session.flush()
        return self._game_data(game)

    def has_overlap(
        self,
        home_team_id: int,
        away_team_id: int,
        venue_key: str,
        starts_at: datetime,
        ends_at: datetime,
        *,
        exclude_game_id: int | None = None,
    ) -> bool:
        query = Game.query.filter(
            Game.starts_at < ends_at,
            Game.ends_at > starts_at,
            or_(
                Game.venue_key == venue_key,
                Game.home_team_id.in_((home_team_id, away_team_id)),
                Game.away_team_id.in_((home_team_id, away_team_id)),
            ),
        )
        if exclude_game_id is not None:
            query = query.filter(Game.id != exclude_game_id)
        return query.with_for_update().first() is not None

    def add_game(
        self,
        season_sport_division_id: int,
        home_team_id: int,
        away_team_id: int,
        venue: str,
        venue_key: str,
        starts_at: datetime,
        ends_at: datetime,
    ) -> GameData:
        game = Game(
            season_sport_division_id=season_sport_division_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            venue=venue,
            venue_key=venue_key,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        db.session.add(game)
        db.session.flush()
        return self._game_data(game)

    def update_schedule(
        self,
        game_id: int,
        venue: str,
        venue_key: str,
        starts_at: datetime,
        ends_at: datetime,
    ) -> GameData | None:
        game = db.session.get(Game, game_id)
        if game is None:
            return None
        game.venue = venue
        game.venue_key = venue_key
        game.starts_at = starts_at
        game.ends_at = ends_at
        db.session.flush()
        return self._game_data(game)

    @staticmethod
    def _game_data(game: Game) -> GameData:
        return {
            "id": game.id,
            "season_sport_division_id": game.season_sport_division_id,
            "home_team_id": game.home_team_id,
            "away_team_id": game.away_team_id,
            "venue": game.venue,
            "starts_at": game.starts_at.isoformat(),
            "ends_at": game.ends_at.isoformat(),
            "result_status": game.result_status,
            "home_score": game.home_score,
            "away_score": game.away_score,
            "finalized_at": game.finalized_at.isoformat() if game.finalized_at else None,
            "finalized_by": game.finalized_by,
        }
