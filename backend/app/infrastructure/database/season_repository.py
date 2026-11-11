from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.seasons import Season
from app.extensions import db


class SeasonRepository(BaseRepository):
    def list_all(self) -> list[Season]:
        return Season.query.order_by(Season.year.desc(), Season.id.desc()).all()

    def get_by_id(self, season_id: int) -> Season | None:
        return db.session.get(Season, season_id)

    def exists_by_name(self, name: str) -> bool:
        return Season.query.filter_by(name=name).first() is not None

    def has_active_season(self, *, exclude_id: int | None = None) -> bool:
        query = Season.query.filter(
            Season.season_status.in_(("REGISTRATION", "ONGOING"))
        )
        if exclude_id is not None:
            query = query.filter(Season.id != exclude_id)
        return query.first() is not None

    def add(self, season: Season) -> None:
        db.session.add(season)