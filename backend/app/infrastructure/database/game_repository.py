from datetime import datetime

from sqlalchemy import or_, update

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.games import Game, ScheduleLock
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.seasons import Season
from app.extensions import db


class GameRepository(BaseRepository):
    def get_division_assignment(self, assignment_id: int) -> SeasonSportDivision | None:
        return db.session.get(SeasonSportDivision, assignment_id)

    def get_season_for_update(self, assignment: SeasonSportDivision) -> Season | None:
        season_sport = db.session.get(SeasonSport, assignment.season_sport_id)
        if season_sport is None:
            return None
        return Season.query.filter_by(id=season_sport.season_id).with_for_update().first()

    def list_for_division(self, assignment_id: int) -> list[Game]:
        return Game.query.filter_by(season_sport_division_id=assignment_id).order_by(
            Game.starts_at, Game.id
        ).all()

    def lock_schedule(self) -> None:
        # Serialize writes across all seasons before checking for overlaps.
        locked = db.session.execute(
            update(ScheduleLock).where(ScheduleLock.id == 1).values(id=1)
        )
        if locked.rowcount != 1:
            raise RuntimeError("Schedule lock is missing; apply the latest database migration.")

    def get_team_for_update(self, team_id: int) -> SeasonTeam | None:
        return SeasonTeam.query.filter_by(id=team_id).with_for_update().first()

    def get_game_for_update(self, game_id: int) -> Game | None:
        return Game.query.filter_by(id=game_id).with_for_update().first()

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

    def add(self, game: Game) -> None:
        db.session.add(game)
